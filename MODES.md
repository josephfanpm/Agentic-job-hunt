# Choose your flow

Three flows do the same job search with different amounts of AI. Pick one with:

```bash
python -m jobhunt mode lean      # or: standard, full
```

The setting lives in `private/config.json` as `"mode"`. Agents read it and follow the rules for that mode below. You can switch at any time.

| | **Lean** | **Standard** | **Full** |
|---|---|---|---|
| Best for | Lowest AI usage | Most people | Least effort from you |
| Daily scan | Script only | Script, then the agent reviews the list | Script, then the agent evaluates every new job |
| Ranking and "why it fits" | Rules in your config | Rules, with the agent removing poor fits | The agent writes a fit evaluation per job |
| LinkedIn searches | Script | Script | Script |
| Keyword gap and resume check | Script | Script | Script |
| Tailored resume and cover letter | Only for jobs you pick | Only for jobs you pick | Prepared ahead for the top matches |
| Submitting the application | The agent, for jobs you pick | The agent, for jobs you pick | You, or the agent for the top matches if you turn on auto-apply |
| Finding the person to message | You, from the search links | You, from the search links | The agent names one person per job |
| Outreach messages | Only when you ask | One draft per job you pick | Drafted for the top matches. You send them |
| Follow-ups and weekly review | Script (`due`, `stats`) | The agent drafts nudges | The agent drafts nudges and a review |
| AI use on a day you apply to nothing | None with the CSV tracker | A little | The most |

## What uses AI and what doesn't

These commands make no AI calls in any mode:

| Command | What it does |
|---|---|
| `python -m jobhunt scan` | Reads every source, filters, ranks, removes duplicates, saves each job description |
| `python -m jobhunt people "Company" "Title"` | Three LinkedIn searches with links (`--wider` adds two fallback searches) |
| `python -m jobhunt picks` | Lists the jobs ticked Pick and not yet applied |
| `python -m jobhunt network build <folder>` / `network find "Company"` | Indexes your LinkedIn export; lists who you know at a company |
| `python -m jobhunt check resume.pdf --jd job.txt` | Resume pre-flight and keyword gap |
| `python -m jobhunt boards add "Company"` | Finds a company's job board |
| `python -m jobhunt applied / due / stats` | Logs applications, lists follow-ups, compares channels (CSV tracker) |

AI is used where judgment or writing is needed: tailoring a resume, writing a cover letter or message, evaluating fit in depth, interview practice.

## The tracker matters too

- **CSV tracker** (`"tracker": "csv"`): the scan writes straight to files in `private/tracker/`. No agent is involved, so a scheduled scan costs nothing. Open the files in Excel, or import them into Google Sheets.
- **Google Sheet with the receiver** (`"tracker": "sheet"` plus `sheet_webhook`): the scan writes straight to your sheet through a small script inside it ([setup](sheet/README-apps-script.md)). Also no AI.
- **Google Sheet without the receiver:** the scan prepares an update file, and an agent sends it through its Sheets connector. That costs a small amount of AI use per scan.

Lean mode with the CSV tracker or the sheet receiver, scheduled with `python -m jobhunt schedule on`, uses no AI until you pick a job.

## Rules for agents, by mode

**Every mode**
- Run the scripts instead of doing their work by hand. Never rank, dedupe or build LinkedIn searches yourself.
- Read a job description from `private/jds/` if the scan saved it. Fetch it only if it isn't there.
- Don't read a whole tracker tab when a script or one row answers the question.

**Lean**
- Do nothing unprompted. Act only on jobs the user names.
- For the daily scan with a sheet: run `python -m jobhunt scan`, send the update file it names, report the one-line summary. Don't comment on individual jobs.
- Before tailoring, run `check --jd` on the base resume and work from its gap list. Don't re-read the whole profile if the approved bullets cover the job.
- One draft per message. No alternatives unless asked.

**Standard**
- After the scan, read the result file and flag at most three jobs that the rules ranked high but look like poor fits, with a one-line reason each.
- For each job the user picks: tailor, check, draft one message, log it.
- Draft follow-up nudges when they come due.

**Full**
- After the scan, run [prompts/evaluate.md](prompts/evaluate.md) on every new job and write the verdict in the Notes column.
- For jobs graded A or B, prepare the tailored resume, cover letter and one outreach draft ahead of time.
- Name one person to message for each of those jobs, following [prompts/find-person.md](prompts/find-person.md). If no hiring manager or recruiter turns up, use its fallback: a manager in the same function who could be hiring for the role.
- **Auto-apply off (the default):** do not submit. The user still picks what goes out.
- **Auto-apply on:** submit those applications yourself, following [prompts/auto-apply.md](prompts/auto-apply.md). Never send the messages.
- Once a week, run [prompts/review.md](prompts/review.md).

## Auto-apply (Full mode only)

```bash
python -m jobhunt mode full --auto-apply       # agents submit for the top matches
python -m jobhunt mode full --no-auto-apply    # agents prepare, you submit
```

With auto-apply on, the agent tailors the resume, fills in the form and submits, without asking first, for new jobs graded B or better. Your part is to send the message it drafts for each one. Settings in `private/config.json`:

| Setting | Default | What it does |
|---|---|---|
| `auto_apply.enabled` | `false` | The switch the commands above set |
| `auto_apply.max_per_day` | `5` | The most applications an agent submits in a day |
| `auto_apply.min_grade` | `"B"` | Set to `"A"` to submit only the strongest fits |

The agent still stops and hands the job to you when:

- you know someone at the company, or it's one of your `priority_companies` (ask for a referral first)
- the form asks something your profile's **Application answers** section doesn't cover, such as a sponsorship question
- the site needs an account, a password, a captcha or an assessment
- the form asks you to agree to more than "these answers are true"

Before each submission the agent saves the answers it entered to `private/applications/`, so you can see what went out under your name.

Auto-apply raises the number of cold applications, and cold applications convert poorly (see the README). Keep the daily limit low, and send the messages: the message is what turns a cold application into a conversation.

### Letting the agent open LinkedIn

To name a person, the agent first uses the posting, the company's own site and a web search. None of those touch your LinkedIn account. Set `"linkedin": {"browse": true}` to also let it open LinkedIn in your own signed-in browser, limited to `max_searches_per_day` and `max_profiles_per_day` (10 each). LinkedIn's terms don't allow automated use, so this carries some risk to your account however carefully it's done. With it off, you get the search links to open yourself. The rules are in [prompts/find-person.md](prompts/find-person.md).
