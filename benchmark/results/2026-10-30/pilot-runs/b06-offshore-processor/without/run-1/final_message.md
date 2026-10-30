I've written `dpdp-submission.yaml` and didn't change the application code.

**Does the Act apply? Partially (`partially-applicable`).** A Chennai company handling digital personal data counts as processing in India, so the Act reaches it (s.3(a)). But the data belongs only to US residents and is handled under a contract with a US insurer. That is the s.17(1)(d) exemption, which switches off most of the Act: consent, notice, the rights of the people whose data it is, breach notification and retention limits. Two duties still apply: general compliance under s.8(1) and **reasonable security safeguards under s.8(5)**, which Rule 6 spells out in more detail.

**Findings in `etl/load_members.py`:**
1. **High, mandatory:** line 15 writes every member's name and full SSN to the logs as plain text.
2. **High, mandatory:** SSNs are stored in the database without encryption, masking or tokens (Rule 6(1)(a)).
3. **Medium, mandatory:** diagnosis codes, which are health data, are stored in plain text next to name, SSN and date of birth.
4. **Medium, mandatory:** the database is a local SQLite file with no access control and default file permissions (Rule 6(1)(b)).
5. **Low, mandatory:** nothing records who reads or exports the data (Rule 6(1)(c) and 6(1)(e)).
6. **Low, best practice:** the full SSN probably isn't needed for reporting, and records are never deleted. Both are advisable fixes, but the exemption means the Act doesn't require them.

**Questions for a lawyer:**
- Does the exemption really hold? It depends on every person in the feed being outside India and the company sticking to the contracted processing.
- Who carries the s.8(5) duty the exemption keeps: the US insurer or the Chennai company? Does Rule 6 bind the company directly or only through its contract?
- Do separate Indian rules apply anyway, such as CERT-In's log retention and incident reporting directions?