I wrote the assessment to `dpdp-submission.yaml`. It has 15 findings and parses as valid YAML. I didn't change any application code.

**Does the Act apply? Yes, with high confidence.** The portal processes digital personal data about identifiable students and staff in India, including health symptoms, and the university decides why and how it's processed (Act s.3(a), s.2(t), s.2(i)). The README says the app was built on the assumption that "an internal university portal is outside the DPDP Act". That isn't an exemption under the Act. The only carve-out in play is the partial State exemption in s.17(4), which needs legal review. The substantive obligations take effect on **13 May 2027** (G.S.R. 843(E)), so they apply to this processing but can't be enforced yet.

**Top problems:**
1. **Any user can read any user's appointments and symptoms (critical).** `get_appointments` ignores `requester_id` (`clinic/app.py:58`). There is also no login or role check anywhere in the code.
2. **Health data goes to a US analytics vendor (critical).** Every booking sends the user's email and symptoms to the vendor (`clinic/app.py:54`). There's no lawful ground, no notice, no trimming of the data, and no record of a processor contract.
3. **Marketing consent is pre-ticked (high).** It defaults to opted-in in both the database and `register()`, and there's no way to withdraw (s.6(1), s.6(4)).
4. **Missing basics (high/medium):**
   - no notice or consent record
   - no way for users to see, correct or erase their data
   - no published contact person or complaint process
   - deleting a user leaves their appointments and symptoms behind and doesn't reach the vendors
5. **Weak security handling (medium):**
   - names, emails and phone numbers are written to logs in plain text
   - health data is stored unencrypted
   - there's no audit logging of who reads health records
   - there's no process for reporting a data breach
6. **Possible minors.** Date of birth is collected, but there's no age check before analytics tracking. I left this as non-mandatory until someone confirms whether users can be under 18.

The skill I used only allows legal-gap findings to be marked `mandatory: true`. So the security findings are marked `mandatory: false`, even though they fall under the security duty in s.8(5) and Rules r.6.

**Questions for a lawyer:**
- Is the university "State" under Article 12? If so, s.17(4) would remove the erasure duties in s.8(7) and s.12(3).
- What is the lawful basis for each purpose (booking, analytics, newsletter)?
- Is the analytics vendor acting for the university or independently, and do any health-sector rules restrict sending this data to the US?
- Do the children's-data exemptions for clinics and universities cover booking but not analytics?
- What must be kept for one year under Rules r.8(3), and what must be erased?

This is an engineering assessment, not legal advice.