# Tailor a resume and cover letter

## Before writing

1. **Fetch the real job description** and save it. Greenhouse (`boards-api.greenhouse.io/v1/boards/<board>/jobs/<id>`), Ashby (`api.ashbyhq.com/posting-api/job-board/<org>`) and Lever all have public APIs. If you can't fetch it, stop: never tailor from a guess or a remembered description.
2. **Look up the company's tools**: check this posting and the company's other postings for their stack.
3. **Read `private/profile.md`**: experience, wins, metrics, and approved bullets.

## Resume rules

- **Layout:** Jake's Resume ([resume/template.tex](../resume/template.tex)), one page, filled to the bottom with no empty space.
- **Section order:** Experience, Projects, Education, Additional Information.
- **No generic skills list** (Diego Granados's advice). Put job keywords inside bullets, showing how you used each one, and only where your experience backs it up. Additional Information is 2–3 lines: Tools (only real tools, the company's matching stack first), Languages, and Licensure if it helps.
- **Education** shows the graduation year only.
- **Bullets:** action + what changed for users + a number. Put the bullets closest to this job first.
- **Plain language.** A recruiter outside your company must understand every bullet. Replace internal feature names with what changed for the user.
- **Numbers come only from your own sources.** If you can't defend a number in an interview, leave it out.
- **Never invent** titles, employers, dates, degrees, tools or projects. Projects are public repos only, each name a hyperlink.

## Compile and check

```
tectonic resume.tex
python scripts/check_pdf.py resume.pdf
```

The check fails if the PDF runs past one page, has fused ligatures, or has a line that wraps with only 1–3 words. Fused ligatures turn "staffing" into "sta?ing" for an ATS, so the keyword never matches. Fix every failure and recompile.

## Cover letter

Write one only if the form accepts it. Keep it to three short paragraphs: why this team (one specific detail), two results that match the job, and a close. Run the same checks.

## Save

Name files `First_Last_Resume_Company.pdf` and `First_Last_Cover_Letter_Company.pdf`, and link them in the job's Resume and Cover letter cells.
