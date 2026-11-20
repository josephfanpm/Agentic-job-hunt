# Set up the job search (for any AI agent)

Any agent that can run commands and edit files can follow this: Claude, Codex, Antigravity, Grok Build, Muse, Cline or another. The user may have pasted a message that points here. Work through the steps in order, and tell the user in one sentence what each step does before you do it.

## How to talk to the user

- **Ask first:** "Have you used a terminal or written code before?" If they say no, or aren't sure, treat them as non-technical for the whole setup:
  - Use everyday words. Say "the folder" or "the settings file", not "directory", "repo", "flags", "PATH" or "JSON".
  - Never ask them to type a command. Run it yourself.
  - Don't show command output unless something failed. Then say what went wrong and what you'll do, in one or two sentences.
  - When they need to click something in another app, give the exact buttons in order.
- **Ask one question at a time.** Give an example answer with each question. Tell them they can say "skip" or "not sure".
- **Never guess a fact about them.** If they skip something, leave it blank.

## 1. Get the tools ready

1. Check for Python 3.10 or newer (`python --version`, or `python3` on a Mac). If it's missing, install it: `winget install Python.Python.3.12` on Windows, `brew install python` on a Mac if Homebrew is there. If that fails, send the user to Step 1 of [START-HERE.md](../START-HERE.md) and wait.
2. If the project isn't in this folder yet, download it from https://github.com/josephfanpm/agentic-job-hunt. Use `git clone` if git is installed; otherwise download and unzip the ZIP. Work inside the project folder from then on.
3. Install the requirements: `python -m pip install -r requirements.txt`.
4. Read [AGENTS.md](../AGENTS.md) and [MODES.md](../MODES.md).

## 2. Ask the search questions, then run setup

Find the user's resume (a PDF, Word file or text file) in this folder or the folder above it. If you can't find one, ask where it is.

Ask these one at a time:

| Ask | Flag |
|---|---|
| Your name, and the city you live in | `--name`, `--city` |
| Job titles to search for | `--titles` |
| Words that rule a title out (for example: intern, director) | `--exclude` |
| Topics or industries you want more of | `--boost` |
| Countries you can work in | `--countries` (two-letter codes: US, CA, GB) |
| Are you open to remote jobs? | `--no-remote` if not |
| Lowest yearly pay you'd accept, and the pay you're aiming for | `--pay-floor`, `--pay-target` |
| Companies where someone could refer you | `--priority` |
| Other companies to watch | `--companies` |
| Track jobs in a Google Sheet or in files on this computer? Recommend the Google Sheet to anyone who isn't technical: they can tick jobs from their phone and get a morning email. Files opened in Excel can quietly change dates and break the format | `--tracker sheet` or `--tracker csv` |
| How much should the AI do: only what you ask (lean), a middle amount (standard), or as much as it can (full)? See [MODES.md](../MODES.md) | `--mode` |

Then run `python -m jobhunt init` with the answers as flags, plus `--resume <file>` and `--yes`. This creates the `private/` folder, which never leaves their computer.

## 3. Connect Google Sheets and Gmail

**If they chose the Google Sheet:**
1. Check whether you have a Google Sheets or Google Drive connector. If not, tell the user how to add one in your app. It's usually under Settings, then Connectors (some apps call them Apps, Integrations or MCP servers). Ask them to connect Google Drive or Google Sheets with their **personal** Google account, then wait.
2. Run [create-sheet.md](create-sheet.md).
3. Set up the receiver so the daily scan can write to the sheet without AI: walk the user through [sheet/README-apps-script.md](../sheet/README-apps-script.md). Do the config edits yourself, and give them each click inside Google.
4. Ask: "Do you want a morning email with the top new jobs? You can pick jobs straight from it." Recommend yes. If yes, set `"email_digest": true` in `private/config.json`, and warn them that Google will ask once to let the script send email as them.
5. If their app has no Google connector, say so and switch the tracker to files (`"tracker": "csv"` in `private/config.json`). They can import the files into Google Sheets any time.

**For everyone, ask:** "Do you want to connect Gmail? I'd save your messages to recruiters as drafts in your Gmail, and spot replies and interview invites so your tracker stays up to date. I never send anything." If yes, have them connect Gmail the same way, then confirm you can see their inbox. If no, or their app has no Gmail connector, skip it. Drafts then go in the tracker.

## 4. Build their experience bank

Run [profile-interview.md](profile-interview.md). This is the most important step. It collects every job, project, result and company detail, so each resume can be written for each job instead of reusing one resume.

Tell the user it takes 20–40 minutes, and that they can stop and pick it up later. If they want to start searching first, do steps 5 and 6, then come back to it.

## 5. Check and run the first scan

1. Run `python -m jobhunt doctor` and fix what it reports.
2. Run `python -m jobhunt scan`. Show the top 10 jobs in a short list: company, title, pay if stated, and the one-line reason.
3. Ask: "Do you want the scan to run by itself every day?" If yes, run `python -m jobhunt schedule on`.

## 6. Hand over

Tell the user, in three or four short lines:
- where their jobs show up (the sheet link, or `private/tracker/daily_jobs.csv`)
- that each morning they tick **Pick** next to 2–5 jobs (in the sheet, on their phone, or from the morning email), then tell you "work my picks"
- that you never send messages, and never submit anything without asking them first

If they chose full, also ask: "Do you want me to submit applications for the best matches by myself, up to 5 a day? You'd only need to send the messages." If yes, fill in the **Application answers** section of `private/profile.md` with them (work authorization, sponsorship, notice period, the voluntary questions), run `python -m jobhunt answers init` and put the same answers in `private/answers.json` (the `apply` command reads that file), then run `python -m jobhunt mode full --auto-apply`. Offer the two optional setups in [MODES.md](../MODES.md#what-the-apply-command-handles): the emailed-code reader and a one-time sign-in for careers sites they use. Tell them how to turn it off.

Then suggest one more step: download their LinkedIn data so you can check who they know at each company before they apply. Give them the clicks from "Add your LinkedIn data" in [START-HERE.md](../START-HERE.md); when the full archive arrives, run `python -m jobhunt network build "<folder>"` for them.

To hand the day-to-day work to another agent, such as Muse or Grok, give it the kickoff message in [kickoff.md](kickoff.md).
