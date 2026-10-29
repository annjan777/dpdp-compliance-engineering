#!/usr/bin/env bash
# Build a run-staging plugin dir: the skill (no evals/benchmark/examples/truth) + runnable benchmark cases.
# Ground truth never enters the staging dir, so runs cannot read it.
set -eu
REPO="$(cd "$(dirname "$0")/.." && pwd)"
STAGE="${1:?usage: build_stage.sh STAGE_DIR}"
mkdir -p "$STAGE"
for p in SKILL.md references assets scripts; do cp -R "$REPO/$p" "$STAGE/"; done
for c in "$REPO"/benchmark/cases/*/; do
  name="$(basename "$c")"; d="$STAGE/bench-cases/$name"
  mkdir -p "$d/graders"; cp -R "$c/files" "$d/files"
  printf -- '---\ntags: [dpdp-bench]\nmax_turns: 40\ntimeout_seconds: 1200\nallowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]\n---\n\n' > "$d/prompt.md"
  cat "$REPO/benchmark/PROMPT.md" >> "$d/prompt.md"
  printf 'schema_version: "1.1"\nname: %s\nexpected_outcome: |\n  Writes dpdp-submission.yaml; scored offline by benchmark/score.py.\ncontext:\n  scaffold_script: place-files.sh\n' "$name" > "$d/case.yaml"
  printf '#!/usr/bin/env bash\nset -eu\ncp -R "$(dirname "$0")/files/." .\n' > "$d/place-files.sh"; chmod +x "$d/place-files.sh"
  printf -- '---\ntype: file_exists\npath: dpdp-submission.yaml\n---\n\nThe agent wrote dpdp-submission.yaml.\n' > "$d/graders/01-submission-written.md"
done
find "$STAGE" -name __pycache__ -prune -exec rm -rf {} +
echo "staged $(ls "$STAGE/bench-cases" | wc -l) cases in $STAGE"
