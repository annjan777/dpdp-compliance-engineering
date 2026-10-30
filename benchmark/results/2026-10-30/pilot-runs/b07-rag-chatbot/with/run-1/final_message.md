I wrote the assessment to `dpdp-submission.yaml`. I didn't change any application code.

**Applicability: `applicable`.** The app is a loan-helper chatbot for borrowers in India. It handles their name, PAN, phone number, income, chat messages and uploaded loan documents in digital form, so the Act covers it. The duties that matter here start on **13 May 2027**, so on today's date (31 Oct 2026) they apply but can't be enforced yet. The findings marked `mandatory: true` are things you'll be legally required to fix from that date, not things you're in breach of today. That date comes from secondary sources about the official commencement notice and should be checked against the notice itself.

**Main problems found (11 in total):**
1. **Critical – other borrowers' documents leak into answers** (`bot/store.py:9-13`, `bot/service.py:16-17`). Uploaded documents all go into one shared store with no owner attached. Every chat pulls from that store, so one borrower's documents end up in another borrower's prompt and answer. This counts as a personal data breach and is a security failure.
2. **High – deleting an account leaves most data behind** (`bot/service.py:20-21`). Only the user record is removed. Chat history and uploaded documents stay, and the LLM provider is never told to delete anything.
3. **High – too much personal data sent to the AI provider** (`bot/service.py:7-10`). Every prompt includes name, PAN, phone and income, whatever the question is. The provider is hosted in the US, and there's no sign of a contract with it or of where the data goes (`bot/llm.py:1`).
4. **Medium:**
   - Users are never shown a notice or asked for consent, and no lawful basis is recorded.
   - Chat history is stored unencrypted and kept forever.
   - Nothing logs who reads personal data, so a breach couldn't be detected or investigated.
   - Apart from deleting their account, users can't see a summary of their data, correct it or complain, and no contact person is published.
   - Uploaded document text goes straight into the prompt next to the borrower's personal details, so a crafted document could get the AI to reveal them.

**Questions for a lawyer (also in the file):**
- Who is the data controller under the Act (the "Data Fiduciary"): the lender or the chatbot operator?
- What is the legal basis for each use of the data: consent, or the user volunteering it?
- Do RBI rules or other banking rules limit sending PAN and income data to a US provider?
- After an account is deleted, which data must still be kept (the Rules require one year of logs, plus lending and KYC record rules) and which must be erased?
- Can people under 18 use the app?

This is an engineering assessment, not legal advice.