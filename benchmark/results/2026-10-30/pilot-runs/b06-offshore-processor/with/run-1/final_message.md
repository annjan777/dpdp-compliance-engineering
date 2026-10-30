I wrote the assessment to `dpdp-submission.yaml`. The file parses as valid YAML with 8 findings, and I didn't change any application code. This is an engineering assessment, not legal advice.

**Overall status: partially applicable.** The Act reaches the code, but most of it is switched off by an exemption.
- **Why it applies:** a Chennai company processes digital personal data in India, which brings it under the Act (s.3(a)).
- **Why most of it doesn't:** the data belongs only to US residents and is handled under a contract with a US insurer. That fits the exemption in s.17(1)(d), so notice, consent, data-subject rights, erasure and breach notification don't apply.
- **What still applies:** s.8(1) (accountability) and s.8(5) (reasonable security safeguards). Both come into force on **13 May 2027**, so these duties are fixed but not yet enforceable.

**Main problems in `etl/load_members.py`:**
1. **Critical (line 18):** every member's name and Social Security number is written to the logs in plain text.
2. **High:** Social Security numbers, dates of birth and diagnosis codes are stored unencrypted and unmasked in a local SQLite file.
3. **High:** the database has no access control. It sits at a default relative path with no file permissions and no authentication.
4. **Medium:** there are no access logs that record who reads the data by ID. The only log copies the personal data itself.
5. **Medium:** nothing checks that every record really belongs to someone outside India. The exemption depends on that, and right now the only support is the README's claim.
6. **Lower priority, not legally required here:** the Social Security number is copied into a reporting store that probably doesn't need it. There is also no retention limit or deduplication, and no connection close or rollback if a load fails.

**Questions for a lawyer:**
- Is the exemption fully met for every record?
- Do the detailed security minimums in the Rules (r.6) apply alongside s.8(5) when the exemption is in play?
- Is the Chennai company the party that decides how the data is used, or only a processor acting for the insurer? This decides who owes the security duty.
- Please confirm the 13 May 2027 start date against the official notice.
- Because DPDP breach notification is switched off here, which contract and US-law (e.g. HIPAA) breach duties apply instead?