# Legal sources and citation registry

This file is the skill's authoritative legal starting point. Cite **only** what is listed here, in the citation format shown. `validate_assessment.py` rejects citations outside these patterns.

If a question is not answered here, don't fill the gap from memory, from the GDPR, or from commentary. Record a `legal_questions` entry instead.

> Engineering reference, not legal advice. Summaries below are paraphrases. Before relying on a provision for a consequential decision, read the official text (links at the end).

## Citation format

| Source | Format | Valid range |
|---|---|---|
| Digital Personal Data Protection Act, 2023 (No. 22 of 2023) | `Act s.8(5)`, `Act s.7(i)`, `Act s.17(1)(d)` | sections 1–44 |
| Act's penalty Schedule | `Act Sch. item 1` | items 1–7 |
| Digital Personal Data Protection Rules, 2025 (G.S.R. 846(E), 13 Nov 2025, as corrected by G.S.R. 892(E)) | `Rules r.7(2)`, `Rules r.8(3)` | rules 1–23 |
| Rules' Schedules | `Rules Sch.3`, `Rules Sch.4 Part A item 3` | Schedules 1–7 |
| Commencement notification | `G.S.R. 843(E)` | — |
| Board establishment | `G.S.R. 844(E)`, `G.S.R. 845(E)` | — |

Requirement IDs (`DPDP-SEC-01` etc.) come from `requirements-catalog.yaml`. Each catalog entry carries its own citations.

G.S.R. 892(E) (10 Dec 2025) corrects only typographical errors in the Rules (cross-references, punctuation, "of this Gazette" → "in the Official Gazette"). It changes no obligation.

## Commencement (verify before each assessment)

All dates run from the Gazette publication of 13 Nov 2025.

| Date | Rules in force | Act provisions in force (G.S.R. 843(E)) | Engineering meaning |
|---|---|---|---|
| 13 Nov 2025 | r.1, 2, 17–21 | s.1(2), 2, 18–26, 35, 38–43, 44(1), 44(3) | Board, definitions, RTI amendment. No fiduciary duties yet. |
| 13 Nov 2026 | r.4 (Consent Manager registration) | s.6(9), 27(1)(d) | Consent Managers can register. |
| 13 May 2027 | r.3, 5–16, 22, 23 | All remaining provisions, including s.3–17 (scope, duties, rights, exemptions), 27–34, 36, 37, 44(2) (IT Act s.43A omitted) | Substantive obligations apply. |

The Act-section split above is as reported from G.S.R. 843(E) by multiple secondary sources. Confirm against the gazette before relying on a specific section's date.

**Rule for assessments:** set `in_force` per requirement by comparing its catalog `commencement` with `project.assessment_date`. "Applicable but not yet in force" is a normal and important result. It means "build now, the deadline is fixed".

## The Act — provisions that drive engineering work

| Cite | Gist (paraphrase) | Typical engineering consequence |
|---|---|---|
| Act s.2(t) | Personal data = data about an individual identifiable by or in relation to that data. | Includes indirect identifiers (user IDs, emails, device IDs, IPs, chat text), not only "sensitive" fields. |
| Act s.2(i), s.2(k) | Fiduciary determines purpose and means. Processor processes on a fiduciary's behalf. | Role decides who owes which duties. |
| Act s.2(f), s.2(j) | Child = under 18. Data Principal includes parent or lawful guardian. | Age matters for s.9. |
| Act s.2(u) | Personal data breach covers unauthorised processing and accidental disclosure, alteration, destruction or loss of access affecting confidentiality, integrity or availability. | Outages that lose data count, not just leaks. |
| Act s.3(a) | Applies to digital personal data processed in India, whether collected digitally or digitised later. | Paper never digitised is outside. |
| Act s.3(b) | Applies outside India if processing is connected to offering goods or services to Data Principals in India. | Foreign SaaS serving Indian users is in scope. |
| Act s.3(c)(i) | Excludes processing by an individual for personal or domestic purposes. | Personal tools can be outside scope. |
| Act s.3(c)(ii) | Excludes data made public by the Data Principal herself, or by someone legally obliged to publish it. | Narrow. Scraped or third-party-published data is not automatically excluded. |
| Act s.4 | Process only for a lawful purpose with consent, or for a legitimate use under s.7. | Every purpose needs a recorded ground. |
| Act s.5(1), s.5(3); Rules r.3 | Notice before or with a consent request: itemised data, specific purposes, how to withdraw, exercise rights and complain to the Board. Standalone, clear and plain, with an option to view it in English or an Eighth Schedule language. | Versioned notice shown at the point of consent. |
| Act s.5(2) | For consents obtained before commencement, give notice as soon as reasonably practicable. Processing may continue until withdrawal. | Legacy-user notice campaign. |
| Act s.6(1) | Consent must be free, specific, informed, unconditional and unambiguous, by clear affirmative action, and limited to data necessary for the purpose. | No pre-ticked boxes, no bundled unrelated purposes. |
| Act s.6(2) | Parts of a consent that infringe the law are invalid. | No waiver clauses. |
| Act s.6(3) | Consent request in clear language, with language option, and contact details of the DPO or authorised person. | Contact shown at consent. |
| Act s.6(4), s.6(5) | Withdrawal anytime, as easy as giving consent. Prior processing stays lawful. The Data Principal bears the consequences of withdrawing. | One-click withdrawal where consent was one click. |
| Act s.6(6) | After withdrawal, stop processing within reasonable time and make processors stop, unless law requires or authorises otherwise. | Withdrawal propagates to vendors. |
| Act s.6(7)–(9); Rules r.4, Sch.1 | Consent Managers: registered with the Board. | Only if integrating with, or acting as, a Consent Manager. |
| Act s.6(10) | In proceedings, the fiduciary must prove notice and consent. | Consent ledger with notice version and timestamp. |
| Act s.7 | Legitimate uses without consent: (a) voluntarily provided for a specified purpose with no objection; (b) State subsidies, benefits, services, certificates, licences, permits (Rules r.5, Sch.2); (c) State functions, sovereignty, security; (d) legal disclosure duty to State; (e) court orders and judgments; (f) medical emergency; (g) epidemic or public-health threat; (h) disaster or public order; (i) employment and safeguarding the employer. | Map each purpose to a specific clause, with its conditions met. |
| Act s.8(1) | Fiduciary is responsible, including for its processors, whatever any agreement says. | Liability can't be contracted away. |
| Act s.8(2) | Processors only under a valid contract. | Vendor contracts and DPAs. |
| Act s.8(3) | Ensure completeness, accuracy and consistency when data is used for a decision affecting the person or disclosed to another fiduciary. | Conditional, not universal. |
| Act s.8(4) | Appropriate technical and organisational measures. | — |
| Act s.8(5); Rules r.6 | Reasonable security safeguards to prevent breach (r.6(1)(a)–(g) minimums). | Encryption, masking or tokenisation; access control; logging and monitoring; continuity and backups; one-year log retention; processor contract clauses; organisational measures. |
| Act s.8(6); Rules r.7 | Intimate breach to the Board and each affected Data Principal. Board detailed report within 72 hours (extendable on request). | Incident pipeline and notification templates. |
| Act s.8(7) | Erase on withdrawal or when the purpose is no longer served (whichever is earlier), unless law requires retention. Make processors erase. | Erasure workflow with downstream propagation. |
| Act s.8(8), s.8(11); Rules r.8(1)–(2), Sch.3 | Purpose deemed over after a prescribed inactivity period. Rules prescribe it only for Sch.3 classes: e-commerce entities ≥2 crore users, online gaming intermediaries ≥50 lakh, social media intermediaries ≥2 crore. 3 years, with 48-hour advance notice. | Inactivity purge only for those classes. Others assess "purpose served" case by case. |
| Rules r.8(3), Sch.7 | Retain personal data, associated traffic data and processing logs for at least one year from processing, for Sch.7 purposes, then erase unless law requires otherwise. Applies even after account deletion. | Restricted retention store. Erasure must not destroy these within one year. |
| Act s.8(9); Rules r.9 | Publish business contact of the DPO or a person who answers processing questions, prominently on the website or app and in every rights response. | Contact in footer, settings and response templates. |
| Act s.8(10), s.13; Rules r.14(3) | Effective grievance mechanism. Respond within the published period, not exceeding 90 days. Data Principal must exhaust it before going to the Board. | Ticketing with due dates. |
| Act s.9(1); Rules r.10 | Verifiable parental consent before processing a child's data. Due diligence that the parent is an identifiable adult, via data already held or a token from an authorised entity (e.g. DigiLocker). | Age-aware onboarding. |
| Act s.9(1); Rules r.11 | Person with disability with a lawful guardian: verify the guardian's appointment by court, designated authority or local-level committee. | Guardian verification workflow. |
| Act s.9(2) | No processing likely to harm a child's well-being. | Design review. |
| Act s.9(3) | No tracking, behavioural monitoring or targeted advertising directed at children. | Disable analytics and ads profiling for minors. |
| Act s.9(4); Rules r.12, Sch.4 | Exemptions from s.9(1) and s.9(3). Part A classes: clinical establishments, health professionals, educational institutions, creches, their transport providers. Part B purposes include email account creation, safety location tracking, blocking harmful content, and verifying a user is not a child. Each is limited to stated purposes. | Exemption must match class or purpose **and** its limiting condition. |
| Act s.10; Rules r.13 | Significant Data Fiduciary: only if notified by the Central Government. DPO in India, independent auditor, annual DPIA and audit, algorithmic due diligence, localisation of data a government committee specifies. | Not applicable unless there's evidence of notification. |
| Act s.11 | Right to a summary of data and processing, and identities of fiduciaries and processors it was shared with. Only for processing based on consent, including s.7(a). | Access summary endpoint. Not for other legitimate uses. |
| Act s.12 | Correction, completion, updating. Erasure on request unless retention is needed for the purpose or by law. Same consent / s.7(a) scope. | Correction and erasure requests. |
| Act s.14; Rules r.14(4) | Nominate one or more persons for death or incapacity. | Nominee records. |
| Rules r.14(1)–(2), (5) | Publish how to exercise rights and which identifiers are needed. | Rights page. |
| Act s.15 | Duties of Data Principals (no impersonation, no false complaints). Penalty up to ₹10,000. | Not an engineering duty. |
| Act s.16; Rules r.15 | Cross-border transfer allowed except to notified countries, and subject to any Central Government orders on making data available to foreign States. Stricter sectoral laws still apply (s.16(2)). | Record destinations. Check notifications and sectoral rules. |
| Act s.17(1) | Chapter II (except s.8(1), s.8(5)), Chapter III and s.16 don't apply to: (a) enforcing legal claims; (b) courts and regulators; (c) offence prevention and investigation; (d) data of non-India principals processed under a contract with a foreign person; (e) court-approved mergers; (f) loan-default asset checks. | Partial only. Security (s.8(5)) still applies. |
| Act s.17(2)(a) | Notified State instrumentalities for security purposes. | Requires a notification. |
| Act s.17(2)(b); Rules r.16, Sch.2 | Research, archiving or statistics: Act does not apply if no decision specific to a Data Principal is taken **and** Sch.2 standards are followed. | Exemption has conditions to evidence. |
| Act s.17(3) | Government may notify fiduciaries or classes (including startups) exempt from s.5, s.8(3), s.8(7), s.10, s.11. | Only with notification evidence. |
| Act s.17(4) | For the State or its instrumentalities: s.8(7) and s.12(3) don't apply. s.12(2) doesn't apply where no decision affects the principal. | Public bodies: legal review on "State" status (Constitution Art. 12). |
| Act s.17(5) | Government may exempt any fiduciary from any provision within 5 years of commencement. | Only with notification evidence. |
| Act s.33, Act Sch. | Penalty maxima: item 1 security safeguards ₹250 cr; item 2 breach notice ₹200 cr; item 3 children ₹200 cr; item 4 SDF ₹150 cr; item 5 Data Principal duties ₹10,000; item 6 voluntary undertaking (as original breach); item 7 any other ₹50 cr. | Input to severity, not a severity by itself. |
| Act s.36; Rules r.23, Sch.7 | Government can call for information. Non-disclosure of the request can be directed. | Runbook for government requests. |
| Act s.37 | Blocking after penalties in two or more instances. | Risk context only. |
| Act s.44(2) | IT Act s.43A (compensation for negligent handling of sensitive data) omitted. | Context: older IT Act SPDI rules fall away when this commences. |

## What the Act and Rules do **not** say (common over-reach)

Don't create obligations that aren't there:

- **No separate "sensitive personal data" tier.** All personal data is treated alike. Sensitivity affects risk and severity, not the legal category.
- **No right to data portability or export.** s.11 gives a *summary*, not a machine-readable export. Export can still be a sensible best practice, but tag it `mandatory: false`.
- **No general data-localisation requirement.** Only notified SDFs (Rules r.13(4)) and stricter sectoral laws (s.16(2)) restrict location.
- **No mandatory DPO for ordinary fiduciaries.** Only SDFs must appoint one. Everyone else must publish a contact who can answer questions (s.8(9)).
- **No "legitimate interests" or "contract necessity" ground.** The only grounds are consent and the s.7 list.
- **No general cookie-banner rule.** Consent is needed only where consent is the ground for that processing.
- **No requirement to consent for every processing.** s.7 uses need none.
- **No inactivity-based deletion for everyone.** The three-year rule applies only to Rules Sch.3 classes.
- **No breach deadline to Data Principals** beyond "without delay" (Rules r.7(1)). The 72-hour clock is for the Board's detailed report (r.7(2)(b)).
- **No individual compensation route** under the Act. Penalties go to the Consolidated Fund (s.34).
- **Access, correction and erasure rights (s.11–12) don't attach to processing on s.7(b)–(i) grounds.**

## Open interpretive questions (always route to legal review)

- Whether pseudonymised or hashed identifiers are still "personal data" for a given fiduciary (s.2(t)).
- Whether an organisation is "State" or an instrumentality under Article 12 (s.17(4), s.7(b)–(c)).
- The precise scope of "offering goods or services to Data Principals within India" for foreign processing (s.3(b)).
- Whether a vendor is a processor or an independent fiduciary (s.2(i), s.2(k)).
- How far s.7(a) "voluntarily provided" stretches before consent is needed.
- What exactly must be retained under Rules r.8(3) versus erased under s.8(7), for each data category.
- Whether the s.5(3) language option means all 22 Eighth Schedule languages or a chosen subset.
- How strong age assurance must be before s.9 obligations attach to a given service.
- Whether Rules Sch.4 exemptions cover a given processing activity and its limiting condition.

## Official texts

- Act (Gazette, 11 Aug 2023): https://www.meity.gov.in/static/uploads/2024/06/2bf1f0e9f04e6fb4f8fef35e82c42aa5.pdf
- Rules, 2025 (G.S.R. 846(E), 13 Nov 2025): https://www.meity.gov.in/static/uploads/2025/11/53450e6e5dc0bfa85ebd78686cadad39.pdf
- Corrigendum G.S.R. 892(E) (10 Dec 2025): https://www.meity.gov.in/static/uploads/2025/12/3c7ebbae0e5456f493f486e6845df86b.pdf

Registry last reviewed: 2026-10-29. If the assessment date is well past this, or a new notification exists (SDF designation, s.16 restriction list, s.17(3) or s.17(5) exemptions, amended Rules), record a legal question and update this file before relying on it.
