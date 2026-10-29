#!/usr/bin/env python3
"""Collect submissions, final messages and leak checks from a `claude plugin eval --keep-temp` run.

Usage: python3 collect_runs.py RESULT_JSON RUNS_DIR [--leak-pattern REGEX ...]
Writes RUNS_DIR/<case>/<arm>/run-N/{dpdp-submission.yaml, final_message.md, meta.json}
and prints, per run, any tool call whose input matches a leak pattern (e.g. reads of ground truth).
"""
import argparse
import json
import os
import re
import shutil

DEFAULT_LEAKS = [r"/truth/", r"benchmark/truth", r"/evals/[^\"']*/graders", r"dpdp-compliance-engineering-workspace"]


def trace_lines(path):
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line.startswith("{"):
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue


def final_message(lines):
    res = [l for l in lines if l.get("type") == "result" and l.get("result")]
    if res:
        return res[-1]["result"]
    texts = [c.get("text", "") for l in lines if l.get("type") == "assistant"
             for c in l.get("message", {}).get("content", []) if c.get("type") == "text"]
    return texts[-1] if texts else ""


def tool_calls(lines):
    return [(c.get("name"), json.dumps(c.get("input"))) for l in lines if l.get("type") == "assistant"
            for c in l.get("message", {}).get("content", []) if c.get("type") == "tool_use"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("result_json")
    ap.add_argument("runs_dir")
    ap.add_argument("--leak-pattern", action="append", default=None)
    o = ap.parse_args()
    leaks = [re.compile(p) for p in (o.leak_pattern or DEFAULT_LEAKS)]
    result = json.load(open(o.result_json))
    summary = []
    for case in result["cases"]:
        for arm, runs in case["arms"].items():
            for i, run in enumerate(runs, 1):
                out = os.path.join(o.runs_dir, case["name"], arm, f"run-{i}")
                os.makedirs(out, exist_ok=True)
                trace = run.get("tracePath")
                root = os.path.dirname(os.path.dirname(trace)) if trace else None
                cwd = os.path.join(root, "home", "cwd") if root else None
                sub = os.path.join(cwd, "dpdp-submission.yaml") if cwd else None
                if sub and os.path.exists(sub):
                    shutil.copy(sub, os.path.join(out, "dpdp-submission.yaml"))
                lines = list(trace_lines(trace)) if trace and os.path.exists(trace) else []
                calls = tool_calls(lines)
                leak_hits = [f"{n}: {inp[:160]}" for n, inp in calls if any(p.search(inp) for p in leaks)]
                skill_used = any(n == "Skill" or "SKILL.md" in inp for n, inp in calls)
                with open(os.path.join(out, "final_message.md"), "w", encoding="utf-8") as fh:
                    fh.write(final_message(lines))
                meta = {"case": case["name"], "arm": arm, "run": i, "error": run.get("error"), "turns": run.get("turns"),
                        "costUsd": run.get("costUsd"), "durationSeconds": run.get("durationSeconds"),
                        "trace_found": bool(lines), "submission_found": os.path.exists(os.path.join(out, "dpdp-submission.yaml")),
                        "skill_used": skill_used, "tool_calls": len(calls), "leak_hits": leak_hits}
                json.dump(meta, open(os.path.join(out, "meta.json"), "w"), indent=2)
                summary.append(meta)
    for m in summary:
        flag = " LEAK:" + "; ".join(m["leak_hits"]) if m["leak_hits"] else ""
        print(f"{m['case']}\t{m['arm']}\trun-{m['run']}\tsub={m['submission_found']}\tskill={m['skill_used']}\t"
              f"turns={m['turns']}\t${m['costUsd']}\terr={bool(m['error'])}{flag}")


if __name__ == "__main__":
    main()
