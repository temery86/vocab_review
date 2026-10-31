"""Runs the RLS tests in a throwaway local Postgres 16 container and writes reports/rls-test-report.md.

Applies tests/supabase_shim.sql (the Supabase roles and auth.jwt()), every migration in supabase/migrations/, the
fictional seed and tests/rls.sql. Exits non zero if any case fails. Needs docker (colima on this machine).

Usage: .venv/bin/python tests/run_rls.py
"""
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = "review-site-rls"


def sh(*a, **k):
    return subprocess.run(list(a), capture_output=True, text=True, **k)


def psql(sql_file=None, sql=None):
    # Over TCP, not the socket. While the image initialises it runs a temporary server on the socket only, then
    # restarts, so a socket check can pass too early (seen on GitHub runners). TCP answers only once the real one is up.
    cmd = ["docker", "exec", "-i", NAME, "psql", "-h", "127.0.0.1", "-U", "postgres", "-d", "postgres", "-v", "ON_ERROR_STOP=1", "-q", "-A", "-t", "-F", "\t"]
    if sql is not None:
        return sh(*cmd, "-c", sql)
    return subprocess.run(cmd, stdin=open(sql_file), capture_output=True, text=True)


sh("docker", "rm", "-f", NAME)
r = sh("docker", "run", "-d", "--name", NAME, "-e", "POSTGRES_PASSWORD=test", "postgres:16-alpine")
if r.returncode:
    sys.exit(r.stderr)
ok = 0
for _ in range(90):
    ok = ok + 1 if psql(sql="SELECT 1").returncode == 0 else 0
    if ok >= 3:                                   # three answers in a row, so not a server about to restart
        break
    time.sleep(1)
else:
    sys.exit("Postgres did not become ready")
try:
    files = [ROOT / "tests" / "supabase_shim.sql", *sorted((ROOT / "supabase" / "migrations").glob("*.sql")), ROOT / "tests" / "seed.sql",
             ROOT / "tests" / "rls.sql"]
    for f in files:
        r = psql(f)
        if r.returncode:
            sys.exit(f"{f.name} failed\n{r.stderr}")
    rows = [l.split("\t") for l in psql(sql="SELECT name, ok, detail FROM rls_result").stdout.strip().splitlines()]
    version = psql(sql="SHOW server_version").stdout.strip()
finally:
    sh("docker", "rm", "-f", NAME)
failed = [x for x in rows if x[1] != "t"]
L = ["# Row level security test report", "",
     f"Run {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC on Postgres {version} in a local container, with the Supabase roles and "
     "auth.jwt() emulated as Supabase implements them (`tests/supabase_shim.sql`). Data is the fictional seed (`tests/seed.sql`).", "",
     f"{len(rows)} cases, {len(rows) - len(failed)} passed, {len(failed)} failed.", "", "| Case | Result | Detail |", "|---|---|---|"]
L += [f"| {n} | {'pass' if ok == 't' else 'FAIL'} | {d.replace('|', '/')[:120]} |" for n, ok, d in rows]
(ROOT / "reports").mkdir(exist_ok=True)
(ROOT / "reports" / "rls-test-report.md").write_text("\n".join(L) + "\n")
print(f"{len(rows)} cases, {len(failed)} failed")
for x in failed:
    print("FAIL", x)
sys.exit(1 if failed else 0)
