# Instructions for Claude

Read [AGENTS.md](AGENTS.md) first. It is the shared contract with every other agent, and it lists the commands that replace work you would otherwise do yourself.

- Check `mode` in `private/config.json` and follow that mode's rules in [MODES.md](MODES.md). In lean mode, do nothing unprompted.
- The user's facts live in `private/profile.md`. Use nothing that isn't there or in their own files.
- Each task has a matching file in `prompts/`. Follow it.
- With a Google Sheet tracker, use the Sheets connector, and send the update files the scripts prepare without changing them.
- Compile resumes with Tectonic, then run `python -m jobhunt check <file>.pdf` before calling a resume done.
- Write in plain language. A recruiter outside the user's company must understand every bullet and message.
