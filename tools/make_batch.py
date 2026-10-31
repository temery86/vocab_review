"""Build a batch and its assignments (sections 6, 12.4 and 12.7, V-07).

Quality batches are a stratified sample of a vocabulary's quality items. Cells are the stratum keys of the vocabulary
(below), sampled in proportion to their size with the cells where errors are known to cluster weighted up, and cells
not yet covered for the reviewer first, so owner batches can be built one after another (12.4). Items the reviewer
already has are never drawn again. Gold items are added at 3 per 25 (V-07), never one the reviewer has seen. For
invited reviewers 15 percent of the items are also assigned to a second reviewer (--overlap-with). For the owner
overlap is off. Quality items are never drawn while the same link is in an open or draft curation batch (12.7).

Curation batches take the next items of a queue in the queue's order, every item rather than a sample (12.7).

The sampling specification, with the seed, goes to batch.sampling_spec and to <repo>/review/batches/<batch_id>.json,
so the batch can be rebuilt exactly. The batch is created as draft unless --open is given.

Usage: .venv/bin/python tools/make_batch.py ../scv --export scv-review-0.3.0 --reviewer owner@example.org --size 50
       .venv/bin/python tools/make_batch.py ../register-corpus --export rvv-review-0.1.0 --reviewer owner@example.org --queue placement --size 50
"""
import argparse
import json
import math
import random
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import audit, connect  # noqa: E402

CELLS = {"scv": ["programme", "construct_type", "method", "grade"], "rvv": ["country", "placement", "statement_basis", "poc_member"]}


def oversample(v, s):
    """Cells where errors are known to cluster (section 6). Survey, from the breadth run and D-33 checks. Register, from
    the R-29 calibration and R-25."""
    if v == "scv":
        return 2.0 if (s.get("battery_construct") or s.get("attributes_method") in ("model_lite", "model_opus_period")
                       or (s.get("method", "").startswith("poc_lowcost") and s.get("grade") in ("related", "identical"))) else 1.0
    return 2.0 if (s.get("placement") in ("R-29 join", "R-29 cluster", "nearest part", "adjudicator unseen") or s.get("provisional")) else 1.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--export", required=True)
    ap.add_argument("--reviewer", required=True)
    ap.add_argument("--size", type=int, default=25)
    ap.add_argument("--queue", choices=["placement", "membership"])
    ap.add_argument("--overlap-with", help="second reviewer for 15 percent of the items (invited rounds)")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--open", action="store_true")
    ap.add_argument("--db-url")
    a = ap.parse_args()
    repo = Path(a.repo).resolve()
    email = a.reviewer.lower()
    seed = a.seed if a.seed is not None else int(datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"))
    rnd = random.Random(seed)
    con = connect(a.db_url)
    cur = con.cursor()
    cur.execute("SELECT role FROM review.reviewer WHERE email = %s AND active", [email])
    row = cur.fetchone()
    if not row:
        raise SystemExit("reviewer not found or inactive")
    owner = row[0] == "owner"
    if not owner and not 20 <= a.size <= 30:
        raise SystemExit("batches for invited reviewers have 20 to 30 items (section 6, V-07 25)")
    if owner and not 25 <= a.size <= 100 and not a.queue:
        raise SystemExit("owner batches have 25 to 100 items (V-07)")
    cur.execute("SELECT vocabulary FROM review.item WHERE export_version = %s LIMIT 1", [a.export])
    vrow = cur.fetchone()
    if not vrow:
        raise SystemExit(f"no items of {a.export} loaded")
    vocab = vrow[0]
    cur.execute("""SELECT s.item_id FROM review.assignment s JOIN review.batch b ON b.batch_id = s.batch_id
        WHERE s.reviewer_email = %s AND NOT b.flow_test""", [email])                      # flow test batches do not count
    seen = {r[0] for r in cur.fetchall()}

    if a.queue:
        cur.execute("""SELECT item_id FROM review.item WHERE export_version = %s AND queue = %s
            AND item_id NOT IN (SELECT item_id FROM review.assignment) ORDER BY item_id""", [a.export, a.queue])
        picked = [r[0] for r in cur.fetchall()][:a.size]
        gold, overlap = [], []
        spec = {"kind": "curation", "queue": a.queue, "export": a.export, "order": "item_id", "first": picked[0] if picked else None,
                "last": picked[-1] if picked else None, "size": len(picked)}
    else:
        cur.execute("""SELECT i.measure_pid, i.construct_pid FROM review.item i JOIN review.assignment s ON s.item_id = i.item_id
            JOIN review.batch b ON b.batch_id = s.batch_id WHERE i.queue IS NOT NULL AND b.status IN ('open', 'draft')""")
        in_queue = set(cur.fetchall())
        cur.execute("""SELECT item_id, measure_pid, construct_pid, stratum, is_gold FROM review.item
            WHERE export_version = %s AND queue IS NULL ORDER BY item_id""", [a.export])
        pool = [r for r in cur.fetchall() if r[0] not in seen and (r[1], r[2]) not in in_queue]
        cells = defaultdict(list)
        for iid, _, _, s, g in pool:
            if not g:
                cells[tuple(str(s.get(k)) for k in CELLS[vocab])].append((iid, s))
        cur.execute("""SELECT DISTINCT i.stratum FROM review.item i JOIN review.assignment s ON s.item_id = i.item_id
            JOIN review.batch b ON b.batch_id = s.batch_id WHERE s.reviewer_email = %s AND i.export_version = %s AND NOT b.flow_test""",
                    [email, a.export])
        covered = {tuple(str(s.get(k)) for k in CELLS[vocab]) for (s,) in cur.fetchall()}
        n_gold = round(a.size * 3 / 25)
        n_main = a.size - n_gold
        weight = {c: len(v) * oversample(vocab, v[0][1]) for c, v in cells.items()}
        order = sorted(cells, key=lambda c: (c in covered, -weight[c] * rnd.random()))
        total = sum(weight.values())
        quota = {c: max(1, math.floor(n_main * weight[c] / total)) for c in order}
        picked = []
        for c in order:
            if len(picked) >= n_main:
                break
            picked += [i for i, _ in rnd.sample(cells[c], min(quota[c], len(cells[c]), n_main - len(picked)))]
        rest = [i for c in order for i, _ in cells[c] if i not in set(picked)]
        rnd.shuffle(rest)
        picked += rest[:n_main - len(picked)]
        gold = [r[0] for r in pool if r[4]]
        gold = rnd.sample(gold, min(n_gold, len(gold)))
        overlap = [] if owner or not a.overlap_with else rnd.sample(picked, round(0.15 * len(picked)))
        spec = {"kind": "quality", "export": a.export, "seed": seed, "size": a.size, "cells": CELLS[vocab],
                "oversampled": "known error cells weighted 2", "gold": len(gold), "overlap_share": 0 if owner else (0.15 if a.overlap_with else 0),
                "overlap_with": a.overlap_with, "owner_round": owner, "cells_new_first": True}
    items = picked + gold
    rnd.shuffle(items) if not a.queue else None
    if not items:
        raise SystemExit("nothing left to draw")
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    cur.execute("SELECT count(*) FROM review.batch WHERE batch_id LIKE %s", [f"b-{day}-%"])
    bid = f"b-{day}-{cur.fetchone()[0] + 1:02d}"
    spec |= {"reviewer": "owner" if owner else "invited", "items": items, "overlap_items": overlap}
    cur.execute("INSERT INTO review.batch (batch_id, vocabulary, kind, description, sampling_spec, status) VALUES (%s, %s, %s, %s, %s, %s)",
                [bid, vocab, spec["kind"], f"{spec['kind']} batch of {len(items)} from {a.export}" + (f", queue {a.queue}" if a.queue else ""),
                 json.dumps(spec), "open" if a.open else "draft"])
    cur.executemany("INSERT INTO review.assignment (batch_id, item_id, reviewer_email, position, is_overlap) VALUES (%s, %s, %s, %s, %s)",
                    [(bid, i, email, n, False) for n, i in enumerate(items, 1)])
    if overlap:
        cur.executemany("INSERT INTO review.assignment (batch_id, item_id, reviewer_email, position, is_overlap) VALUES (%s, %s, %s, %s, %s)",
                        [(bid, i, a.overlap_with.lower(), n, True) for n, i in enumerate(overlap, 1)])
    con.commit()
    con.close()
    out = repo / "review" / "batches" / f"{bid}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"batch_id": bid, "vocabulary": vocab, **spec}, indent=1))
    counts = {"items": len(items), "gold": len(gold), "overlap": len(overlap), "status": "open" if a.open else "draft"}
    audit(f"Batch {bid} built from {a.export}", type="publish", inputs=[f"review.item {a.export}"], outputs=[f"review.batch {bid}", str(out)],
          counts=counts, vocab_repo=repo)
    print(bid, json.dumps(counts))


if __name__ == "__main__":
    main()
