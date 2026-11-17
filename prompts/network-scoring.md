# Score your LinkedIn network

Warm contacts beat cold ones, so mine the people you already know before you search for strangers.

## Get the data

On a computer: LinkedIn → **Me** → **Settings & Privacy** → **Data privacy** → **Get a copy of your data** → choose the larger archive. A first file arrives within minutes and the full archive within 24 hours; wait for the full one (the link works for 72 hours). Unzip it and run:

```bash
python -m jobhunt network build "<the unzipped folder>"
```

That writes `private/network/contacts.csv` (every connection with message counts, last message, endorsements, recommendations) and `private/network/pending.csv` (invitations not accepted yet). Nothing in `private/` is ever committed.

## Prompt

> Score every connection in `private/network/contacts.csv` against my goal. Don't sample or skip anyone.
>
> **MY GOAL:** {{goal, e.g. a mid-level PM role at a company that pays at least X}}
> **WHO I'M LOOKING FOR:** {{roles, companies, industries, seniority}}
>
> Rate each connection 1–5 on title, company, seniority and tenure. Use the warmth columns too: someone who replied to me (`received` above 0), endorsed me or recommended me is warm, and outranks a cold contact with the same title.
>
> Show only the 4s and 5s, in 2–4 categories that fit my goal (for example: warm PM insiders, warm referral sources, cold PM peers, cold hiring managers and recruiters). For each one, give a one-sentence reason they fit this goal, and an opening line that names a real detail from their title or company. Never use "great to connect".
>
> Say plainly what this file can't show: their About section, recent posts and mutual connections. For every strong match, tell me to check their profile for a sharper detail to mention.
>
> Finally, name the groups that barely appear in my network. Those are where I need new connections, so I'll switch to Boolean search ([linkedin-search.md](linkedin-search.md)).
>
> Output a table sorted by score: name, company, title, score, category, why they fit, suggested opener. Then write the matches to the Network tab.

## After scoring

- Draft about 5 messages a week, using [outreach.md](outreach.md). Before writing each draft, read that person's message history in the export's `messages.csv`, so it refers to what you actually discussed.
- Before every application, run `python -m jobhunt network find "Company"`. Someone you know there is worth more than any cold message.
- When you send one, set Status to Messaged and fill in Messaged on. Follow up on fills itself in 7 days later.
