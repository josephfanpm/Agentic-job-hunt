# Tailor a resume and cover letter

## Before writing

1. **Get the real job description.** The scan saves one per job in `private/jds/`. If it isn't there, fetch the posting and save it. If you can't, stop: never tailor from a guess or a remembered description.
2. **See the gap:** `python -m jobhunt check private/resume.pdf --jd <jd file>` lists the posting's most-used terms that the base resume lacks. Treat it as a list of things to check against the profile, not a list of words to add.
3. **Look up the company's tools** in this posting and its other postings.
4. **Read `private/profile.md`:** experience, wins, metrics and approved bullets.

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
python -m jobhunt check resume.pdf --jd <jd file>
```

The check reads the PDF the way an applicant tracking system does. It fails if the PDF runs past one page, has fused letters, has no email in its text, or has a line that wraps with only 1–3 words. Fused letters turn "staffing" into "sta?ing", so the keyword never matches. It warns about missing section headings, multi-column layouts and images. Fix every failure and recompile.

## Cover letter

Write one only if the form accepts it. Keep it to three short paragraphs: why this team (one specific detail), two results that match the job, and a close. Check it with `python -m jobhunt check letter.pdf --letter`.

## Save

Name files `First_Last_Resume_Company.pdf` and `First_Last_Cover_Letter_Company.pdf`, and link them in the job's Resume and Cover letter cells.
