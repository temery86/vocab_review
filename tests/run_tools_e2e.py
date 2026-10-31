"""End to end test of the tools on fictional data (phase 3, section 12.6 step 2). Writes reports/tools-e2e-report.md.

A throwaway Postgres container gets the Supabase shim and the migrations. Two fictional vocabulary repositories are
written to a temporary folder, with quality items, gold and, for the register one, curation queues. Then the tools run
in order, reviewers, items (and a file with an invalid line, which must be refused), batches of every kind, answers
given as the reviewers would give them through RLS (changed answers included), the export with its round trip check,
and the analysis. Last, the register vocabulary's apply step reads the export, on a copy of nothing but its columns.

Usage: .venv/bin/python tests/run_tools_e2e.py
"""
import csv
import json
import random
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parents[1]
NAME, PORT = "review-site-e2e", 55433
URL = f"postgresql://postgres:test@localhost:{PORT}/postgres"
PY = sys.executable
log = []


def step(name, ok, detail=""):
    log.append((name, ok, detail))
    print("PASS" if ok else "FAIL", name, detail[:200])


def tool(*a, expect=0):
    r = subprocess.run([PY, *a, "--db-url", URL], capture_output=True, text=True, cwd=ROOT)
    return r.returncode == expect, (r.stdout + r.stderr).strip()


def fake_item(v, n, queue=None, gold=False):
    rnd = random.Random(n)
    if v == "scv":
        s = {"programme": rnd.choice(["aa", "bb", "cc"]), "construct_type": rnd.choice(["attitude", "status"]),
             "method": rnd.choice(["poc_full", "poc_lowcost_v2", "not_graded"]), "grade": rnd.choice(["identical", "related", "not_graded"]),
             "battery_construct": rnd.random() < 0.2}
        graded = s["grade"] != "not_graded"
        return {"item_id": f"scv:x:m/aa/{n:06d}:x:c/{n % 7:05d}:scv-test-0.0.1", "vocabulary": "scv", "export_version": "scv-test-0.0.1",
                "construct_pid": f"x:c/{n % 7:05d}", "construct_label": f"Fictional construct {n % 7}", "construct_definition": "A fictional definition.",
                "measure_pid": f"x:m/aa/{n:06d}", "programme": s["programme"], "waves": "w1", "question_text": f"Fictional question {n}?",
                "response_categories": [{"code": "1", "label": "Yes"}, {"code": "2", "label": "No"}], "grade": s["grade"] if graded else None,
                "anchor_measure_pid": "x:m/aa/000000" if graded else None, "anchor_question_text": "Fictional anchor?" if graded else None,
                "method": s["method"], "neighbour_constructs": [{"pid": f"x:c/{k:05d}", "label": f"Fictional construct {k}"} for k in range(5)],
                "stratum": s, "context": {}, "is_gold": gold, "gold_belongs": "yes" if gold else None, "gold_grade": s["grade"] if gold and graded else None}
    s = {"country": rnd.choice(["xa", "xb"]), "body": "test", "placement": rnd.choice(["R-29 join", "adjudicator shown"]),
         "statement_basis": rnd.choice(["definition", "label_only"]), "provisional": rnd.random() < 0.5, "definition_provenance": "draft_generated",
         "poc_member": False}
    x = {"item_id": f"rvv:x:r/xa/test/{n:06d}:x:c/{n % 5:05d}:rvv-test-0.0.1" + (f":{queue}" if queue else ""), "vocabulary": "rvv",
         "export_version": "rvv-test-0.0.1", "queue": queue, "construct_pid": f"x:c/{n % 5:05d}", "construct_label": f"Fictional register construct {n % 5}",
         "construct_definition": "A fictional definition.", "measure_pid": f"x:r/xa/test/{n:06d}", "programme": "xa/test", "waves": "2001 to 2010",
         "question_text": "Fiktive Definition", "method": "not_graded",
         "neighbour_constructs": [{"pid": f"x:c/{k:05d}", "label": f"Fictional register construct {k}"} for k in range(5)], "stratum": s,
         "context": {"variable_name": f"V{n}", "label": "Fiktiv"}, "is_gold": gold, "gold_belongs": "yes" if gold else None}
    if queue:
        x["reject_reasons"] = ["technical", "other"]
    return x


def write_repo(base, v):
    repo = base / v
    (repo / "audit").mkdir(parents=True)
    (repo / "audit" / "log.jsonl").touch()
    exp = f"{v}-test-0.0.1"
    items = [fake_item(v, n) for n in range(1, 81)]
    golds = [fake_item(v, n, gold=True) for n in range(1, 7)]
    for d, rows in (("items", items), ("gold", golds)):
        (repo / "review" / d).mkdir(parents=True)
        (repo / "review" / d / f"{exp}.jsonl").write_text("\n".join(json.dumps(x) for x in rows) + "\n")
    if v == "rvv":
        q = repo / "review" / "queues" / exp
        q.mkdir(parents=True)
        (q / "placement.jsonl").write_text("\n".join(json.dumps(fake_item(v, n, "placement")) for n in range(100, 112)) + "\n")
        mem = [{"item_id": f"rvv:membership/M{n:03d}:x:c/{n % 5:05d}:{exp}", "vocabulary": "rvv", "export_version": exp, "queue": "membership",
                "construct_pids": [f"x:c/{n % 5:05d}"], "construct_label": "Fictional", "construct_definition": "A fictional definition.",
                "note": "Fictional note", "members": [{"pid": f"x:r/xa/test/{k:06d}", "label": "Fiktiv"} for k in range(3)],
                "named_members": ["x:r/xa/test/000001"], "answers_per_member": ["stay", "move", "reject"], "reject_reasons": ["technical"]}
               for n in range(1, 4)]
        (q / "membership.jsonl").write_text("\n".join(json.dumps(x) for x in mem) + "\n")
    return repo


def answer(con, email, rnd):
    """Answers through RLS, as the front end gives them."""
    with con.cursor() as cur:
        cur.execute("BEGIN")
        cur.execute("SET LOCAL ROLE authenticated")
        cur.execute("SELECT set_config('request.jwt.claims', %s, true)", [json.dumps({"email": email})])
        cur.execute("SELECT assignment_id, queue, grade, neighbour_constructs, curation FROM review.item_reviewer")
        rows = cur.fetchall()
        n = 0
        for aid, queue, grade, nb, curation in rows:
            if queue == "membership":
                ma = {m["pid"]: {"answer": rnd.choice(["stay", "move", "reject"]), "target": nb[0]["pid"] if nb else None, "reason": "technical"}
                      for m in curation["members"]}
                cur.execute("INSERT INTO review.response (assignment_id, member_answers, seconds_on_item) VALUES (%s, %s, %s)",
                            [aid, json.dumps(ma), rnd.randint(5, 90)])
            elif queue == "placement":
                b = rnd.choice(["yes", "neighbour", "reject", "unsure", "no"])
                cur.execute("""INSERT INTO review.response (assignment_id, belongs, better_construct_pid, better_construct_text, reject_reason)
                    VALUES (%s, %s, %s, %s, %s)""", [aid, b, nb[1]["pid"] if b == "neighbour" else None, "A fictional missing construct" if b == "no" else None,
                                                     "technical" if b == "reject" else None])
            else:
                b = rnd.choice(["yes", "yes", "yes", "no", "unsure"])
                cur.execute("""INSERT INTO review.response (assignment_id, belongs, better_construct_pid, grade_ok, correct_grade, seconds_on_item)
                    VALUES (%s, %s, %s, %s, %s, %s)""", [aid, b, nb[0]["pid"] if b == "no" else None, rnd.choice(["yes", "no"]) if grade else "not_shown",
                                                         "related" if grade else None, rnd.randint(5, 90)])
                if rnd.random() < 0.2:      # a changed answer is a new row
                    cur.execute("INSERT INTO review.response (assignment_id, belongs) VALUES (%s, 'yes')", [aid])
            n += 1
        cur.execute("SELECT DISTINCT batch_id FROM review.item_reviewer")
        for (bid,) in cur.fetchall():
            cur.execute("INSERT INTO review.batch_comment (batch_id, reviewer_email, missing_constructs) VALUES (%s, %s, %s)",
                        [bid, email, "Fictional missing construct about commuting"])
        cur.execute("COMMIT")
    return n


subprocess.run(["docker", "rm", "-f", NAME], capture_output=True)
subprocess.run(["docker", "run", "-d", "--name", NAME, "-p", f"{PORT}:5432", "-e", "POSTGRES_PASSWORD=test", "postgres:16-alpine"], check=True,
               capture_output=True)
try:
    for _ in range(60):
        try:
            psycopg.connect(URL).close()
            break
        except Exception:
            time.sleep(1)
    time.sleep(2)
    with psycopg.connect(URL, autocommit=True) as con:
        for f in [ROOT / "tests" / "supabase_shim.sql", *sorted((ROOT / "supabase" / "migrations").glob("*.sql"))]:
            con.execute(f.read_text())
    tmp = Path(tempfile.mkdtemp(prefix="review-e2e-"))
    scv, rvv = write_repo(tmp, "scv"), write_repo(tmp, "rvv")
    with open(tmp / "reviewers.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["email", "name", "affiliation", "expertise", "programmes", "role", "consent_acknowledgement"])
        w.writerows([["owner@example.org", "Test Owner", "", "", "", "owner", "yes"], ["r1@example.org", "Reviewer One", "", "labour", "aa", "reviewer", "no"],
                     ["r2@example.org", "Reviewer Two", "", "health", "bb", "reviewer", "no"]])
    step("reviewers added", *tool("tools/make_reviewers.py", str(tmp / "reviewers.csv"), "--no-auth"))
    step("survey items loaded", *tool("tools/load_items.py", str(scv), "--export", "scv-test-0.0.1"))
    step("register items and queues loaded", *tool("tools/load_items.py", str(rvv), "--export", "rvv-test-0.0.1"))
    bad = write_repo(tmp / "bad", "scv")
    with open(bad / "review" / "items" / "scv-test-0.0.1.jsonl", "a") as fh:
        fh.write(json.dumps({"item_id": "x", "vocabulary": "zzz"}) + "\n")
    ok, out = tool("tools/load_items.py", str(bad), "--export", "scv-test-0.0.1", expect=1)
    step("a file with an invalid line is refused", ok and "REFUSED" in out, out[-150:])
    step("owner quality batch of 25", *tool("tools/make_batch.py", str(scv), "--export", "scv-test-0.0.1", "--reviewer", "owner@example.org",
                                              "--size", "25", "--seed", "1", "--open"))
    step("invited batch of 25 with 15 percent overlap", *tool("tools/make_batch.py", str(scv), "--export", "scv-test-0.0.1", "--reviewer",
                                                              "r1@example.org", "--size", "25", "--overlap-with", "r2@example.org", "--seed", "2", "--open"))
    step("invited batch outside 20 to 30 is refused", *tool("tools/make_batch.py", str(scv), "--export", "scv-test-0.0.1", "--reviewer",
                                                            "r2@example.org", "--size", "40", expect=1))
    step("owner curation batch, placement queue", *tool("tools/make_batch.py", str(rvv), "--export", "rvv-test-0.0.1", "--reviewer",
                                                        "owner@example.org", "--queue", "placement", "--size", "10", "--open"))
    step("owner register quality batch", *tool("tools/make_batch.py", str(rvv), "--export", "rvv-test-0.0.1", "--reviewer", "owner@example.org",
                                               "--size", "25", "--seed", "3", "--open"))
    with psycopg.connect(URL) as con:
        with con.cursor() as cur:
            cur.execute("BEGIN")
            cur.execute("SET LOCAL ROLE authenticated")
            cur.execute("SELECT set_config('request.jwt.claims', %s, true)", [json.dumps({"email": "owner@example.org"})])
            cur.execute("SELECT review.owner_next_batch('scv-test-0.0.1', 25, 0.3)")
            b1 = cur.fetchone()[0]
            cur.execute("SELECT review.owner_next_queue_batch('rvv-test-0.0.1', 'membership', 3)")
            b2 = cur.fetchone()[0]
            cur.execute("SELECT count(*), count(DISTINCT item_id), count(*) FILTER (WHERE i.is_gold) FROM review.assignment s JOIN review.item i USING (item_id) WHERE batch_id = %s", [b1])
            n, nd, ng = cur.fetchone()
            cur.execute("""SELECT count(*) FROM review.assignment a JOIN review.assignment b USING (item_id)
                WHERE a.batch_id = %s AND b.batch_id <> a.batch_id AND b.reviewer_email = a.reviewer_email""", [b1])
            again = cur.fetchone()[0]
            cur.execute("COMMIT")
    step("owner batch built on request from the admin screen", n == 25 and nd == 25 and ng == 3 and again == 0,
         f"{b1}, {n} items, {ng} gold, {again} repeated from earlier batches. Curation batch {b2}")
    rnd = random.Random(7)
    with psycopg.connect(URL) as con:
        given = {e: answer(con, e, rnd) for e in ("owner@example.org", "r1@example.org", "r2@example.org")}
    step("answers given through RLS", all(given.values()), json.dumps(given))
    ok, out = tool("tools/export_reviews.py", str(scv), "--stamp", "e2e")
    step("survey export with round trip check", ok, out)
    ok, out = tool("tools/export_reviews.py", str(rvv), "--stamp", "e2e")
    step("register export with round trip check", ok, out)
    with psycopg.connect(URL) as con:
        n_resp = con.execute("SELECT count(*) FROM review.response").fetchone()[0]
    n_exp = sum(sum(1 for _ in open(r / "review" / "exports" / "e2e" / "response.jsonl")) for r in (scv, rvv))
    step("every response row is in an export", n_resp == n_exp, f"{n_resp} in the database, {n_exp} in the exports")
    j = [json.loads(l) for l in open(scv / "review" / "exports" / "e2e" / "reviews_joined.jsonl")]
    leaked = any("@" in json.dumps(x) for x in j) or any("@" in open(scv / "review" / "exports" / "e2e" / f).read()
                                                          for f in ("response.csv", "assignment.csv", "batch_comment.csv", "reviews_joined.csv"))
    step("no email in the export files except the key", not leaked)
    step("the key is gitignored", (scv / "review" / "exports" / "e2e" / ".gitignore").read_text().strip() == "reviewers_key.csv")
    r = subprocess.run([PY, "tools/analyse_reviews.py", str(scv), "--export", str(scv / "review" / "exports" / "e2e")], capture_output=True, text=True, cwd=ROOT)
    step("survey analysis", r.returncode == 0, r.stdout.strip() or r.stderr[-300:])
    r = subprocess.run([PY, "tools/analyse_reviews.py", str(rvv), "--export", str(rvv / "review" / "exports" / "e2e")], capture_output=True, text=True, cwd=ROOT)
    step("register analysis", r.returncode == 0, r.stdout.strip() or r.stderr[-300:])
    rj = [json.loads(l) for l in open(rvv / "review" / "exports" / "e2e" / "reviews_joined.jsonl")]
    cur_q = [x for x in rj if x.get("queue")]
    need = {"item_id", "reviewer", "submitted_at", "belongs", "better_construct_pid", "better_construct_text", "reject_reason", "member_answers"}
    step("the joined export has every column apply_curation.py reads", need <= set(rj[0]), f"{len(cur_q)} curation answers")
    audits = sum(1 for _ in open(scv / "audit" / "log.jsonl")), sum(1 for _ in open(rvv / "audit" / "log.jsonl"))
    step("every tool run is an audit event in the vocabulary repository", audits[0] >= 5 and audits[1] >= 5, f"survey {audits[0]}, register {audits[1]}")
finally:
    subprocess.run(["docker", "rm", "-f", NAME], capture_output=True)

L = ["# Tools end to end test report", "", f"Run {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC by `tests/run_tools_e2e.py` on fictional data in a "
     "throwaway Postgres 16 container with the Supabase roles emulated. Fictional vocabulary repositories in a temporary folder.", "",
     f"{len(log)} steps, {sum(ok for _, ok, _ in log)} passed.", "", "| Step | Result | Detail |", "|---|---|---|"]
L += [f"| {n} | {'pass' if ok else 'FAIL'} | {d.replace('|', '/').replace(chr(10), ' ')[:160]} |" for n, ok, d in log]
(ROOT / "reports" / "tools-e2e-report.md").write_text("\n".join(L) + "\n")
sys.exit(0 if all(ok for _, ok, _ in log) else 1)
