# Build the experience bank (profile interview)

One resume can't fit every job. This interview collects everything the user has done, so each tailored resume can pick the jobs, projects and results that match one posting and write fresh bullets for it. The answers go in the **Experience bank** section of `private/profile.md`.

Run it during setup, and again whenever the user starts a new job or finishes a project.

## How to interview

- **Start from what you already have.** Read `private/profile.md` and their resume. Don't ask for what's already there; confirm it instead ("Your resume says you were a Product Manager at Acme from March 2022 to now. Is that right?").
- **Ask one question at a time,** in plain language, with an example answer. If the user isn't technical, avoid jargon such as "KPI", "stakeholder" or "scope". Ask "What number got better?" and "Who did you work with?"
- **Dig for the result.** When they describe work, ask: what changed, for whom, by how much, and how they know. If they don't know the number, record the result without one. **Never suggest or estimate a number.**
- **Write down the source of every number** (a dashboard, a report, a performance review, their manager). If they can't say where it came from, mark it `(unverified)`. Tailoring skips unverified numbers.
- **Save as you go.** Write each role to the file when it's done, so nothing is lost if the user stops.
- **Let them stop at any time.** Say which role you'll pick up from next time.

## What to collect

**For each job, most recent first:**
1. Title, company, start and end month and year.
2. **About the company:** what it sells and to whom, industry, rough size (people or customers), and stage (startup, growth, public, non-profit, government). Ask what a recruiter outside the company would need to know to picture it.
3. **The role:** team, who they reported to, who they worked with most (engineering, sales, clinicians, customers), and what they owned.
4. **Projects, 2–5 per job.** For each one:
   - The problem, and why it mattered
   - What *they* did, as opposed to the team
   - The result, with the number and its source
   - Tools, methods and skills used
   - Who used it or benefited (users, customers, staff)
5. **Other wins:** awards, promotions, things they started, people they trained or managed.

**Then, outside work:** side projects, volunteering, school projects, publications, certifications and licenses. For each one, ask whether it's public, and get the link if so.

**Last:** "Is there anything you're proud of that we haven't covered?"

## How to write it

Add this under the `## Experience bank` heading in `private/profile.md`, one block per job:

```
### Product Manager, Acme Health (Mar 2022 – present)
Company: Online scheduling for home-care agencies; about 200 staff; Series B; customers are agency owners in the US.
Role: Owned the scheduling app for caregivers. Reported to the VP Product. Worked daily with 6 engineers and the support team.

- Project: Shift swap
  Problem: Caregivers called the office to swap shifts, and about 1 in 10 shifts went unfilled.
  Did: Interviewed 20 caregivers, wrote the spec, ran a two-month test in 3 agencies.
  Result: Unfilled shifts fell from 11% to 7% (source: Looker dashboard, Q3 2024).
  Skills: user interviews, A/B testing, SQL, Figma
```

Keep their words where you can. Don't polish it into resume bullets yet: tailoring does that for each job.

## When you're done

Show the user a short summary: how many jobs and projects, and which results have no number or no source yet. Ask whether you may write 3–5 **Approved bullets** for their strongest work. Agents use approved bullets word for word, so add them only after the user says yes to each one.
