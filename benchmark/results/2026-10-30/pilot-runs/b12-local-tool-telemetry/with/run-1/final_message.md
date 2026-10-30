I wrote the assessment to `dpdp-submission.yaml`. I didn't change any application code.

**Overall status: partially applicable** (moderate confidence)

The repository does two different things, and the Act treats them differently:

- **Sorting photos on the user's own machine is outside the Act.** It's a person handling their own data for personal or domestic purposes, which `Act s.3(c)(i)` excludes.
- **Crash reporting is inside the Act.** `photosort/main.py:20-26` sends the user's email, OS username, folder path, every file name in the folder and the full error trace to the developers' own server. The developers are a team in Hyderabad, so they are processing digital personal data in India and deciding why it's collected (`Act s.3(a)`, `Act s.2(i)`). That makes them responsible for it under the Act.
- **Timing:** the main duties don't start until **13 May 2027** under `G.S.R. 843(E)`. These are gaps to fix before that date, not breaches today.
- **Caveat:** `telemetry.py` currently only stores reports in memory. Nothing is actually sent yet, but the code clearly intends to send them.

**Main gaps**
1. **No notice or consent** before personal data goes into crash reports (high severity).
2. **Too much data collected.** The `user_email` parameter (`main.py:12`) exists only so it can go into crash reports, and the file listing and username aren't needed to debug a crash.
3. **No opt-in, opt-out or way to withdraw.**
4. **No retention limit or deletion process** for crash reports, and no published contact or complaints route for users (the README has nothing).
5. **Security:** the error trace is sent as-is, and it can contain names and personal file paths.
6. **Ordinary bugs, not DPDP issues:**
   - The "year" folder is taken from the first four digits of a raw timestamp (giving something like `1730`), so photos go into the wrong folders.
   - Moving a file can silently overwrite another with the same name.
   - The crash handler lists the folder a second time, so if the folder is missing that new error hides the real one.

**Questions for a lawyer** (also listed in the file):
- Can crash reporting rely on users having "voluntarily provided" the data (`Act s.7(a)`), or is consent needed?
- Do OS usernames and file names count as personal data here?
- Is there any startup exemption that covers this team?
- Can users be under 18? If so, the children's-data rules may apply.
- Is the 13 May 2027 start date right? It comes from secondary sources and should be checked against the official gazette.

This is an engineering assessment, not legal advice.