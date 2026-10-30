I wrote the assessment to `dpdp-submission.yaml` and didn't change any application code.

**Applicability: not currently applicable.** Pocket Ledger runs only on each person's own computer, with no server, accounts, telemetry or network calls. The author never receives the data or decides why or how it's processed, so the author isn't a Data Fiduciary under Act s.2(i). Each user is recording their own expenses for personal use, which falls under the personal/domestic exclusion in Act s.3(c)(i). The README's assumption that DPDP doesn't apply is right for now.

**Findings (none are mandatory under DPDP):**
1. **Medium, security:** `export_csv` saves by default to a fixed filename in the shared system temp folder (`ledger/core.py:24-26`). On a computer with several user accounts, others may be able to read the file. Someone could also create that file or a link in its place before the export runs.
2. **Low, security:** the database `~/.pocket-ledger.db` is created with default file permissions and isn't encrypted, so other accounts on the machine may be able to read the expense notes.
3. **Low, best practice:** notes go into the CSV unchanged. A note starting with `=`, `+`, `-` or `@` can run as a formula when the file is opened in a spreadsheet program.
4. **Low, best practice:** there's no way to delete entries or exported files, and notes may contain other people's names.

**Questions for a lawyer:**
- If an employer or other organisation requires staff to use the tool, or collects their exports, does that organisation become a Data Fiduciary?
- If the author later adds sync, accounts or telemetry, does the author take on obligations? These would include notice and consent (Act s.5 and s.6) and security safeguards (Act s.8(5), Rules r.6).