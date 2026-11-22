# Turn shared skill gaps into a learning plan

The terms most postings for a role share describe the role itself. When the user's resume doesn't use one, either they have the experience and didn't write it down, or it's a real gap. This prompt sorts the two and plans the second.

**When:** once the scan has saved at least ten job descriptions for the target title, then monthly, or when the user asks. In Full mode, run it with the weekly review ([review.md](review.md)) once a month.

## Steps

1. **List the gaps.** Run:

   ```
   python -m jobhunt terms private/jds/*.txt --gaps private/resume.pdf
   ```

   It lists the terms three or more postings share that the resume doesn't use, with how many postings use each. Drop generic words that describe no skill ("solutions", "value", "process").

2. **Sort each remaining term** against `private/profile.md`:
   - **Have it, not written down:** the profile shows the experience under another name, or the user has done it. Add it to the resume and the Experience bank in the posting's words, where true. If you're unsure, ask the user one question at a time, as in [profile-interview.md](profile-interview.md).
   - **Real gap:** nothing in the profile supports it.
   - **Not worth it:** the term comes from a kind of role the user doesn't want, or appears only in a few postings. Say why in one line.

3. **For each real gap, plan the smallest proof**, worked out from the postings that ask for it:
   - **What good enough looks like:** what the postings actually ask for (for example, "writes SQL for their own analysis", not "database administrator").
   - **The smallest thing that shows it:** a public project, a short course with a certificate, or a task in the user's current job. A project the user can link beats a course they can only list.
   - **Resources:** two or three, found by web search, each with a link. Prefer free and recent. Check that each link works.
   - **Time:** an estimate in hours, and say it's an estimate.

4. **Rank the plan** by how many postings ask for the skill, divided by the hours it takes. Put the top three first.

## Output

Save to `private/learning-plan.md`:

- **Add to the resume now:** the terms the user already has, with the bullet each one goes in
- **Learn next:** the ranked gaps, each with what good enough looks like, the smallest proof, resources and hours
- **Skipped:** the terms left out, one line each

Tell the user the top three in chat, in plain language.

## Rules

- **Never put a skill on the resume until there's proof.** A course in progress or a plan is not experience. Add it to the profile only when the user has done the work, and say what they did.
- Don't pad the plan. Three gaps worth closing are better than ten.
- Compare with the last plan, if there is one, and mark what the user has closed since.
