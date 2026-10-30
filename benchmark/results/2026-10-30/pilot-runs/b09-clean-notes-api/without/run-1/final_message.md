I wrote the assessment to `dpdp-submission.yaml` and didn't change any application code.

**Does the Act apply? Yes, fully.** This is a consumer note-taking backend for users in India. It handles personal data in digital form: email addresses, password hashes, note content and consent records. That makes the operator a Data Fiduciary under the Act (s.2(i), s.2(t), s.3(a), s.4(1)).

**What the code already does well:**
- Passwords are hashed with bcrypt (cost 12).
- A user can only read their own notes, so one user can't fetch another's.
- Product-update emails are off unless the user opts in, and each consent is recorded with the version of the privacy notice.
- Logs record only the user ID, not the email or other personal details.
- Deleting an account removes the user, their notes and their sessions.

**Findings (6):**
1. **Medium, legal gap, mandatory:** The only way to withdraw consent to product-update emails is to delete the whole account. The Act requires withdrawing consent to be as easy as giving it (s.6(4), r.3(c)).
2. **Medium, security:** Signup doesn't check its input. If no password is sent, the code hashes the literal text "undefined" as the password. Missing or duplicate emails are also accepted.
3. **Low, security:** Session tokens never expire and are never replaced.
4. **Medium, legal gap:** There's no age check or parental consent flow (s.9, r.10). I marked this not mandatory for now, because it only applies if children can actually sign up. That's flagged as a question for a lawyer.
5. **Low, operational:** Logs only go to the console. There's no record of failed logins or note access and no log retention, though r.6 expects logs that can detect unauthorised access, kept for a year.
6. **Low, best practice:** There's no rate limiting.

**Questions for a lawyer:**
- Can children use the app, and if so, what parental consent is needed?
- Is the core service run on consent or on a "legitimate use" basis, and does notice-v3 meet the notice requirements?
- How long can consent records and erasure logs be kept after an account is deleted?
- How are access, correction and complaint requests, and breach notifications, handled outside this code?