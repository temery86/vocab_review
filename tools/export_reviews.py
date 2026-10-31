"""Export every review of one vocabulary (section 7, 12.5). Complete, repeatable and lossless.

Pulls, with the service rights, every response row (not only the latest), every batch comment, the items, assignments
and batches they refer to, and writes them to <repo>/review/exports/<yyyy-mm-dd-hhmm>/ as CSV and JSON lines, one file
per table, plus reviews_joined.csv and reviews_joined.jsonl with one row per current response and every item field
beside it, and codebook.md. Reviewer emails are replaced by their stable pseudonym everywhere. The key from
pseudonym to email is written to reviewers_key.csv beside them, with a .gitignore so it is never committed.
The export checks itself. Every response row in the database for the vocabulary must be in the export.

Usage: .venv/bin/python tools/export_reviews.py ../scv
"""
import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import audit, connect, vocab_of  # noqa: E402

CODEBOOK = {
    "item": "One row per item of the vocabulary that appears in any assignment. Fields as review.item (CLAUDE.md sections 4 and 12.3). "
            "Gold fields are included, since the export is for the owner.",
    "batch": "One row per batch of the vocabulary. sampling_spec holds the seed and specification, so the batch can be rebuilt.",
    "assignment": "One row per item given to a reviewer in a batch. reviewer is the pseudonym. is_overlap marks the second reviewer of an overlap item.",
    "response": "Every response row ever submitted, append only. The latest row per assignment by submitted_at is the current answer. "
                "belongs is yes, no, unsure, or on curation items neighbour or reject. better_construct_pid is the neighbour chosen, "
                "better_construct_text the free text when none fits, reject_reason the reason from the queue's list, member_answers the "
                "answers per member on membership items, grade_ok and correct_grade the answers to question 2, seconds_on_item the time on the item.",
    "batch_comment": "The free comments at the end of a batch. reviewer is the pseudonym.",
    "reviews_joined": "One row per current response (the latest per assignment), with the batch, the assignment, the reviewer pseudonym, "
                      "reviewer_role (owner or reviewer), flow_test (true for answers in a batch marked as a flow test, which analysis leaves out), "
                      "queue (empty for quality items) and every item field beside it.",
}


def rows_of(cur, sql, params):
    cur.execute(sql, params)
    cols = [d.name for d in cur.description]
    return cols, [dict(zip(cols, r)) for r in cur.fetchall()]


def cell(v):
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, datetime):
        return v.isoformat()
    return v


def write(d, name, cols, rows):
    with open(d / f"{name}.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows({k: cell(r.get(k)) for k in cols} for r in rows)
    with open(d / f"{name}.jsonl", "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps({k: cell(r.get(k)) for k in cols}, ensure_ascii=False, default=str) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--db-url")
    ap.add_argument("--stamp", help="tests only, the folder name")
    a = ap.parse_args()
    repo = Path(a.repo).resolve()
    vocab = vocab_of(repo)
    con = connect(a.db_url)
    cur = con.cursor()
    cur.execute("SELECT email, pseudonym, role FROM review.reviewer")
    who = {e: (p, r) for e, p, r in cur.fetchall()}
    ps = lambda e: who.get(e, ("unknown", ""))[0]
    # By item vocabulary, so a mixed topic batch sends each answer to the repository its item belongs to.
    bc, batches = rows_of(cur, """SELECT * FROM review.batch b WHERE EXISTS (SELECT 1 FROM review.assignment s JOIN review.item i ON i.item_id = s.item_id
        WHERE s.batch_id = b.batch_id AND i.vocabulary = %s) ORDER BY batch_id""", [vocab])
    ac, assigns = rows_of(cur, """SELECT s.* FROM review.assignment s JOIN review.item i ON i.item_id = s.item_id
        WHERE i.vocabulary = %s ORDER BY s.assignment_id""", [vocab])
    rc, resps = rows_of(cur, """SELECT r.* FROM review.response r JOIN review.assignment s ON s.assignment_id = r.assignment_id
        JOIN review.item i ON i.item_id = s.item_id WHERE i.vocabulary = %s ORDER BY r.response_id""", [vocab])
    cc, comments = rows_of(cur, """SELECT c.* FROM review.batch_comment c JOIN review.batch b ON b.batch_id = c.batch_id
        WHERE b.vocabulary IN (%s, 'mixed') ORDER BY c.comment_id""", [vocab])
    ic, items = rows_of(cur, """SELECT * FROM review.item WHERE vocabulary = %s AND item_id IN (SELECT item_id FROM review.assignment)
        ORDER BY item_id""", [vocab])
    cur.execute("""SELECT count(*) FROM review.response r JOIN review.assignment s ON s.assignment_id = r.assignment_id
        JOIN review.item i ON i.item_id = s.item_id WHERE i.vocabulary = %s""", [vocab])
    n_db = cur.fetchone()[0]
    con.close()
    for x in assigns:
        x["reviewer"] = ps(x.pop("reviewer_email"))
    ac = [c if c != "reviewer_email" else "reviewer" for c in ac]
    for x in comments:
        x["reviewer"] = ps(x.pop("reviewer_email"))
    cc = [c if c != "reviewer_email" else "reviewer" for c in cc]
    flow = {x["batch_id"] for x in batches if x.get("flow_test")}
    by_a = {x["assignment_id"]: x for x in assigns}
    by_i = {x["item_id"]: x for x in items}
    current = {}
    for r in sorted(resps, key=lambda r: (r["submitted_at"], r["response_id"])):
        current[r["assignment_id"]] = r
    joined, jc = [], None
    role_of = {p: r for p, r in who.values()}
    for aid, r in sorted(current.items()):
        s, i = by_a[aid], by_i[by_a[aid]["item_id"]]
        row = {"response_id": r["response_id"], "submitted_at": r["submitted_at"], "batch_id": s["batch_id"], "assignment_id": aid,
               "position": s["position"], "is_overlap": s["is_overlap"], "flow_test": s["batch_id"] in flow,
               "reviewer": s["reviewer"], "reviewer_role": role_of.get(s["reviewer"], ""),
               **{k: r[k] for k in rc if k not in ("response_id", "assignment_id", "submitted_at")}, **i}
        joined.append(row)
        jc = list(row)
    stamp = a.stamp or datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M")
    d = repo / "review" / "exports" / stamp
    d.mkdir(parents=True, exist_ok=False)
    for name, cols, rows in (("item", ic, items), ("batch", bc, batches), ("assignment", ac, assigns), ("response", rc, resps),
                             ("batch_comment", cc, comments)):
        write(d, name, cols, rows)
    write(d, "reviews_joined", jc or ["response_id"], joined)
    with open(d / "reviewers_key.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["pseudonym", "email", "role"])
        w.writerows(sorted((p, e, r) for e, (p, r) in who.items()))
    (d / ".gitignore").write_text("reviewers_key.csv\n")
    L = [f"# Codebook, review export {stamp}", "", f"Vocabulary {vocab}. Exported {datetime.now(timezone.utc).isoformat(timespec='seconds')}. "
         "Every file comes as CSV and as JSON lines with the same columns. JSON fields are written as JSON text in the CSV files. "
         "Reviewer emails are replaced by pseudonyms (r00 is the owner). The key is in reviewers_key.csv, which is never committed.", ""]
    for name, cols in (("item", ic), ("batch", bc), ("assignment", ac), ("response", rc), ("batch_comment", cc), ("reviews_joined", jc or [])):
        L += [f"## {name}", "", CODEBOOK[name], "", "Columns. " + ", ".join(f"`{c}`" for c in cols) + ".", ""]
    (d / "codebook.md").write_text("\n".join(L))
    n_file = sum(1 for _ in open(d / "response.jsonl"))
    if n_file != n_db:
        raise SystemExit(f"round trip failed, {n_db} responses in the database and {n_file} in the export")
    counts = {"items": len(items), "batches": len(batches), "assignments": len(assigns), "responses": len(resps), "current_responses": len(joined),
              "batch_comments": len(comments), "responses_in_db": n_db}
    audit(f"Reviews of {vocab} exported to review/exports/{stamp}", type="publish", inputs=["review schema"], outputs=[str(d)], counts=counts,
          vocab_repo=repo)
    print(stamp, json.dumps(counts))


if __name__ == "__main__":
    main()
