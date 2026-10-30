I've written `dpdp-submission.yaml`; it parses as valid YAML. I didn't change any application code.

**Does the Act apply? Yes (`applicable`).** This is a consumer notes API for users in India. It handles digital personal data (email, password hash, note contents, session tokens), and the operator decides why and how that data is used, which makes it the "Data Fiduciary" (the party the Act's duties fall on). That puts it in scope under Act s.3(a)/(b) and s.2(t). No exclusion or exemption fits. The main duties don't take effect until **13 May 2027** (G.S.R. 843(E)), so these gaps should be fixed before then.

**What the code already does well:**
- Users can only read their own notes.
- Passwords are hashed with bcrypt.
- Product-update emails are opt-in, and each consent is stored with the notice version and a timestamp.
- Logs record only user IDs, not emails or note text.
- Deleting an account removes the user's notes and sessions.

**Findings (4):**
1. **Medium, mandatory:** users can't withdraw product-update consent except by deleting their whole account (`src/app.js:19`). The Act requires withdrawal to be as easy as giving consent (s.6(4), s.6(6)).
2. **Low:** after an account is deleted, the consent records and processing log keep the user's ID with no expiry date. Rules r.8(3) requires keeping them at least one year, then erasing them unless another law says otherwise (`src/db.js:14-20`).
3. **Low, security:** signup doesn't check its input. It accepts any email format and duplicate emails, and a missing password gets hashed as the literal string `"undefined"`. There's also no rate limiting (`src/app.js:16-22`).
4. **Low, best practice:** there's no self-service way for users to see a summary of their data or correct it. This may be handled outside this code.

**Questions for a lawyer:**
- Can under-18s sign up? If so, verifiable parental consent rules apply, and the signup flow has no age handling.
- Is the account and notes processing based on consent or on the user voluntarily providing the data (s.7(a))? Does "notice-v3" contain everything the notice rules (s.5, Rules r.3) require?
- Which consent and deletion records must be kept as proof, and for how long?
- Is the email provider (not in this repo) bound by a proper processor contract, and does a withdrawal reach it?

This is an engineering assessment, not legal advice.