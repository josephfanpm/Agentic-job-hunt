# Instructions for Claude

Read [AGENTS.md](AGENTS.md) first; it is the shared contract with the other agent.

- The user's facts live in `private/profile.md`: resume, wins, metrics, targets, pay floor, work authorization and sheet ID. Use nothing that isn't there or in their own files.
- Each task has a matching file in `prompts/`. Follow it.
- Use the Google Sheets connector for every sheet change. Build batch requests with the scripts in `scripts/`.
- Compile resumes with Tectonic, then run `python scripts/check_pdf.py <file>.pdf` before calling a resume done.
- Write in plain language. A recruiter outside the user's company must understand every bullet and message.
