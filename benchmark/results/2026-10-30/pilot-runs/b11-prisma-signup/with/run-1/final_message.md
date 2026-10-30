I wrote the assessment to `dpdp-submission.yaml` and didn't change any application code. This is an engineering assessment, not legal advice.

**Does the Act apply? Yes (`applicable`).** The app is a gym-class booking service for adults in India. It stores names, emails, phone numbers, Aadhaar numbers and booking history in a database, and sends marketing emails. That counts as digital personal data processed in India (Act s.3(a), s.2(t)). The gym operator appears to decide what the data is used for, which makes it the party responsible under the Act (the "Data Fiduciary"). I found no exclusion or exemption that covers it.

**When it takes effect:** Today is 2026-10-31. The main duties (Act s.4–17, Rules r.3 and r.5–16) start on **13 May 2027** (G.S.R. 843(E)). So the gaps below are obligations that already apply to this app but aren't enforceable until that date. I still marked them `mandatory: true`.

**Main problems:**
1. **Aadhaar numbers:** the app collects them for class booking, with no clear need. It stores them unencrypted alongside phone numbers and names, and `signup()` returns the whole user record, Aadhaar number included, to the caller (`schema.prisma:11`, `signup.ts:7`). Rated critical/high.
2. **Marketing consent is on by default:** `marketingOptIn` starts as `true`, and `marketingList()` emails everyone who has the flag. In effect, users who never agreed get marketing. That breaks the rule that consent must be free and given by a clear action (s.6(1)).
3. **Consent handling is missing:** users get no notice when they sign up, there is no record of when or how anyone consented, and there is no way to withdraw (s.5, s.6(4), s.6(10)).
4. **Raw input goes straight to the database:** signup passes `...input` into `create` without checking it, so a caller could set extra fields, including the marketing flag.
5. **No deletion or rights handling:** there is no way to correct or delete an account, no access logging and no breach process. No contact person or complaints channel is named anywhere in the repo.

**Questions for a lawyer** (all listed in the file):
- Is Aadhaar collection allowed at all here? This turns on the Aadhaar Act, not just DPDP.
- What is the legal basis for each use of the data, account data versus marketing?
- How should existing users whose opt-in was switched on by default be told and asked again for consent?
- Do the contracts with email and hosting vendors meet the Act's requirements for processors?
- Which data must be kept for a year under r.8(3), and which must be deleted?