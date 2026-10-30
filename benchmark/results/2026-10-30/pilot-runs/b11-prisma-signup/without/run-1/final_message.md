I wrote the assessment to `dpdp-submission.yaml` and didn't change any application code. The repo is small: a README, the Prisma schema and `src/signup.ts`.

**Does the Act apply?** Yes, the status is `applicable`. The app is a fitness-class booking service for adults in India. It collects name, email, phone, Aadhaar number and booking history through a web signup, so it handles digital personal data inside India (Act s.3(a)). None of the exemptions fit. The business decides why and how the data is used, so it is the "Data Fiduciary" (the party responsible under the Act).

The obligations aren't in force yet, though. As I understand the November 2025 notification, the main duties (Act ss.3–17 and Rules r.3–r.16) start about 18 months later, around 13 May 2027. I've marked the findings mandatory because they will apply to this app from then. Please check that date with your lawyer; it's the first of the legal questions in the file.

**Main findings (13 in total):**
- **High:**
  - The Aadhaar number isn't needed to book gym classes, so collecting it breaks the rule to collect only what the purpose needs (s.6(1), s.4).
  - The Aadhaar number is stored in plaintext (s.8(5), r.6(1)(a)).
  - `marketingOptIn` defaults to `true`, so every new user is added to the marketing list without actively agreeing (s.6(1)).
  - Users get no notice at collection, and no record of consent is kept (s.5, r.3, s.6(10)).
- **Medium:**
  - Users can't withdraw marketing consent or unsubscribe (s.6(4)).
  - Signup copies the incoming request fields straight into the database without checking them. Someone could set `marketingOptIn` or other fields themselves.
  - Users can't see, correct or delete their data, and there's no complaint process (ss.11–13, s.8(10)).
  - There's no limit on how long data is kept and nothing erases it (s.8(7)).
  - Nothing controls or logs who reads or exports personal data (r.6).
- **Low:**
  - There's no contract or safeguard for whoever sends the marketing emails.
  - Nothing can detect a data breach or notify users and the regulator (s.8(6), r.7).
  - Nothing checks that users are adults (s.9, best practice).

**Questions for a lawyer:**
- Can a private gym business lawfully collect Aadhaar numbers at all under the Aadhaar Act and UIDAI rules?
- When do these obligations start, and what does that mean for the remediation timeline?
- Can booking messages rely on "legitimate use" (s.7(a)) while promotional emails need separate consent?
- Could the business ever be designated a "Significant Data Fiduciary", which carries extra duties?