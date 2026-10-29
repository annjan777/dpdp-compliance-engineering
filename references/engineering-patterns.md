# Engineering patterns (Phases D–E)

Patterns, not templates. Fit them to the project's existing architecture, language and libraries. For each one, first check whether the project already has something equivalent and extend that.

Each pattern lists the requirement IDs it serves, the minimum viable version, and what **not** to build.

---

## 1. Processing register (DPDP-LAW-01, LAW-02)

**Minimum:** a version-controlled file (`.dpdp/config.yaml` → `processing_activities`, or a constants module) listing each purpose with:
- its lawful ground (`consent` or `s.7(a)`…`s.7(i)`);
- data categories;
- retention rule;
- processors.

Code that processes data for a purpose references the purpose ID, so the mapping can be tested.

**Don't:** build a register UI no one asked for, or claim a legitimate use without the clause's conditions.

## 2. Notice registry and versioning (DPDP-NOT-01–03, CON-04)

**Minimum:**
- Notice content stored as versioned entries (`notice_id`, `version`, `language`, `items[]`, `purposes[]`, links to withdraw, rights and Board complaint), rendered at the point of the consent action.
- The consent record stores the notice version shown.
- The content itself is legal text. Implement the mechanism with clearly marked placeholder text, and set `approvals_required: [legal]` for the wording.

**Don't:** show a notice for purposes that rely on s.7 grounds as if consent were being asked. Don't block the core service on optional consent.

## 3. Consent ledger and purpose gates (DPDP-CON-01, CON-03, CON-04)

**Minimum:**
- An append-only table or collection: `subject_ref`, `purpose_id`, `notice_version`, `status` (granted/withdrawn), `timestamp`, `channel`.
- Current state = latest event per (subject, purpose).
- Defaults are **not granted**.
- A single function `has_consent(subject, purpose)` checked **at the time of use** (send marketing email, emit analytics), not only at signup.
- `withdraw(subject, purpose)` records the event, then triggers downstream stop and erase hooks for processors tied to that purpose.

**Don't:**
- Store consent as one boolean on the user row that gets overwritten. That loses the s.6(10) proof.
- Make core service access conditional on optional consents. That breaks "free" and "unconditional".

## 4. Data Principal requests (DPDP-RGT-01–04, GRV-01–02)

**Minimum:**
- **Request intake:** an authenticated endpoint or form plus an out-of-band channel. Store type, subject, received time and due date.
- **Identity verification:** use the existing login. Never ask for extra identity documents unless they're really needed.
- **Access summary (s.11):** data categories held, purposes, processing activities, and recipients (other fiduciaries and processors). This is a summary, not a full dump.
- **Correction (s.12(2)):** route through the existing edit paths so validation and audit apply.
- **Erasure (s.12(3)):** reuse the erasure cascade (pattern 5). Record the reason when refusing (purpose still active, legal retention).
- **Grievance:** due date = received + configured period, where the period is at most 90 days. Responses include the contact (r.9).
- **Nomination:** store nominee contact and relationship, and define a verification procedure for when a nominee acts.

**Don't:** build a portability or export feature and call it a DPDP requirement. If useful, add it as `best-practice`.

## 5. Erasure and retention (DPDP-RET-01, RET-02, SEC-05)

**Minimum:**
- A retention schedule per data category: the period or event, the legal basis for keeping it, and the purge action.
- **Erasure cascade:** primary rows, child rows, derived data, file and object storage, caches, search and vector indexes, analytics or CRM processors (API delete calls or tickets), plus an erasure record that holds no personal data.
- **Backups:** don't edit them. Document the expiry window and make sure restores re-apply erasures (an erasure tombstone list replayed after restore).
- **Rules r.8(3) one-year minimum:** keep processing logs and associated traffic data for at least one year from processing, even after account erasure. Put them in a restricted store and purge after the period. Exactly which fields must survive is a legal question. Implement the mechanism, and get the field list approved.
- **Identifiers are never reused.** Retained records (logs, ledgers, legally held data) stay keyed by the erased person's ID. If the database can reuse IDs (e.g. SQLite `INTEGER PRIMARY KEY` without `AUTOINCREMENT`, or recycled sequences), a new user can inherit them. Close open consents on erasure rather than deleting the ledger.
- **Processor erasure calls use an identifier the processor actually holds.** Check what the vendor received. If it got no identifiers, per-user erasure is impossible, so raise a one-off deletion request for historical data instead of sending a new identifier abroad.
- **Erasure is an authorised action.** Only the account holder, or an audited admin path, can trigger it. Log the real actor.
- **RET-02:** only for Sch.3 classes. Needs last-activity tracking, a 48-hour advance notice job, and cancel-on-login.

**Don't:**
- Hard-delete the audit or consent history needed to prove compliance.
- Treat a soft delete (`deleted_at`) as erasure.
- Run purge jobs against production from this skill.

## 6. Security safeguards (DPDP-SEC-01–04, SEC-06)

**Minimum, prioritised by exposure:**
1. **Object-level authorisation on every personal-data read and write.** The most common real breach path.
2. **Secrets out of code.** Use the environment or a secret manager. Rotate anything committed.
3. **TLS everywhere.** At-rest encryption via the platform (DB, disk, bucket). Field-level encryption or tokenisation only where risk justifies it, such as health, financial and identity numbers. Key management is a `security` approval item.
4. **Password hashing** with bcrypt, scrypt or argon2.
5. **Audit events** for personal-data access by admins and services: who, what record ID, when, and why. Don't copy the data into the event.
6. **Backups** enabled, encrypted, with a restore tested and recorded.
7. **Vendor contracts** include security clauses (legal item).

**Don't:**
- Add encryption without a key-management plan.
- Weaken existing controls.
- Log full request bodies.

## 7. Privacy-aware logging and telemetry (DPDP-SEC-03, CON-01, CHD-02)

**Minimum:**
- Central redaction at the logger level (formatter or filter) for known personal fields and patterns.
- Log stable internal IDs instead of emails or phones.
- Analytics events carry an event name plus a pseudonymous ID. They're gated by `has_consent(subject, analytics)` where consent is the ground, and disabled for child accounts unless an Sch.4 exemption applies.
- Error trackers have PII scrubbing turned on and send no request bodies by default.

## 8. Breach detection and escalation (DPDP-BRE-01–02)

**Minimum:**
- An incident record with `aware_at` (the clock starts here), `board_initial_sent_at`, `board_detailed_due_at = aware_at + 72h`, affected-subject query, and notification status.
- Templates covering every Rules r.7(1) and r.7(2) item.
- Alert sources wired to on-call: auth anomalies, mass exports, access-denied spikes, data store exposure.
- A named owner role in config.

**Don't:** auto-send Board or user notifications from code without human approval.

## 9. Processor controls (DPDP-FID-01, SEC-06, XB-01)

**Minimum:**
- A vendor register (in config) with: role, purpose, data categories, region, contract reference, and an erasure method.
- Outbound calls carrying personal data go through a small allow-listed client, or are at least covered by a test checking that destinations are registered.
- Minimise payloads to what the vendor needs.

## 10. Children (DPDP-CHD-01–03)

**Minimum:**
- Decide whether minors are possible (a legal or management question, not a code guess).
- If yes: an age signal at onboarding; a verified-parent path per Rules r.10 using existing verified accounts or an authorised-entity token; tracking, ads and behavioural analytics off for child accounts.
- Document any Sch.4 exemption relied on, together with its limiting condition.

**Don't:**
- Collect full date of birth when a simple age-band answer is enough.
- Build Aadhaar or ID-document capture without legal sign-off.

## 11. AI and LLM features

**Minimum:**
- **Prompt minimisation:** strip or replace identifiers before sending text to external model providers when the task doesn't need them.
- **Provider settings:** where the provider supports it and the code controls it, disable training on submitted data and set retention. Otherwise record it as a vendor contract item.
- **Conversation history** has a retention period and is included in the erasure cascade.
- **Vector stores** keep `subject_ref` or `source_doc_id` metadata so vectors can be deleted per user or document.
- **Model outputs** used for decisions about people need a correction path (s.8(3)).

## Anti-patterns to reject

- A consent banner added in place of a lawful-ground analysis.
- Consent requested for processing that relies on s.7.
- A "DPDP compliant" badge or claim.
- Collecting identity documents "for verification" with no requirement for them.
- A second audit or consent system next to an existing one.
- Copying personal data into compliance logs or reports.
- Turning off security checks to make tests green.
