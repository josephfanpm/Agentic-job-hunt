# Tailor a resume and cover letter

The README's [Resume rules, and why](../README.md#resume-rules-and-why) explains the reason behind each rule below.

## Before writing

1. **Get the real job description.** The scan saves one per job in `private/jds/`. If it isn't there, read the posting and save it, following [fetch-pages.md](fetch-pages.md). If you can't, stop: never tailor from a guess or a remembered description.
2. **See the gap:** `python -m jobhunt check private/resume.pdf --jd <jd file>` lists the posting's most-used terms that the base resume lacks. Treat it as a list of things to check against the profile, not a list of words to add.
3. **Look up the company's tools** in this posting and its other postings.
4. **Read `private/profile.md`,** especially the **Experience bank**: every job, project, result and company detail the user gave in [profile-interview.md](profile-interview.md).
5. **Choose what goes in for this job.** Rank the bank's projects by how closely they match the job description's top needs, and pick the strongest for each role. Different jobs should get different projects in a different order, not the same resume with new keywords. If the bank is empty or thin, offer to run the profile interview first; otherwise work from the base resume.

**Building the base resume** (no single job yet): run `python -m jobhunt terms private/jds/*.txt` on at least five saved postings for the target title. It lists the terms that appear in three or more of them. Those describe the role itself, so work the ones the user's experience backs up into the bullets.

## Resume rules

**The page**
- **Layout:** Jake's Resume ([resume/template.tex](../resume/template.tex)): one column, one page, filled to the bottom with no empty space.
- **Section order:** Experience, Projects, Education, Additional Information.
- **The top third carries the match.** The first role's title, company line and first 2–3 bullets should answer "does this person fit this job?" on their own. Put the bullets closest to this job first.
- **No summary or objective,** unless the user is changing careers and the experience alone doesn't explain why they fit. Then write two lines on the switch.
- **Company context:** when an employer isn't well known, add a short line under its name saying what it does (from the bank's Company line), so the recruiter can picture it.
- **Projects only when they match the job.** Public repos only, each name a hyperlink. Leave the section out rather than add an unrelated one.
- **Education** shows the graduation year only.

**Each bullet**
- **Action, then what you did with which tool or method, then the result:** *Cut [what] by [number] by [what you did] using [tool or method]*. Write each one fresh for this job from the Experience bank, using the job description's words where the user's work really matches. Use an Approved bullet word for word when it fits.
- **Open with a strong verb** (Launched, Cut, Grew, Built, Led). Never open with a duty ("Responsible for", "Helped", "Worked on", "Assisted").
- **A number in at least 80% of bullets,** but only numbers from the user's sources. If you can't defend a number in an interview, leave it out and say what changed instead. Skip `(unverified)` numbers. Never estimate.
- **No filler:** "team player", "various", "results-driven", "detail-oriented" and the like say nothing a recruiter can check.
- **Plain language.** A recruiter outside the user's company must understand every bullet. Replace internal feature names with what changed for the user.

**Keywords and tools**
- **No generic skills list.** Put job keywords inside bullets, showing how the user used each one, and only where their experience backs it up.
- **Additional Information** is 2–3 lines: Tools (only real tools, the company's matching stack first), Languages, and Licensure if it helps.
- **Every listed tool should appear in a bullet** too. A tool that only sits in a list is a claim; a bullet that shows what you did with it is evidence. If a tool can't go in a bullet, consider dropping it.

**Never invent** titles, employers, dates, degrees, tools, numbers or projects.

## Compile and check

```
tectonic resume.tex
python -m jobhunt check resume.pdf --jd <jd file>
python -m jobhunt check resume.pdf --bullets
```

The check reads the PDF the way an applicant tracking system does. It **fails** if the PDF runs past one page, has fused letters, has no email in its text, or has a line that wraps with only 1–3 words. Fused letters turn "staffing" into "sta?ing", so the keyword never matches. Fix every failure and recompile.

It **warns** about missing section headings, multi-column layouts and images, and about the bullets: fewer than 80% with a number, openers that describe a duty, filler, and listed tools no bullet shows. With `--jd`, it also says which of the posting's terms sit in the top third of the page. `--bullets` lists every bullet with what it's missing. Warnings are judgment calls: fix the ones you can fix with true facts, and leave the rest.

**Runs past one page?** Run `python -m jobhunt check resume.pdf --cuts --jd <jd file>` (add `--cover letter.pdf` once the letter exists). It ranks every bullet by what it does for this job: the posting's terms it uses, whether it has a number, whether another bullet already says much the same, and whether the cover letter relies on it. Shorten the bullets at the top of the list first, then cut them, until the page fits. Keep the top third strong even if a bullet there scores low; say why if you keep one.

## Cover letter

Write one only if the form accepts it. Keep it to three short paragraphs: why this team (one specific detail), two results that match the job, and a close. Check it with `python -m jobhunt check letter.pdf --letter`.

## Review

In Standard and Full modes, have the draft reviewed with [review-draft.md](review-draft.md) before it goes anywhere: a fresh reader checks that every claim traces to the profile, that the top third shows the match, and that the letter is about this company. Apply the true fixes and run the check again.

## Save

Name files `First_Last_Resume_Company.pdf` and `First_Last_Cover_Letter_Company.pdf`, and link them in the job's Resume and Cover letter cells.
