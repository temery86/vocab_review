"""Shared helpers for the tools (section 12.5). Settings from the gitignored .env, a Postgres connection with the
service rights, and audit events in the format of ../scv/CLAUDE.md section 3.1, written to this repository's log and
to the vocabulary repository's log."""
from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_env(path: Path = ROOT / ".env") -> None:
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def connect(db_url: str | None = None):
    """A connection as the database owner or the service role. The URL is never printed or logged."""
    import psycopg
    load_env()
    url = db_url or os.environ.get("SUPABASE_DB_URL")
    if not url:
        raise SystemExit("SUPABASE_DB_URL is not set (see .env.example)")
    return psycopg.connect(url, autocommit=False)


def _commit(repo: Path) -> str:
    r = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=repo)
    return r.stdout.strip() if r.returncode == 0 else ""


def _next_id(log: Path) -> str:
    last = None
    if log.exists():
        for line in log.read_text().splitlines():
            if line.strip():
                last = line
    return f"evt-{int(json.loads(last)['id'].split('-')[1]) + 1 if last else 1:06d}"


def audit(summary: str, *, type: str, phase: str = "review", inputs=(), outputs=(), counts=None, vocab_repo: Path | None = None,
          actor: str = "agent", decision_ref: str = "") -> None:
    """One event in this repository's log and, when given, the vocabulary repository's log."""
    for repo in [ROOT] + ([Path(vocab_repo).resolve()] if vocab_repo else []):
        log = repo / "audit" / "log.jsonl"
        log.parent.mkdir(parents=True, exist_ok=True)
        ev = {"id": _next_id(log), "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "actor": actor, "phase": phase,
              "type": type, "summary": summary, "inputs": [str(x) for x in inputs], "outputs": [str(x) for x in outputs],
              "counts": counts or {}, "model": {"name": "", "version": "", "prompt_id": "", "prompt_hash": ""},
              "decision_ref": decision_ref, "git_commit": _commit(repo)}
        with open(log, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(ev, ensure_ascii=False) + "\n")


def vocab_of(repo: Path) -> str:
    """scv for ../scv, rvv for ../register-corpus, from the item files present."""
    names = {p.name for p in (Path(repo) / "review" / "items").glob("*.jsonl")}
    for v in ("scv", "rvv"):
        if any(n.startswith(v + "-") for n in names):
            return v
    raise SystemExit(f"no item file in {repo}/review/items")
