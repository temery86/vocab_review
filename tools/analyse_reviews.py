"""Analyse one review export (sections 8 and 12.4, V-06) and write <repo>/reports/review-<date>.md.

Only quality sample items are analysed. Curation answers are not used for quality estimates (12.7). Owner rounds are
reported apart from invited rounds and never pooled for the headline estimates (12.4).
- Membership precision per stratum, with Wilson 95 percent intervals. Unsure answers are reported apart and left out of
  the denominator. Gold items are left out of the estimates and used for reviewer accuracy.
- Grade accuracy per stratum and per grade, for graded items with an answer to question 2.
- Agreement on overlap items, Cohen's kappa for membership and for grade.
- Gold item accuracy per reviewer, the owner included so drift is visible.
- Gap detection. Free text better construct answers and missing construct comments, embedded with the vocabulary's
  pinned model and clustered when sentence_transformers is importable (run with the scv repository's .venv python), else listed.
  Clusters with answers from more than one reviewer are candidate systematic gaps.
- Error patterns. Wrong answers by method, construct type, programme or country and placement.
- For each stratum of an invited round, whether the lower bound clears the V-06 threshold (membership 0.95, grade 0.85).

Usage: python tools/analyse_reviews.py ../scv --export ../scv/review/exports/<stamp>
"""
import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import audit, vocab_of  # noqa: E402

THRESH = {"membership": 0.95, "grade": 0.85}
STRATA = {"scv": ["programme", "construct_type", "method", "grade", "battery_construct"],
          "rvv": ["country", "body", "placement", "statement_basis", "provisional", "definition_provenance"]}
MODEL_NAME = "BAAI__bge-large-en-v1.5@d4aa6901d3a4"     # the pinned model of ../scv (D-25), found from the vocabulary repository


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None, None)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, max(0.0, c - h), min(1.0, c + h))


def kappa(pairs):
    if not pairs:
        return None
    labs = sorted({x for p in pairs for x in p})
    n = len(pairs)
    po = sum(a == b for a, b in pairs) / n
    pe = sum((sum(a == l for a, _ in pairs) / n) * (sum(b == l for _, b in pairs) / n) for l in labs)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def load(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def js(v):
    return json.loads(v) if isinstance(v, str) and v[:1] in "{[" else (v or {})


def fmt(t):
    p, lo, hi = t
    return "n/a" if p is None else f"{p:.2f} ({lo:.2f} to {hi:.2f})"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--export", required=True)
    a = ap.parse_args()
    repo, d = Path(a.repo).resolve(), Path(a.export).resolve()
    vocab = vocab_of(repo)
    J_all = load(d / "reviews_joined.jsonl")
    J = [r for r in J_all if r.get("flow_test") not in (True, "true", "True")]      # flow test batches are left out
    comments = load(d / "batch_comment.jsonl")
    quality = [r for r in J if not r.get("queue")]
    for r in quality:
        r["stratum"] = js(r.get("stratum"))
        r["is_gold"] = r.get("is_gold") in (True, "true", "True")
    L = [f"# Review analysis, {vocab}, export {d.name}", "", f"Written {datetime.now(timezone.utc).date()} by `tools/analyse_reviews.py`. "
         f"{len(J)} current responses ({len(J_all) - len(J)} more in batches marked as a flow test are left out), {len(quality)} on quality sample items, {len(J) - len(quality)} on curation items, which are not used for "
         "quality estimates. Owner rounds are reported apart from invited rounds and are not judged against the V-06 threshold.", ""]
    counts = {"responses": len(J), "quality": len(quality)}
    for group, sel in (("Invited rounds", lambda r: r.get("reviewer_role") != "owner"), ("Owner rounds", lambda r: r.get("reviewer_role") == "owner")):
        rs = [r for r in quality if sel(r) and not r["is_gold"]]
        L += [f"## {group}", ""]
        if not rs:
            L += ["No responses.", ""]
            continue
        judged = group == "Invited rounds"
        for kind in ("membership", "grade"):
            L += [f"### {'Membership precision' if kind == 'membership' else 'Grade accuracy'}", "",
                  "| Stratum | Value | Answered | Unsure | Estimate (95 percent interval) |" + (" Clears V-06 |" if judged else ""),
                  "|---|---|---|---|---|" + ("---|" if judged else "")]
            for key in ["all"] + STRATA[vocab] + (["grade_shown"] if kind == "grade" else []):
                cells = defaultdict(list)
                for r in rs:
                    if kind == "grade" and (not r.get("grade") or r.get("grade_ok") in (None, "", "not_shown")):
                        continue
                    v = "all" if key == "all" else (r.get("grade") if key == "grade_shown" else r["stratum"].get(key))
                    cells[str(v)].append(r)
                for v, xs in sorted(cells.items()):
                    if kind == "membership":
                        ok, bad, uns = (sum(x.get("belongs") == "yes" for x in xs), sum(x.get("belongs") == "no" for x in xs),
                                        sum(x.get("belongs") == "unsure" for x in xs))
                    else:
                        ok, bad, uns = (sum(x.get("grade_ok") == "yes" for x in xs), sum(x.get("grade_ok") == "no" for x in xs),
                                        sum(x.get("grade_ok") == "unsure" for x in xs))
                    w = wilson(ok, ok + bad)
                    clear = "" if not judged else (" yes |" if w[1] is not None and w[1] >= THRESH[kind] else " no |")
                    L.append(f"| {key} | {v} | {ok + bad} | {uns} | {fmt(w)} |{clear}")
            L.append("")
        ov = defaultdict(dict)
        for r in quality:
            ov[r["item_id"]][r["reviewer"]] = r
        pairs = [list(v.values())[:2] for v in ov.values() if len(v) >= 2]
        km = kappa([(x.get("belongs"), y.get("belongs")) for x, y in pairs])
        kg = kappa([(x.get("grade_ok"), y.get("grade_ok")) for x, y in pairs if x.get("grade") and x.get("grade_ok") and y.get("grade_ok")])
        if judged:
            L += ["### Agreement on overlap items", "", f"{len(pairs)} items answered by two reviewers. Cohen's kappa for membership "
                  f"{'n/a' if km is None else f'{km:.2f}'}, for grade {'n/a' if kg is None else f'{kg:.2f}'}.", ""]
        wrong = [r for r in rs if r.get("belongs") == "no" or r.get("grade_ok") == "no"]
        L += ["### Error patterns", "", f"{len(wrong)} wrong answers (membership no or grade not right).", "",
              "| Method | Construct type or placement | Programme or country | Wrong |", "|---|---|---|---|"]
        pat = Counter((r.get("method"), r["stratum"].get("construct_type") or r["stratum"].get("placement"),
                       r["stratum"].get("programme") or r["stratum"].get("country")) for r in wrong)
        L += [f"| {m} | {t} | {p} | {n} |" for (m, t, p), n in pat.most_common(20)] + [""]
        counts[f"{group} answered"] = len(rs)
    # gold
    L += ["## Gold item accuracy per reviewer", "", "| Reviewer | Role | Gold answered | Membership right | Grade right |", "|---|---|---|---|---|"]
    gold = defaultdict(list)
    for r in quality:
        if r["is_gold"]:
            gold[(r["reviewer"], r.get("reviewer_role"))].append(r)
    for (rv, role), xs in sorted(gold.items()):
        mb = [x for x in xs if x.get("gold_belongs") and x.get("belongs") in ("yes", "no")]
        gr = [x for x in xs if x.get("gold_grade") and x.get("grade_ok") in ("yes", "no")]
        m_ok = sum((x["belongs"] == "yes") == (x["gold_belongs"] == "yes") for x in mb)
        g_ok = sum((x["grade_ok"] == "yes") == (x["gold_grade"] == x.get("grade")) or (x.get("correct_grade") == x["gold_grade"]) for x in gr)
        L.append(f"| {rv} | {role} | {len(xs)} | {m_ok} of {len(mb)} | {g_ok} of {len(gr)} |")
    L.append("")
    # gaps
    texts = [(r["reviewer"], r["better_construct_text"]) for r in J if (r.get("better_construct_text") or "").strip()]
    texts += [(c["reviewer"], c["missing_constructs"]) for c in comments if (c.get("missing_constructs") or "").strip()]
    L += ["## Gap detection", ""]
    if not texts:
        L += ["No free text answers or missing construct comments.", ""]
    else:
        groups = None
        try:
            from sentence_transformers import SentenceTransformer
            from sklearn.cluster import AgglomerativeClustering
            model = next(p for p in (repo / "models" / MODEL_NAME, repo.parent / "scv" / "models" / MODEL_NAME) if p.exists())
            V = SentenceTransformer(str(model)).encode([t for _, t in texts], normalize_embeddings=True)
            lab = AgglomerativeClustering(n_clusters=None, distance_threshold=0.35, metric="cosine", linkage="average").fit(V).labels_ \
                if len(texts) > 1 else [0]
            groups = defaultdict(list)
            for (rv, t), k in zip(texts, lab):
                groups[k].append((rv, t))
        except Exception as e:  # the pinned model is not importable here
            L += [f"Clustering skipped ({type(e).__name__}), run with the scv repository's .venv python for the pinned model. The answers are listed.", ""]
        if groups:
            L += ["| Cluster | Reviewers | Answers | Example |", "|---|---|---|---|"]
            for k, xs in sorted(groups.items(), key=lambda kv: -len({r for r, _ in kv[1]})):
                L.append(f"| {k} | {len({r for r, _ in xs})}{' (candidate systematic gap)' if len({r for r, _ in xs}) > 1 else ''} | {len(xs)} | "
                         f"{xs[0][1][:100].replace('|', '/')} |")
        else:
            L += [f"- {rv}. {t[:200]}" for rv, t in texts]
        L.append("")
    out = repo / "reports" / f"review-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n")
    counts["gold_answered"] = sum(len(v) for v in gold.values())
    counts["gap_texts"] = len(texts)
    audit(f"Review analysis of export {d.name}", type="validate", inputs=[str(d)], outputs=[str(out)], counts=counts, vocab_repo=repo)
    print(out, json.dumps(counts))


if __name__ == "__main__":
    main()
