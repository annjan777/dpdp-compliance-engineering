I wrote the assessment to `dpdp-submission.yaml` and didn't change any application code.

**Applicability: `not-currently-applicable`, high confidence.** I didn't take the README's claim that DPDP doesn't apply at face value. I checked the code: `ledger/core.py` only uses `csv`, `os`, `sqlite3` and `tempfile`, with no network calls, accounts or telemetry. Each person records their own expenses on their own machine, which is personal use and falls under the exclusion in **Act s.3(c)(i)**. No data reaches the developer, so the developer isn't a Data Fiduciary (**s.2(i)**). That would change if the developer added telemetry, sync, crash reports or accounts, or if an organisation used the tool to record expenses about other people. Both of these are listed as legal questions.

**Findings (none are DPDP obligations, so all have `mandatory: false`):**
1. **Security weakness, medium, `core.py:26-31`:** by default, `export_csv` writes every expense to a file with a fixed, predictable name in the shared system temp folder. Other users on the same machine may be able to read it, someone could create or redirect that file before the export runs, and it's never deleted.
2. **Best practice, low, `core.py:6-12`:** the database file is created with default file permissions and no encryption, so other users on a shared machine may be able to read it.
3. **Best practice, low, `core.py:10-18`:** there's no way to edit or delete a single entry. Free-text notes may mention other people, and the only way to remove them is to delete the whole database file.

I didn't run the test suite, because no code was changed. This is an engineering assessment, not legal advice.