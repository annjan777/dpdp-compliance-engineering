I've written the assessment to `dpdp-submission.yaml` and didn't change any application code. I didn't run a YAML parser on it.

**Applicability: applicable.** The README assumes an internal university portal is outside the DPDP Act, but nothing in the Act says that. The portal handles digital personal data about identifiable students and staff, including their symptoms, so it falls under the Act (s.2(t), s.3(a)). Sending data to a US analytics vendor is a cross-border transfer under s.16. Some exemptions may cover part of it: the State-instrumentality exemption (s.17(2)(a)) and the education and healthcare exemptions for children's data (Rules r.12, Fourth Schedule). They are narrow, though, and I've listed them as questions for a lawyer rather than assuming they apply.

**Timing:** today is 30 October 2026, and under the phased start dates in the Rules, most of the obligations behind these findings take effect around 13 May 2027.

**Main findings (14 in total):**
- **Critical:** every booking sends the patient's email and symptoms to the US analytics vendor (`app.py:54`). There is no notice, no consent, no data minimisation and no contract with the vendor.
- **Critical:** `get_appointments` never checks who is asking, so any user can read anyone else's appointments and symptoms (`app.py:58`).
- **High:** marketing consent is switched on by default and there is no way to opt out (s.6(1), s.6(4)).
- **High:** deleting a user leaves their appointments and symptoms in the database, and the vendor is never asked to erase its copy (s.8(7), s.12(3)).
- **High:** users get no privacy notice when they register (s.5, r.3).
- **High:** date of birth is collected, but there is no age check or parental consent for students under 18 (s.9, r.10).
- **Medium:**
  - registration logs names, emails and phone numbers in plain text;
  - health data is stored unencrypted;
  - there are no access logs or way to detect a breach and report it (s.8(6), r.7);
  - there is no retention limit;
  - users have no way to exercise their rights or raise a complaint (s.11–14).
- **Low:** phone, date of birth and roll number are collected without a clear need for booking (data minimisation).

The open questions for a lawyer are:
- whether the university qualifies for the State-instrumentality exemption;
- how far the education and healthcare exemptions reach;
- whether the medical-treatment grounds in s.7 cover any of the clinical processing;
- whether any rules restrict transfers to the vendor's country;
- whether the university could be named a Significant Data Fiduciary.