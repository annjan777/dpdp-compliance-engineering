I wrote `dpdp-submission.yaml` and checked that it parses: it has 8 findings. The command reported exit code 1, but that came from a read-only file error in the shell wrapper, not from the check, which printed the expected result. I didn't change any application code.

**Applicability: partially applicable**
- **The photo sorting itself is outside the Act.** It runs only on the user's machine and sorts their own photos. That is personal or domestic use, which the Act excludes (Act s.3(c)(i)).
- **The crash reporting is inside the Act.** When the sort fails, `photosort/main.py:20-26` builds a report for the developers' own server containing:
  - the user's email address
  - their computer login name
  - the folder path
  - the name of every file in the folder
  - the error trace

  That makes the two-person team in Hyderabad a "Data Fiduciary" (the party responsible for the data) under Act s.3(a), so the Act's duties apply to this part.

**Main findings**
1. **High:** The crash report collects personal data with no notice and no consent (Act s.4–6, Rules r.3).
2. **Medium:** It collects more than fixing a crash needs (Act s.6(1)). The email, login name and full file list aren't needed, and file names may also identify other people.
3. **Medium:** Users can't turn crash reporting off, withdraw consent or contact anyone with a complaint (Act s.6(4), s.8(10), s.13).
4. **Medium:** There is no limit on how long reports are kept and no way to delete them (Act s.8(7), Rules r.8).
5. **Medium:** There are no security safeguards (Act s.8(5), Rules r.6). Nothing is pseudonymised, and the error trace can include paths and usernames.
6. **Low, not legal requirements:**
   - `user_email` is passed into the sort function only so it can go into crash reports.
   - The crash handler lists the folder again, which can itself fail and hide the original error.
   - The year is taken as the first four digits of the file's raw timestamp, so files go into folders like "1700" instead of the real year.

**Questions for a lawyer**
- **Is anything actually sent?** `telemetry.py` currently only stores reports in a list in memory. Whether the duties above apply depends on whether released versions really send them to the server.
- **Who exactly is the fiduciary?** The two individuals or a company, and whether anyone else runs the crash server.
- **Does a startup exemption apply?** Check whether s.17(3) or later government notices reduce the obligations for a team this small.