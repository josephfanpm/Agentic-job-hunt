# Find the person to message

Every application gets one named person to message. In Full mode the agent finds them; in other modes, use this when the user asks "who should I message at Company?".

## Who to look for, in order

1. **Someone the user already knows there.** Run `python -m jobhunt network find "Company"`. A known contact beats any stranger.
2. **The hiring manager for the role.**
3. **A recruiter for the role.**
4. **A likely hiring manager.** If you can't find either, use the fallback rule below.

## Where to look, in order

Stop at the first step that gives you a name. The early steps cost nothing and never touch the user's LinkedIn account.

1. **The saved job description.** Some postings name the recruiter, or say who the role reports to.
2. **The company's own site:** its team, about or leadership page, and the authors of its product or engineering blog. Follow the rules in [fetch-pages.md](fetch-pages.md).
3. **A web search, not a LinkedIn search.** Take a title from `python -m jobhunt people "Company" "Job title"` and search the web for it, for example `site:linkedin.com/in "Acme" "director of product"`. Read only the result titles and snippets. Search results can be months old, so treat the person as unconfirmed unless another source agrees.
4. **LinkedIn in the user's browser,** only when `linkedin.browse` is `true` in `private/config.json`, and only by the rules below.

## Rules for opening LinkedIn

LinkedIn's terms don't allow automated use, and nothing removes the risk that it limits an account. These rules keep the activity small and slow, at about what a person does by hand. The user accepts the remaining risk by turning `linkedin.browse` on.

- **Use only the user's own browser, already signed in,** through a tool that drives that browser. Never read linkedin.com with a fetch tool, a script or a headless browser. Never sign in for the user, handle their password, or use a second account, a proxy or a VPN.
- **Open the search links that `python -m jobhunt people` prints.** Then set LinkedIn's **Current company** filter. Don't build other searches.
- **Stay under the daily limits:** `linkedin.max_searches_per_day` search pages and `linkedin.max_profiles_per_day` profiles (10 each by default). Before each page, count today's lines in `private/logs/linkedin.log`; after each page, add a line with the date and the address.
- **Read the first page of results only,** and take names and headlines from the list.
- **Open one profile per job:** the person you chose, to confirm they still work there and to find a real detail for the message. The person can see that the user viewed their profile.
- **One page at a time.** Read it, wait a few seconds, then open the next. No extra tabs.
- **Never click Connect, Message, Follow, InMail, Like or Endorse.** The user sends everything.
- **Stop for the day** at a captcha, an "unusual activity" or identity check, a search-limit notice, a sign-in page or an empty page. Don't retry or try another route. Tell the user what you saw (Rule 11 in [AGENTS.md](../AGENTS.md)).
- **Keep one person per job.** Don't save or export lists of people.

If `linkedin.browse` is off, or you hit a limit, put the search links in the report so the user can open them.

## Fallback: a likely hiring manager

Use this when the steps above find no hiring manager and no recruiter for the role.

1. Run `python -m jobhunt people "Company" "Job title" --wider`. The **Managers, any team** search drops the team words and finds managers in the same function (director, head, group or senior manager).
2. Pick the person most likely to be hiring for this role:
   - same function as the job (product for a product manager, engineering for an engineer)
   - same business unit or location, when the posting names one
   - the lowest level that still manages people in that function, since they sit closest to the role
3. At a small company (about 50 people or fewer, or no managers in that function), use the head of the function. If there isn't one, use a founder or the CEO: the **Company leaders** search.
4. If nobody fits, leave the Hiring manager cell empty and write `no contact found` in Notes. Never guess a name or an email address.

## Record who you found

- **Hiring manager cell:** name, title and profile link, plus one label: `hiring manager`, `recruiter`, or `likely hiring manager, not confirmed`.
- **Notes:** where the name came from (posting, company site, web search or LinkedIn).
- **Message:** draft it with [outreach.md](outreach.md). For a likely hiring manager, use the version that doesn't assume the role is theirs.
