"""Text, location, source parsing and the scan pipeline. No network."""
import datetime as dt
import json

import pytest

from jobhunt import config, geo, pipeline
from jobhunt.models import Job
from jobhunt.sources import boards, feeds
from jobhunt.text import drop_boilerplate, norm_title, parse_pay, strip_html, to_date

TODAY = dt.date(2026, 11, 15)


def cfg(**over):
    c = config._merge(config.DEFAULTS, {
        "titles": {"include": ["product manager"], "exclude": ["director", "intern"]},
        "keywords": {"boost": ["marketplace", "health"]},
        "locations": {"countries": ["US", "CA"]},
        "pay": {"floor": 100_000, "target": 160_000},
    })
    return config._merge(c, over)


def job(**kw):
    base = dict(source="greenhouse", company="Acme", title="Senior Product Manager",
                url="https://example.com/1", location="Austin, TX", posted="2026-11-14")
    base.update(kw)
    return Job(**base)


# ---- text --------------------------------------------------------------------
def test_strip_html_handles_escaped_html():
    raw = "&lt;p&gt;Pay: $100,000 &amp;mdash; $150,000&lt;/p&gt;&lt;p&gt;Next&lt;/p&gt;"
    assert strip_html(raw) == "Pay: $100,000 — $150,000\nNext"


@pytest.mark.parametrize("text,lo,hi", [
    ("Base range $159,800 — $235,000 plus equity", 159800, 235000),
    ("USD 130k-195k", 130000, 195000),
    ("CA$145,900 to CA$197,400", 145900, 197400),
    ("Zone A: $150,000 - $180,000. Zone B: $135,000 - $165,000.", 135000, 180000),
])
def test_parse_pay_reads_ranges(text, lo, hi):
    shown, a, b = parse_pay(text)
    assert (a, b) == (lo, hi) and shown


@pytest.mark.parametrize("text", ["$55.75 - $83.07 per hour", "a team of 100 - 200 people",
                                  "competitive salary", "$5,000 - $10,000 sign-on bonus"])
def test_parse_pay_never_guesses(text):
    assert parse_pay(text) == ("", None, None)


def test_parse_pay_keeps_bare_dollar_unlabelled():
    assert parse_pay("$120,000 - $150,000")[0].startswith("$")
    assert parse_pay("CAD 120,000 - 150,000")[0].startswith("CAD ")


@pytest.mark.parametrize("value,expected", [
    ("2026-11-04T16:15:15-05:00", "2026-11-04"), (1792767640768, "2026-10-23"),
    ("1794728071", "2026-11-15"), ("November 13, 2026", "2026-11-13"),
    ("Thu, 12 Nov 2026 10:00:00 +0000", "2026-11-12"), ("2026-05-29", "2026-05-29"),
    ("", ""), ("not a date", ""),
])
def test_to_date(value, expected):
    assert to_date(value) == expected


def test_norm_title_expands_abbreviations():
    assert norm_title("Sr. Product Mgr - Tech") == "senior product manager tech"


def test_drop_boilerplate_removes_benefit_lines():
    text = "You will grow our health marketplace.\nWe offer health insurance and dental."
    kept = drop_boilerplate(text)
    assert "marketplace" in kept and "insurance" not in kept


# ---- geo ---------------------------------------------------------------------
@pytest.mark.parametrize("loc,expected", [
    ("San Francisco, CA", {"US"}), ("Toronto, ON", {"CA"}), ("Toronto, ON, CA", {"CA"}),
    ("Shenzhen, CHN", {"CN"}), ("Bangalore, IN", {"IN"}), ("United States - Remote", {"US"}),
    ("Edmonton, Alberta, Canada", {"CA"}), ("USA Only", {"US"}), ("Worldwide", {geo.ANY}),
    ("Anywhere in the World", {geo.ANY}), ("London", {"GB"}), ("Some Office Park", set()),
])
def test_countries(loc, expected):
    assert geo.countries(loc) == expected


def test_regions_and_stated_country():
    assert {"US", "CA"} <= geo.countries("North America Only")
    assert "US" not in geo.countries("Remote - EMEA")
    assert geo.countries("New York, NY", stated="US") == {"US"}
    assert geo.is_remote("REMOTE (US Timezones)") and not geo.is_remote("Austin, TX")


# ---- source parsers ----------------------------------------------------------
def test_greenhouse():
    payload = {"jobs": [{"id": 7, "title": "Product Manager", "absolute_url": "https://gh/7",
                         "location": {"name": "Seattle, WA"}, "company_name": "Acme USA",
                         "first_published": "2026-11-10T09:00:00-05:00", "content": "&lt;p&gt;Hi&lt;/p&gt;"}]}
    j = boards.parse_greenhouse(payload)[0]
    assert (j.company, j.location, j.posted, j.job_id) == ("Acme USA", "Seattle, WA", "2026-11-10", "7")
    assert boards.parse_greenhouse(payload, "Acme")[0].company == "Acme"


def test_lever():
    payload = [{"id": "x1", "text": "Product Manager, Growth", "hostedUrl": "https://lever/x1",
                "categories": {"location": "New York, NY", "allLocations": ["New York, NY", "Remote"]},
                "country": "US", "workplaceType": "remote", "createdAt": 1792767640768,
                "descriptionPlain": "Do things", "additionalPlain": "$120,000-$150,000",
                "lists": [{"text": "What you'll do", "content": "<li>Ship</li>"}]}]
    j = boards.parse_lever(payload, "Acme")[0]
    assert j.remote is True and j.country == "US" and "Remote" in j.location
    assert "$120,000" in j.description and "Ship" in j.description


def test_ashby_skips_unlisted_and_distrusts_isremote():
    payload = {"jobs": [
        {"id": "a", "title": "PM", "jobUrl": "https://ashby/a", "location": "Edmonton", "isListed": True,
         "isRemote": True, "workplaceType": "Hybrid", "publishedAt": "2026-06-25T18:47:43.356+00:00",
         "address": {"postalAddress": {"addressRegion": "Alberta", "addressCountry": "Canada"}},
         "secondaryLocations": [{"location": "Vancouver", "address": {"postalAddress": {
             "addressRegion": "British Columbia", "addressCountry": "Canada"}}}],
         "compensation": {"compensationTierSummary": "CA$145,900 – CA$197,400"}, "descriptionPlain": "Body"},
        {"id": "b", "title": "Hidden", "jobUrl": "https://ashby/b", "isListed": False}]}
    jobs = boards.parse_ashby(payload, "Jobber")
    assert len(jobs) == 1
    j = jobs[0]
    assert j.remote is None and "Alberta, Canada" in j.location and "Vancouver" in j.location
    assert j.description.startswith("CA$145,900")


def test_workable_and_board_entry_names():
    payload = {"name": "Hugging Face", "jobs": [{"title": "PM", "shortcode": "AB", "url": "https://w/AB",
               "city": "Paris", "state": "", "country": "France", "telecommuting": True,
               "published_on": "2026-05-29", "description": "<p>x</p>"}]}
    j = boards.parse_workable(payload)[0]
    assert (j.company, j.location, j.remote) == ("Hugging Face", "Paris, France", True)
    assert boards._entry("acme-labs") == ("acme-labs", "")
    assert boards._entry({"slug": "acmeusa", "name": "Acme"}) == ("acmeusa", "Acme")


def test_board_tasks_fall_back_to_a_readable_company_name():
    c = cfg(companies={"lever": ["acme-labs"]})
    label, run = next(boards.tasks(c))
    jobs = run(lambda url, **kw: json.dumps([{"id": "1", "text": "PM", "hostedUrl": "https://l/1"}]).encode())
    assert label == "lever:acme-labs" and jobs[0].company == "Acme Labs"


def test_remote_boards():
    rok = feeds.parse_remoteok([{"legal": "notice"}, {
        "id": "9", "position": "Product Manager", "company": " Fuku ", "location": "",
        "url": "https://remoteok.com/9", "date": "2026-11-13T08:00:21+00:00",
        "salary_min": 120000, "salary_max": 160000, "tags": ["saas"], "description": "<p>d</p>"}])
    assert len(rok) == 1 and rok[0].company == "Fuku" and rok[0].pay_max == 160000 and rok[0].remote
    rem = feeds.parse_remotive({"jobs": [{"id": 1, "url": "https://remotive.com/1", "title": "PM",
                                          "company_name": "Co ", "candidate_required_location": "USA Only",
                                          "salary": "$100k-$130k", "publication_date": "2026-11-11T20:17:48",
                                          "description": "x"}]})
    assert rem[0].location == "USA Only" and "$100k" in rem[0].description
    him = feeds.parse_himalayas({"jobs": [{"title": "PM", "companyName": "C1", "minSalary": 175000,
                                           "maxSalary": 195000, "salaryPeriod": "annual", "currency": "USD",
                                           "locationRestrictions": ["United States"], "pubDate": 1794728071,
                                           "applicationLink": "https://himalayas.app/x", "guid": "g"}]})
    assert him[0].pay == "USD 175,000–195,000" and him[0].location == "United States"


def test_wwr_rss():
    xml = b"""<?xml version="1.0"?><rss><channel><item><title>ProArch: BA/Technical Product Manager</title>
    <region>USA Only</region><skills>SQL</skills><link>https://weworkremotely.com/x</link>
    <pubDate>Mon, 09 Nov 2026 10:00:00 +0000</pubDate><description>&lt;p&gt;d&lt;/p&gt;</description>
    </item></channel></rss>"""
    j = feeds.parse_wwr(xml)[0]
    assert (j.company, j.title, j.location, j.posted) == (
        "ProArch", "BA/Technical Product Manager", "USA Only", "2026-11-09")


def test_hacker_news():
    story = {"hits": [{"title": "Ask HN: Who wants to be hired? (November 2026)", "objectID": "1"},
                      {"title": "Ask HN: Who is hiring? (November 2026)", "objectID": "50"}]}
    assert feeds.latest_hn_story(story) == "50"
    comments = {"hits": [
        {"objectID": "51", "parent_id": 50, "created_at": "2026-11-03T10:00:00Z",
         "comment_text": "Acme (<a href=\"x\">https://acme.io</a>) | Senior Product Manager, Growth | "
                         "REMOTE (US, Canada) | Full-time<p>We build things. $150k-$190k."},
        {"objectID": "52", "parent_id": 51, "created_at": "2026-11-03T11:00:00Z",
         "comment_text": "Is the product manager role still open?"}]}
    jobs = feeds.parse_hn(comments, "50", ["product manager"])
    assert len(jobs) == 1
    j = jobs[0]
    assert j.company == "Acme" and j.title == "Senior Product Manager, Growth"
    assert j.remote is True and j.url.endswith("id=51") and "REMOTE (US, Canada)" in j.location


def test_amazon():
    payload = {"jobs": [{"title": "Sr. Product Manager", "job_path": "/en/jobs/10/x", "id_icims": "10",
                         "normalized_location": "Seattle, Washington, USA", "country_code": "USA",
                         "posted_date": "November 13, 2026", "description": "d", "basic_qualifications": "q"}]}
    j = feeds.parse_amazon(payload)[0]
    assert j.url == "https://www.amazon.jobs/en/jobs/10/x" and j.posted == "2026-11-13" and j.job_id == "10"
    assert "normalized_country_code%5B%5D=CAN" in feeds.amazon_url("product manager", ["US", "CA"])


# ---- pipeline ----------------------------------------------------------------
def test_filters_and_reasons():
    raw = [
        job(title="Product Manager Intern", url="u1"),
        job(title="Software Engineer", url="u2"),
        job(title="Product Manager", location="Berlin, Germany", url="u3"),
        job(title="Product Manager", posted="2026-09-01", url="u4", company="Old Co"),
        job(title="Product Manager", url=""),
        job(title="Sr. Product Manager", url="u6", company="Keeper"),
    ]
    jobs, dropped = pipeline.process(raw, cfg(), today=TODAY)
    assert [j.company for j in jobs] == ["Keeper"]
    assert dropped == {"title excluded": 1, "title not targeted": 1, "outside your countries": 1,
                       "too old": 1, "missing title or link": 1}


def test_unknown_location_and_date_are_kept_with_flags():
    jobs, _ = pipeline.process([job(location="Some Office Park", posted="")], cfg(), today=TODAY)
    assert jobs[0].flags == ["location unverified", "post date unknown"]
    assert "Check:" in jobs[0].why


def test_priority_company_is_exempt_from_age_and_ranks_first():
    raw = [job(company="DoorDash USA", posted="2025-07-14", url="u1"),
           job(company="Fresh Co", posted="2026-11-15", url="u2", title="Product Manager, Marketplace")]
    jobs, _ = pipeline.process(raw, cfg(priority_companies=["DoorDash"]), today=TODAY)
    assert [j.company for j in jobs] == ["DoorDash", "Fresh Co"]
    assert "priority company" in jobs[0].why.lower() and "open since 2025-07-14" in jobs[0].why


def test_scoring_ignores_benefit_boilerplate_and_reads_pay():
    perk = job(company="Perk", url="u1", description="We offer health insurance and wellness.")
    real = job(company="Real", url="u2",
               description="Own our health marketplace roadmap.\nBase pay $170,000 - $210,000.")
    low = job(company="Low", url="u3", description="Salary $60,000 - $80,000")
    jobs, _ = pipeline.process([perk, real, low], cfg(), today=TODAY)
    by = {j.company: j for j in jobs}
    assert by["Real"].score > by["Perk"].score > by["Low"].score
    assert "health" in by["Real"].why and "Matches" not in by["Perk"].why
    assert by["Real"].pay == "$170,000–210,000" and "below your floor" in by["Low"].why
    assert [j.company for j in jobs][0] == "Real"


def test_dedupe_prefers_the_employers_own_board_and_skips_seen():
    raw = [job(source="remoteok", url="agg", company="Acme Inc."), job(source="greenhouse", url="direct"),
           job(company="Seen Co", url="s")]
    seen = {pipeline.job_key("Seen Co", "Senior Product Manager"): "2026-11-01"}
    jobs, dropped = pipeline.process(raw, cfg(), seen, TODAY)
    assert [j.url for j in jobs] == ["direct"]
    assert dropped == {"duplicate": 1, "already seen": 1}


def test_per_company_cap_and_result_limit():
    raw = [job(company="Big", title=f"Product Manager, Team {i}", url=f"u{i}") for i in range(8)]
    raw += [job(company=f"Small {i}", url=f"s{i}") for i in range(4)]
    jobs, dropped = pipeline.process(raw, cfg(max_per_company=2, max_results=5), today=TODAY)
    assert len(jobs) == 5 and sum(j.company == "Big" for j in jobs) == 2
    assert dropped["over the per-company limit"] == 6 and dropped["below today's cut-off"] == 1


def test_require_any_and_remote_only():
    raw = [job(company="A", url="a", description="a nursing marketplace"),
           job(company="B", url="b", description="developer tools")]
    jobs, _ = pipeline.process(raw, cfg(keywords={"require_any": ["nursing"]}), today=TODAY)
    assert [j.company for j in jobs] == ["A"]
    raw = [job(company="A", url="a", location="Remote - United States"), job(company="B", url="b")]
    jobs, dropped = pipeline.process(raw, cfg(locations={"remote_only": True}), today=TODAY)
    assert [j.company for j in jobs] == ["A"] and dropped == {"not remote": 1}


def test_run_survives_a_broken_source_and_remembers_what_it_showed(tmp_path):
    c = cfg(companies={"greenhouse": ["good", "broken"]},
            sources={k: False for k in config.DEFAULTS["sources"]})
    payload = {"jobs": [{"id": 1, "title": "Product Manager", "absolute_url": "https://gh/1",
                         "location": {"name": "Austin, TX"}, "company_name": "Good",
                         "first_published": "2026-11-14T00:00:00Z", "content": ""}]}

    def get(url, **kw):
        if "broken" in url:
            raise RuntimeError("boom")
        return json.dumps(payload).encode()

    dry = pipeline.run(c, home=tmp_path, get=get, today=TODAY, remember=False)
    assert len(dry.jobs) == 1 and not (tmp_path / "state" / "seen.json").exists()
    first = pipeline.run(c, home=tmp_path, get=get, today=TODAY)
    assert [j.company for j in first.jobs] == ["Good"]
    assert "greenhouse:broken" in first.errors and first.stats["greenhouse:good"] == 1
    second = pipeline.run(c, home=tmp_path, get=get, today=TODAY)
    assert second.jobs == [] and second.dropped == {"already seen": 1}
    again = pipeline.run(c, home=tmp_path, get=get, today=TODAY, include_seen=True)
    assert len(again.jobs) == 1


def test_require_any_ignores_benefits_and_spares_priority_companies():
    raw = [job(company="Perks Only", url="a", description="Great health insurance and dental."),
           job(company="Amazon", url="b", description="Kindle reading."),
           job(company="Real", url="c", description="Build our nursing marketplace.")]
    c = cfg(keywords={"require_any": ["health", "nursing"]}, priority_companies=["Amazon"])
    jobs, dropped = pipeline.process(raw, c, today=TODAY)
    assert sorted(j.company for j in jobs) == ["Amazon", "Real"] and dropped == {"no required keyword": 1}


def test_forget_undoes_remember(tmp_path):
    j = job()
    pipeline.save_seen(tmp_path / "state" / "seen.json", {pipeline.job_key(j.company, j.title): "2026-11-15"})
    pipeline.forget(tmp_path, [j])
    assert pipeline.load_seen(tmp_path / "state" / "seen.json") == {}


def test_legal_entities_fold_into_tracked_company_and_share_the_cap():
    raw = [job(company=f"Amazon Web Services, Inc.", title=f"Product Manager, Team {i}", url=f"a{i}",
               source="jobspy:linkedin") for i in range(4)]
    raw.append(job(company="Amazon", title="Product Manager, Team 0", url="direct", source="amazon"))
    jobs, dropped = pipeline.process(raw, cfg(priority_companies=["Amazon"], max_per_company=2), today=TODAY)
    assert [j.company for j in jobs] == ["Amazon", "Amazon"]
    assert any(j.url == "direct" for j in jobs)          # the employer's own listing wins
    assert dropped == {"duplicate": 1, "over the per-company limit": 2}


def test_require_min_needs_several_distinct_terms():
    raw = [job(company="One", url="a", description="Software delivery at scale."),
           job(company="Two", url="b", description="Clinical workflows for nursing teams.")]
    c = cfg(keywords={"require_any": ["delivery", "clinical", "nursing"], "require_min": 2})
    jobs, _ = pipeline.process(raw, c, today=TODAY)
    assert [j.company for j in jobs] == ["Two"]
