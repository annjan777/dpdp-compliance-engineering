#!/usr/bin/env python3
"""Merge `claude plugin eval` ablation results and summarise with-skill vs without-skill.

Runs that ended on an error (rate limit, harness failure) are excluded and counted, never scored as 0.
"All" averages only cases that have valid runs in both arms, so the two arms cover the same cases.

Usage: python3 summarize_ablation.py RESULT_JSON [RESULT_JSON ...] [--md OUT.md]
Order matters: for each case and arm, the first file listed that has any valid run supplies all runs.
List re-run files before the original run.
"""
import argparse
import json
from collections import defaultdict


def collect(paths):
    runs = defaultdict(list)  # (case, arm) -> list of (source, run)
    meta = []
    for p in paths:
        r = json.load(open(p))
        meta.append({"file": p, "claude": r["claudeVersion"], "model": r["suite"]["modelOverride"],
                     "judge": r["suite"]["judgeModel"], "started": r["startedAt"], "costUsd": round(r["costUsd"], 2)})
        for c in r["cases"]:
            for arm, rs in c["arms"].items():
                runs[(c["name"], arm)].append((p, rs))
    merged, excluded = {}, defaultdict(int)
    for key, sources in runs.items():
        chosen = []
        for _, rs in sources:  # first file with any valid run for this case+arm wins, whole set
            valid = [x for x in rs if not x.get("error")]
            if valid:
                chosen = valid
                excluded[key] += len(rs) - len(valid)
                break
            excluded[key] += len(rs)
        merged[key] = chosen
    return merged, excluded, meta


def mean(xs):
    return sum(xs) / len(xs) if xs else None


def fmt(x, signed=False):
    return "n/a" if x is None else (f"{x:+.2f}" if signed else f"{x:.2f}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("results", nargs="+")
    ap.add_argument("--md")
    o = ap.parse_args()
    merged, excluded, meta = collect(o.results)
    cases = sorted({c for c, _ in merged})
    lines = ["| Case | With skill: runs, mean score | Without: runs, mean score | Δ | With: grader passes | Without: grader passes |",
             "|---|---|---|---|---|---|"]
    tw, two = [], []
    for c in cases:
        w, wo = merged.get((c, "with"), []), merged.get((c, "without"), [])
        sw, swo = [x["score"] for x in w], [x["score"] for x in wo]
        if sw and swo:
            tw += sw
            two += swo
        g = lambda rs: " ".join("".join("P" if gr["passed"] else "F" for gr in x["graders"]) for x in rs)
        d = (mean(sw) - mean(swo)) if sw and swo else None
        lines.append(f"| {c} | {len(sw)}, {fmt(mean(sw))} | {len(swo)}, {fmt(mean(swo))} | {fmt(d, True)} | {g(w)} | {g(wo)} |")
    tot = mean(tw) - mean(two) if tw and two else None
    lines.append(f"| **All (cases with both arms)** | {len(tw)}, {fmt(mean(tw))} | {len(two)}, {fmt(mean(two))} | {fmt(tot, True)} | | |")
    ex = {f"{c}/{a}": n for (c, a), n in excluded.items() if n}
    out = "\n".join(lines) + f"\n\nExcluded errored runs: {ex or 'none'}\n\nSources: " + json.dumps(meta, indent=1) + "\n"
    print(out)
    if o.md:
        open(o.md, "w").write(out)


if __name__ == "__main__":
    main()
