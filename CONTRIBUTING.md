# Contributing

Thanks for helping. This project is most useful when it stays accurate and measurable, so contributions are judged on evidence.

## Good first contributions

- **New benchmark case.** A small synthetic app in `benchmark/cases/<id>/files/`, plus a `benchmark/truth/<id>.yaml` with the problems an assessment must find and their locations. Run `python -m pytest -q benchmark/tests`; one test checks that every truth location exists in its fixture. Synthetic data only.
- **A fixture in another stack.** Django, Spring, Go, Rails or Laravel.
- **Legal registry corrections** in `references/legal-sources.md`. Cite the official gazette text (MeitY PDF and page). Corrections from practising privacy lawyers are especially welcome; say so in the PR if you'd like credit.
- **False positives or misses** that you saw when running the skill on real code. Open an issue describing the pattern. Don't include proprietary code or real personal data.

## Before opening a PR

```bash
pip install pyyaml pytest
python -m pytest -q scripts/tests benchmark/tests
python scripts/validate_assessment.py examples/campus-clinic/.dpdp/assessment.yaml --strict
```

CI runs the same commands.

## Rules that PRs must keep

- No claims of guaranteed compliance, anywhere.
- Only cite provisions that exist in the registry; the validator enforces this.
- Mandatory obligations stay separate from best practice.
- Benchmark results are reported as measured, including when the skill does worse.

## Reviews

The maintainer aims to respond within a week. Changes to legal interpretation need a source; changes to scoring need a test.
