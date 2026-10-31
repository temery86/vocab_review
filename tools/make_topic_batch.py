"""A topic batch for one reviewer, drawn from both vocabularies (Tom Emery, 31 October 2026), for area experts routed
by expertise (section 6).

Items are quality sample items whose construct label matches --pattern (case insensitive) and none of --exclude.
The batch splits evenly between the exports given, takes at most one item per construct, spreads items over
programmes or countries, and adds gold items at 3 per 25 (V-07), from the topic where there are enough, else from
the whole export, never one the reviewer has seen. The specification with the seed goes to batch.sampling_spec and
to review/batches/<batch_id>.json in each vocabulary repository, with an audit event in each.

Usage: .venv/bin/python tools/make_topic_batch.py --reviewer x@example.org --topic "family policy" \
         --pattern "childcare|parental leave|..." --scv <scv repo> scv-review-0.3.0 --rvv <rvv repo> rvv-review-0.1.0 --open
"""
import argparse
import json
import random
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import audit, connect  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reviewer", required=True)
    ap.add_argument("--topic", required=True)
    ap.add_argument("--pattern", required=True)
    ap.add_argument("--exclude", default="")
    ap.add_argument("--scv", nargs=2, metavar=("REPO", "EXPORT"))
    ap.add_argument("--rvv", nargs=2, metavar=("REPO", "EXPORT"))
    ap.add_argument("--size", type=int, default=25)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--open", action="store_true")
    ap.add_argument("--db-url")
    a = ap.parse_args()
    parts = [(v, Path(x[0]).resolve(), x[1]) for v, x in (("scv", a.scv), ("rvv", a.rvv)) if x]
    if not parts:
        raise SystemExit("give --scv and or --rvv")
    seed = a.seed if a.seed is not None else int(datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"))
    rnd = random.Random(seed)
    email = a.reviewer.lower()
    con = connect(a.db_url)
    cur = con.cursor()
    cur.execute("SELECT role FROM review.reviewer WHERE email = %s AND active", [email])
    if not cur.fetchone():
        raise SystemExit("reviewer not found or inactive")
    cur.execute("""SELECT s.item_id FROM review.assignment s JOIN review.batch b ON b.batch_id = s.batch_id
        WHERE s.reviewer_email = %s AND NOT b.flow_test""", [email])
    seen = {r[0] for r in cur.fetchall()}
    n_gold = round(a.size * 3 / 25)
    n_main = a.size - n_gold
    share = [n_main // len(parts) + (1 if k < n_main % len(parts) else 0) for k in range(len(parts))]
    picked, gold, per = [], [], {}
    for (vocab, repo, export), n in zip(parts, share):
        cur.execute("""SELECT item_id, construct_pid, coalesce(stratum->>'programme', stratum->>'country'), is_gold FROM review.item
            WHERE export_version = %s AND queue IS NULL AND construct_label ~* %s AND NOT (%s <> '' AND construct_label ~* %s)
            ORDER BY item_id""", [export, a.pattern, a.exclude, a.exclude])
        pool = [r for r in cur.fetchall() if r[0] not in seen]
        by_c = defaultdict(list)
        for iid, cp, place, g in pool:
            if not g:
                by_c[cp].append((iid, place))
        cons = list(by_c)
        rnd.shuffle(cons)
        used_place = defaultdict(int)
        chosen = []
        for cp in sorted(cons, key=lambda c: rnd.random()):          # one per construct, spread over places
            opts = sorted(by_c[cp], key=lambda x: (used_place[x[1]], rnd.random()))
            if len(chosen) < n:
                chosen.append(opts[0][0])
                used_place[opts[0][1]] += 1
        picked += chosen
        per[vocab] = {"export": export, "items": len(chosen), "constructs_available": len(cons), "places": dict(used_place)}
        topic_gold = [r[0] for r in pool if r[3]]
        gold += topic_gold
    gold = rnd.sample(gold, min(n_gold, len(gold)))
    if len(gold) < n_gold:                                                  # top up from the whole exports
        cur.execute("SELECT item_id FROM review.item WHERE is_gold AND queue IS NULL AND export_version = ANY(%s) ORDER BY item_id",
                    [[p[2] for p in parts]])
        rest = [r[0] for r in cur.fetchall() if r[0] not in seen and r[0] not in gold]
        gold += rnd.sample(rest, n_gold - len(gold))
    items = picked + gold
    rnd.shuffle(items)
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    cur.execute("SELECT count(*) FROM review.batch WHERE batch_id LIKE %s", [f"b-{day}-%"])
    bid = f"b-{day}-{cur.fetchone()[0] + 1:02d}"
    vocab_col = parts[0][0] if len(parts) == 1 else "mixed"
    spec = {"kind": "quality", "topic": a.topic, "pattern": a.pattern, "exclude": a.exclude, "seed": seed, "size": a.size,
            "per_vocabulary": per, "gold": len(gold), "overlap_share": 0, "reviewer": "invited", "routing": "expertise", "items": items}
    cur.execute("INSERT INTO review.batch (batch_id, vocabulary, kind, description, sampling_spec, status) VALUES (%s, %s, 'quality', %s, %s, %s)",
                [bid, vocab_col, f"{a.topic.capitalize()}, {len(items)} items from survey and register data" if len(parts) > 1 else
                 f"{a.topic.capitalize()}, {len(items)} items", json.dumps(spec), "open" if a.open else "draft"])
    cur.executemany("INSERT INTO review.assignment (batch_id, item_id, reviewer_email, position, is_overlap) VALUES (%s, %s, %s, %s, false)",
                    [(bid, i, email, k) for k, i in enumerate(items, 1)])
    con.commit()
    con.close()
    for vocab, repo, export in parts:
        out = repo / "review" / "batches" / f"{bid}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"batch_id": bid, "vocabulary": vocab_col, **spec}, indent=1))
        audit(f"Topic batch {bid} ({a.topic}) built", type="publish", inputs=[f"review.item {export}"], outputs=[f"review.batch {bid}", str(out)],
              counts={"items": len(items), "from_this_vocabulary": per[vocab]["items"], "gold": len(gold)}, vocab_repo=repo)
    print(bid, json.dumps({"items": len(items), "gold": len(gold), **{v: p["items"] for v, p in per.items()}}))


if __name__ == "__main__":
    main()
