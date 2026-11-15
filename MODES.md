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
| Outreach messages | Only when you ask | One draft per job you pick | Drafted for the top matches |
| Follow-ups and weekly review | Script (`due`, `stats`) | The agent drafts nudges | The agent drafts nudges and a review |
| AI use on a day you apply to nothing | None with the CSV tracker | A little | The most |

## What uses AI and what doesn't

These commands make no AI calls in any mode:

| Command | What it does |
|---|---|
| `python -m jobhunt scan` | Reads every source, filters, ranks, removes duplicates, saves each job description |
| `python -m jobhunt people "Company" "Title"` | Three LinkedIn searches with links |
| `python -m jobhunt check resume.pdf --jd job.txt` | Resume pre-flight and keyword gap |
| `python -m jobhunt boards add "Company"` | Finds a company's job board |
| `python -m jobhunt applied / due / stats` | Logs applications, lists follow-ups, compares channels (CSV tracker) |

AI is used where judgment or writing is needed: tailoring a resume, writing a cover letter or message, evaluating fit in depth, interview practice.

## The tracker matters too

- **CSV tracker** (`"tracker": "csv"`): the scan writes straight to files in `private/tracker/`. No agent is involved, so a scheduled scan costs nothing. Open the files in Excel, or import them into Google Sheets.
- **Google Sheet** (`"tracker": "sheet"`): the scan prepares one update file, and an agent sends it through its Sheets connector. That costs a small, fixed amount of AI use per scan, because the agent has to pass the rows along.

Lean mode with the CSV tracker is the cheapest setup. Lean mode with a sheet is next.

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
- For jobs graded A or B, prepare the tailored resume, cover letter and one outreach draft ahead of time. Do not submit: the user still picks what goes out.
- Once a week, run [prompts/review.md](prompts/review.md).
