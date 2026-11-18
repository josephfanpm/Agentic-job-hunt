# Daily scan

The scan is a script. It reads every source in `private/config.json`, filters by title, location and age, scores each job with your rules, removes duplicates and anything shown before, and saves each job description to `private/jds/`.

```bash
python -m jobhunt scan            # add --dry-run to preview without recording anything
```

## Run it automatically

```bash
python -m jobhunt schedule on                 # every time you log in
python -m jobhunt schedule on --at 08:00      # at log-on and every day at 8:00
python -m jobhunt schedule status
python -m jobhunt schedule off
```

This uses your computer's own scheduler: Task Scheduler on Windows, launchd on macOS, cron on Linux. No window opens, and no AI is used. The scheduled scan:

- runs at most once a day, however often you log in
- waits up to 5 minutes for the internet after start-up
- writes what happened to `private/logs/scan.log`

It catches up after days away, because it looks back `max_age_days`, and the seen-list stops anything showing twice.

**Where results go**
- **CSV tracker:** new rows at the top of `private/tracker/daily_jobs.csv`.
- **Google Sheet:** set up the receiver once ([sheet/README-apps-script.md](../sheet/README-apps-script.md)). It takes about 5 minutes and needs no Google Cloud account. Until then, scheduled scans skip rather than lose results.

### Why not a scheduled cloud agent?

You can schedule an AI agent in the cloud to run the scan instead, but it fails in two common ways:

- **The cloud network blocks job sites.** Hosted agent sandboxes often allow only a short list of websites, so job boards answer "403 Forbidden" and the scan finds nothing. If you use one anyway, allow these domains in its network settings: `boards-api.greenhouse.io`, `api.lever.co`, `api.ashbyhq.com`, `apply.workable.com`, `remoteok.com`, `remotive.com`, `weworkremotely.com`, `himalayas.app`, `hn.algolia.com`, `www.amazon.jobs`, each Workday site you track (such as `cigna.wd5.myworkdayjobs.com`), `script.google.com` and `script.googleusercontent.com`. JobSpy also needs `www.linkedin.com`, `www.indeed.com`, `ca.indeed.com`, `www.ziprecruiter.com` and `www.glassdoor.com`.
- **It shares your AI usage limit.** A scheduled agent draws on the same allowance as your own chats. After a heavy session, the morning run is refused and nothing is added.

The local schedule avoids both: it runs on your network, and the scan needs no AI.

## Keeping the list fresh

The daily list holds only jobs you could still apply to:

- **Applied jobs leave the list.** Tick **Applied** (or run `python -m jobhunt applied` with the CSV tracker), and the job moves to the Applied tab, which is the record from then on.
- **Old jobs are archived.** Jobs you haven't applied to move to an **Archive** tab (or `archive.csv`) once they're older than `expire_after_days`, which defaults to 14. Age is counted from the posting date, or from the day the scan found the job when the posting has no date. Archived jobs never come back as new.
- **Priority companies are exempt.** Jobs at `priority_companies` stay however old they are, because a referral can still work on an older posting.
- Set `"expire_after_days": 0` to keep everything.

**Why 14 days:** recruiters review the earliest applicants first, so a cold application to a posting more than about two weeks old rarely gets looked at. With a referral or a direct message to the hiring manager, an older posting can still be worth it, which is why priority companies are exempt.

## Sources

| Source | Turn it on in config | Notes |
|---|---|---|
| Greenhouse, Lever, Ashby, Workable | `python -m jobhunt boards add "Company"` | One request per company; the freshest and most reliable |
| Workday careers sites | `python -m jobhunt boards add "<careers page URL>" --name "Company"` | For employers with no public feed, common at insurers, hospital systems and banks. Reads the list the careers page itself loads, then opens only postings whose titles match. On big sites, add `"categories"` to the entry (the command lists them) |
| Remote OK, Remotive, Himalayas | `sources.remoteok` etc. (on by default) | Remote roles; responses are cached for hours, as those boards ask |
| We Work Remotely | `sources.weworkremotely: ["remote-product-jobs"]` | List the category feeds you want |
| Hacker News "Who is hiring?" | `sources.hackernews` (on by default) | Free-text posts, so company, title and location are best guesses |
| Amazon | `sources.amazon: true` | Amazon's own careers search |
| LinkedIn, Indeed, ZipRecruiter, Glassdoor | `sources.jobspy: true`, plus `jobspy.searches` | Needs `pip install python-jobspy`; LinkedIn often rate-limits; adds a minute or two |

## Tuning

- **Too many poor matches:** add words to `titles.exclude`, or set `keywords.require_any` and raise `keywords.require_min` to 2.
- **Too few:** widen `titles.include`, raise `max_age_days`, add company boards. A company that `boards add "Company"` can't find may be on Workday: open its careers page, copy the address once the job list shows, and add that.
- **One employer fills the list:** lower `max_per_company`. Legal names such as "Amazon Web Services, Inc." count as the company you listed in `priority_companies` or `big_companies`.
- **Ranking feels off:** edit `keywords.boost`. Title matches count more than description matches, and benefits or legal text is ignored.
- The scan prints how many jobs each rule dropped, so you can see what a change does.
