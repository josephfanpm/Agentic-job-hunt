# Daily scan

The scan is a script. It reads every source in `private/config.json`, filters by title, location and age, scores each job with your rules, removes duplicates and anything shown before, and saves each job description to `private/jds/`.

```bash
python -m jobhunt scan            # add --dry-run to preview without recording anything
```

## With the CSV tracker

No agent is needed. Schedule the command itself:

- **Windows:** Task Scheduler → run `python -m jobhunt scan` daily, starting in the repo folder.
- **macOS / Linux:** `0 8 * * 1-5 cd /path/to/agentic-job-hunt && python -m jobhunt scan`

New rows appear at the top of `private/tracker/daily_jobs.csv`.

## With a Google Sheet

Schedule an agent with this prompt. It's written for an unattended run.

> Run `python -m jobhunt scan` in the repo. If it prints "sheet update ready", send that file's contents as one `batchUpdate` to the spreadsheet it names, without changing them. Then read row 2 of "Daily jobs" back to confirm it landed. Follow AGENTS.md: never reorder, delete or overwrite existing rows. If the scan found nothing, do nothing. Finish with the scan's first two lines of output.
>
> Then follow the rules for the current mode in MODES.md.

## Sources

| Source | Turn it on in config | Notes |
|---|---|---|
| Greenhouse, Lever, Ashby, Workable | `python -m jobhunt boards add "Company"` | One request per company; the freshest and most reliable |
| Remote OK, Remotive, Himalayas | `sources.remoteok` etc. (on by default) | Remote roles; responses are cached for hours, as those boards ask |
| We Work Remotely | `sources.weworkremotely: ["remote-product-jobs"]` | List the category feeds you want |
| Hacker News "Who is hiring?" | `sources.hackernews` (on by default) | Free-text posts, so company, title and location are best guesses |
| Amazon | `sources.amazon: true` | Amazon's own careers search |
| LinkedIn, Indeed, ZipRecruiter | `sources.jobspy: true`, plus `jobspy.searches` | Needs `pip install python-jobspy`; LinkedIn often rate-limits |

## Tuning

- **Too many poor matches:** add words to `titles.exclude`, or set `keywords.require_any`.
- **Too few:** widen `titles.include`, raise `max_age_days`, add company boards.
- **One employer fills the list:** lower `max_per_company`.
- **Ranking feels off:** edit `keywords.boost`. Title matches count more than description matches, and benefits or legal text is ignored.
- The scan prints how many jobs each rule dropped, so you can see what a change does.
