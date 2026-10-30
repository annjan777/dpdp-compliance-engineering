I wrote the assessment to `dpdp-submission.yaml`. It parses as valid YAML and holds 10 findings. I didn't change any application code.

**Does the Act apply? Yes (`applicable`).** The code is an internal leave portal for a company in Pune. It stores employee names, work emails, who their manager is and free-text medical leave reasons in a database. That makes it digital personal data processed in India, which the Act covers (s.3(a)), and the company is the Data Fiduciary, the party that decides why and how the data is processed. The likely lawful basis is the employment exception in s.7(i), which means the company doesn't need employee consent. However, most of the actual duties (s.4–17 and Rules r.3 and r.5–16) **start on 13 May 2027**, so they apply to this system but can't be enforced yet. Problems marked `mandatory: true` should be fixed before that date.

**Main problems in `hr_portal/app.py`:**
1. **Critical:** `list_leaves` (lines 13–14) accepts `requester_id` but never uses it, so anyone who calls it gets every employee's name and medical leave reason.
2. **High:** `apply_leave` (lines 7–8) doesn't check who is calling, so anyone can overwrite any employee's medical leave reason.
3. **High:** each leave request posts the employee's name and medical reason to a Slack channel (lines 10–11). This shares health details more widely than the purpose needs, and there's no sign of a data-processing contract with Slack.
4. **Medium:**
   - the Slack webhook secret is written directly into the source code;
   - medical data is stored unencrypted in a local SQLite file;
   - nothing logs who reads or changes the data;
   - nothing ever deletes the medical data.
5. **Low:** each new leave request overwrites the previous reason, and the leave days are never saved, so there's no leave history. There's also no error handling, and the Slack call has no timeout.

**Questions for a lawyer:**
- Does the employment exception cover storing the specific medical reason, or only the fact that someone took leave?
- Is posting medical reasons to Slack within that employment purpose?
- Is Slack covered by a proper processor contract, and where does it store the data?
- How long must leave records be kept under labour law?
- Where does the company publish its privacy contact and its process for employee complaints? Neither is visible in this repo.

This is an engineering assessment, not legal advice.