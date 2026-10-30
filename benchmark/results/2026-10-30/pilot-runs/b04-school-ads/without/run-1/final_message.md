I wrote `dpdp-submission.yaml` to the current directory and didn't change any application code. The file parses as valid YAML and contains 12 findings. The non-zero exit code on the check comes from the sandbox's read-only temp directory, not from the file.

**Does the Act apply?** Yes. A government school in Odisha is the data fiduciary, and the app handles digital personal data of children in classes 1–10 and their parents' mobile numbers (Act s.3(a)). Marking attendance and texting parents about absences is probably allowed without consent: it likely counts as a legitimate use by the State (s.7), or falls under the Rules' exemption for educational institutions (r.12). That exemption doesn't cover advertising.

**Most serious problems:**
- **Critical:** `school/app.py:19` sends each pupil's ID, class, date of birth, topic and time on page to an ad network hosted outside India. That is tracking and behavioural monitoring of children, which s.9(3) prohibits.
- **Critical:** `school/app.py:20` picks ads using the pupil's interests and age. That is targeted advertising at children, also prohibited by s.9(3).
- **High:**
  - There is no notice or verifiable parental consent for any processing beyond attendance (s.9(1), r.10).
  - Attendance data is reused for ads, and the full date of birth is sent where it isn't needed (s.4, s.6).
  - The database is a plain SQLite file with no encryption, access control or logging (s.8(5), r.6).
- **Medium:**
  - There's no process to detect or report data breaches (s.8(6), r.7).
  - Records are never deleted, even after a pupil leaves (s.8(7)).
  - Parents have no way to see, correct or delete data, or to complain (ss.11–14, r.14).
  - The ad SDK keeps every tracked event indefinitely.
  - Children's data is sent abroad with no contract or safeguards. No country is currently restricted under s.16, so I marked this best practice rather than mandatory.
- **Low:** The SMS gateway has no data processing contract, and parents' mobile numbers aren't checked for accuracy.

**Timing:** Most of the obligations come into force around 13 May 2027. I marked them mandatory because they will apply to this app, and listed the start dates as a question for a lawyer.

**Questions for a lawyer:**
- Has the government notified this school or Odisha's education department as exempt under s.17(2)(a)?
- Does the educational-institution exemption under r.12 fully cover the attendance SMS?
- Is the ad network a processor acting for the school, or a separate data fiduciary?
- Could any sponsored content on the pupils' learning page be lawful at all?