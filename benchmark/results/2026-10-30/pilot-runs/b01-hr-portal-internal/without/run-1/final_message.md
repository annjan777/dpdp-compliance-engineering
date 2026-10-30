I wrote the assessment to `dpdp-submission.yaml` and didn't change the application code. The repo is one 14-line file, `hr_portal/app.py`, plus a README.

**Does the Act apply? Yes.** This is a leave portal for a company in Pune. It handles digital personal data of employees in India: names, work emails, reporting lines and free-text leave reasons that often describe health conditions. That puts it in scope under s.3(a).

Using the data for employment purposes is a "legitimate use" under s.7(i), so the company doesn't need employee consent or a s.5 notice. It still has to meet the s.8 duties on security, retention, processors and breach reporting.

There's a timing point: most of these duties only take effect around May 2027, 18 months after the Rules were notified on 13 Nov 2025. I rated the status as "applicable" and listed the timing as a question for a lawyer.

**Main problems found:**
1. **Anyone can read everyone's medical reasons (high).** `list_leaves` accepts a `requester_id` but never uses it, so it returns every employee's medical leave reason to any caller (s.8(5), r.6(1)(b)).
2. **Health details are posted to Slack (high).** Each leave reason is sent with the employee's name to a Slack webhook. That goes beyond what s.7(i) plausibly covers, and it raises questions about a contract with Slack as a data processor (s.8(2), r.6(1)(f)) and possibly about data going outside India (s.16).
3. **The Slack webhook secret is written into the code (medium).**
4. **Stored data is unencrypted (medium).** The SQLite database holds the medical reasons in plain text.
5. **No access logs (medium).** Nothing records who viewed or shared the data, so a breach couldn't be detected or reported (r.6(1)(c) and (e), s.8(6), r.7).
6. **Data is kept forever (medium).** There's no retention period or deletion, including after an employee leaves (s.8(7)).
7. **Anyone can file leave for anyone (medium).** `apply_leave` doesn't check who is calling, so any caller can submit a reason against any employee ID. It also crashes if the ID doesn't exist.
8. **Smaller issues (low).** All reasons, medical or not, go into one "medical" field and each new one overwrites the last. Employees also have no way to see, correct or delete their data, or to raise a complaint.

**Questions for a lawyer:**
- Does s.7(i) allow sharing reasons in a Slack channel, or only with the approving manager and HR?
- Is there a proper processor contract with Slack, and does storing data abroad raise any s.16 issue?
- How long must leave records be kept under labour law before they have to be deleted?
- Do Slack posts already sent count as a data breach that must be reported?