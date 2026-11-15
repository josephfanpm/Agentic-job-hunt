# Evaluate a job's fit

Use this before spending time on an application. Full mode runs it on every new job; in other modes, run it on request.

## Inputs

- The job description: `private/jds/<Company>__<Title>.txt` if the scan saved it, otherwise fetch the real posting. Never evaluate from a title alone.
- `private/profile.md`.
- `python -m jobhunt check private/resume.pdf --jd <jd file>` for the keyword gap.

## Grade five things, each 1–5

| | 1 | 5 |
|---|---|---|
| **Requirements** | Missing a hard requirement (years, licence, degree, clearance) | Meets every stated requirement |
| **Experience match** | Different domain and different kind of work | Has done this same work, with results to show |
| **Level** | Two levels off | The level held now, or one step up |
| **Pay and location** | Below the floor, or can't work there | At or above target, in a workable location |
| **Path in** | Cold application, no contact | A referral or warm contact at the company |

## Output

```
Grade: A / B / C / D          (A = apply now, B = apply if there's a path in, C = stretch, D = skip)
Scores: requirements 4, experience 5, level 4, pay 3, path in 2
Strongest evidence: <the two profile facts that match best, quoted from the profile>
Gaps: <requirements the profile doesn't back, stated plainly>
Next step: <one action, e.g. "ask Dana at Acme for a referral before applying">
```

Rules:
- Quote evidence from the profile. If the profile doesn't show it, it's a gap.
- A hard requirement the user can't meet caps the grade at C. Say which one.
- Don't soften a poor fit. A clear "skip" saves the user an hour.
- Write the grade and next step in the job's Notes cell.
