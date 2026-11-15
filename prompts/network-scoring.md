# Score your LinkedIn network

Warm contacts beat cold ones, so mine the people you already know before you search for strangers.

## Get the data

LinkedIn → Settings & Privacy → Data privacy → **Download your data** → choose the larger archive. It arrives in about 30 minutes, sometimes in two parts. Keep `Connections.csv` and `messages.csv` in `private/`; they never get committed.

## Prompt

> Score every connection in `private/Connections.csv` against my goal. Don't sample or skip anyone.
>
> **MY GOAL:** {{goal, e.g. a mid-level PM role at a company that pays at least X}}
> **WHO I'M LOOKING FOR:** {{roles, companies, industries, seniority}}
>
> Rate each connection 1–5 on title, company, seniority and tenure. Also use `messages.csv`: someone I've actually messaged is warm, and outranks a cold contact with the same title. Ignore rows with no name.
>
> Show only the 4s and 5s, in 2–4 categories that fit my goal (for example: warm PM insiders, warm referral sources, cold PM peers, cold hiring managers and recruiters). For each one, give a one-sentence reason they fit this goal, and an opening line that names a real detail from their title or company. Never use "great to connect".
>
> Say plainly what this file can't show: their About section, recent posts and mutual connections. For every strong match, tell me to check their profile for a sharper detail to mention.
>
> Finally, name the groups that barely appear in my network. Those are where I need new connections, so I'll switch to Boolean search ([linkedin-search.md](linkedin-search.md)).
>
> Output a table sorted by score: name, company, title, score, category, why they fit, suggested opener. Then write the matches to the Network tab.

## After scoring

- Draft about 5 messages a week, using [outreach.md](outreach.md). Before writing each draft, read that person's message history, so it refers to what you actually discussed.
- When you send one, set Status to Messaged and fill in Messaged on. Follow up on fills itself in 7 days later.
