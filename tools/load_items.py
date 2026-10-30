"""Load a vocabulary's item, gold and queue files into review.item (sections 12.3 and 12.7, V-08).

Reads <repo>/review/items/<export>.jsonl, <repo>/review/gold/<export>.jsonl and <repo>/review/queues/<export>/*.jsonl.
Every line of every file is validated against schema/item.schema.json first, and a file with any invalid line is
refused before anything is written. Items are upserted by item_id. Gold lines mark their item as gold. Queue lines
are loaded as items of their queue, with the fields that are not item columns kept in item.curation.

Usage: .venv/bin/python tools/load_items.py ../scv --export scv-review-0.3.0
"""
import argparse
import json
import sys
from pathlib import Path

import jsonschema

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import ROOT, audit, connect  # noqa: E402

COLS = ["item_id", "vocabulary", "export_version", "queue", "construct_pid", "construct_label", "construct_definition",
        "construct_exclusions", "construct_definition_provenance", "measure_pid", "programme", "waves", "question_text",
        "question_text_en", "text_kind", "response_categories", "universe_text", "anchor_measure_pid", "anchor_question_text",
        "anchor_response_categories", "grade", "grade_reasons", "method", "model_confidence", "neighbour_constructs", "stratum",
        "context", "curation", "is_gold", "gold_belongs", "gold_grade", "gold_source"]
JSONB = {"response_categories", "anchor_response_categories", "grade_reasons", "neighbour_constructs", "stratum", "context", "curation"}
CURATION = ["construct_pids", "members", "named_members", "named_not_members", "note", "source", "reject_reasons",
            "answers_per_member", "centroid_cosine"]


def read(path, validator):
    rows, bad = [], []
    for n, line in enumerate(open(path, encoding="utf-8"), 1):
        if not line.strip():
            continue
        try:
            x = json.loads(line)
        except json.JSONDecodeError as e:
            bad.append(f"{path.name}:{n} invalid JSON {e}")
            continue
        errs = sorted(validator.iter_errors(x), key=lambda e: e.path)
        if errs:
            bad.append(f"{path.name}:{n} {errs[0].message[:200]}")
        rows.append(x)
    return rows, bad


def to_row(x):
    x = dict(x)
    if x.get("queue") == "membership":
        x.setdefault("construct_pid", (x.get("construct_pids") or [""])[0] or "none")
        x.setdefault("measure_pid", x["item_id"].split(":", 2)[1])
        x.setdefault("programme", "membership")
        x.setdefault("stratum", {"queue": "membership"})
    cur = {k: x.pop(k) for k in CURATION if k in x}
    if x.get("queue"):
        x["curation"] = cur
    x.setdefault("construct_definition", "")
    x["construct_definition"] = x["construct_definition"] or ""
    x.setdefault("neighbour_constructs", [])
    x.setdefault("context", {})
    x["is_gold"] = bool(x.get("is_gold"))
    return [json.dumps(x.get(c)) if c in JSONB and x.get(c) is not None else x.get(c) for c in COLS]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--export", required=True)
    ap.add_argument("--db-url", help="tests only, otherwise SUPABASE_DB_URL from .env")
    a = ap.parse_args()
    repo = Path(a.repo).resolve()
    v = jsonschema.Draft202012Validator(json.loads((ROOT / "schema" / "item.schema.json").read_text()))
    files = {"items": [repo / "review" / "items" / f"{a.export}.jsonl"], "gold": [repo / "review" / "gold" / f"{a.export}.jsonl"],
             "queues": sorted((repo / "review" / "queues" / a.export).glob("*.jsonl"))}
    data, refused = {}, []
    for kind, paths in files.items():
        for p in paths:
            if not p.exists():
                if kind == "items":
                    raise SystemExit(f"{p} not found")
                continue
            rows, bad = read(p, v)
            if bad:
                refused.append((p, bad))
            data[p] = (kind, rows)
    if refused:
        for p, bad in refused:
            print(f"REFUSED {p} with {len(bad)} invalid lines, for example {bad[:3]}")
        raise SystemExit(1)
    con = connect(a.db_url)
    counts = {}
    with con.cursor() as cur:
        marks = ", ".join(["%s"] * len(COLS))
        upd = ", ".join(f"{c} = EXCLUDED.{c}" for c in COLS if c not in ("item_id", "is_gold", "gold_belongs", "gold_grade", "gold_source"))
        for p, (kind, rows) in data.items():
            if kind == "gold":
                continue
            cur.executemany(f"INSERT INTO review.item ({', '.join(COLS)}) VALUES ({marks}) ON CONFLICT (item_id) DO UPDATE SET {upd}",
                            [to_row(x) for x in rows])
            counts[p.name if kind != "queues" else f"queue {p.stem}"] = len(rows)
        for p, (kind, rows) in data.items():
            if kind == "gold":
                cur.executemany("""UPDATE review.item SET is_gold = true, gold_belongs = %s, gold_grade = %s, gold_source = %s WHERE item_id = %s""",
                                [(x.get("gold_belongs"), x.get("gold_grade"), x.get("gold_source"), x["item_id"]) for x in rows])
                counts["gold"] = len(rows)
        cur.execute("SELECT count(*) FROM review.item WHERE export_version = %s", [a.export])
        counts["items_in_db_for_export"] = cur.fetchone()[0]
    con.commit()
    con.close()
    audit(f"Items of {a.export} loaded into the review site", type="ingest", inputs=[str(p) for p in data], outputs=["review.item"],
          counts=counts, vocab_repo=repo)
    print(json.dumps(counts))


if __name__ == "__main__":
    main()
