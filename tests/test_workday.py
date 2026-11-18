"""Workday careers sites: URL parsing, paging, title filter, details, categories. No network."""
import datetime as dt
import json

import pytest

from jobhunt import cli, config, net, pipeline
from jobhunt.sources import workday

TODAY = dt.date(2026, 11, 18)
URL = "https://acme.wd5.myworkdayjobs.com/AcmeCareers"


def cfg(**over):
    c = config._merge(config.DEFAULTS, {
        "titles": {"include": ["product manager"], "exclude": ["director"]},
        "locations": {"countries": ["US", "CA"]},
        "max_age_days": 7,
    })
    return config._merge(c, over)


def posting(title, days, n):
    when = "Posted Today" if days == 0 else "Posted Yesterday" if days == 1 else (
        "Posted 30+ Days Ago" if days >= 30 else f"Posted {days} Days Ago")
    return {"title": title, "externalPath": f"/job/Austin-TX/{title.replace(' ', '-')}_R{n}",
            "locationsText": "Austin, TX", "postedOn": when, "bulletFields": [f"R{n}"]}


def detail(p, remote="Hybrid"):
    return {"jobPostingInfo": {
        "title": p["title"], "jobDescription": "<p>Build our marketplace. $140,000 - $170,000</p>",
        "location": "Austin, TX", "startDate": "2026-11-17", "remoteType": remote,
        "jobReqId": p["bulletFields"][0], "jobRequisitionLocation": {"country": {"alpha2Code": "US"}},
        "externalUrl": f"{URL}{p['externalPath']}"},
        "hiringOrganization": {"name": "Acme Holdings, Inc."}}


class FakeSite:
    """Serves search pages and postings like a Workday site; records what was asked."""

    def __init__(self, postings, facets=None, fail_details=()):
        self.postings, self.facets, self.fail = postings, facets or [], set(fail_details)
        self.searches, self.details = [], []

    def __call__(self, url, data=None, **kw):
        if url.endswith("/jobs"):
            body = json.loads(data)
            self.searches.append(body)
            rows = self.postings
            if body["appliedFacets"]:
                rows = [p for p in rows if "Manager" in p["title"]]
            page = rows[body["offset"]:body["offset"] + body["limit"]]
            return json.dumps({"total": len(rows), "jobPostings": page, "facets": self.facets}).encode()
        path = url.split("/AcmeCareers", 1)[1]
        self.details.append(path)
        if path in self.fail:
            raise net.FetchError(f"{url}: HTTP 429")
        p = next(p for p in self.postings if p["externalPath"] == path)
        return json.dumps(detail(p)).encode()


@pytest.mark.parametrize("raw,site,prefix", [
    ("https://acme.wd5.myworkdayjobs.com/AcmeCareers", "AcmeCareers", "/AcmeCareers"),
    ("acme.wd5.myworkdayjobs.com/en-US/AcmeCareers/job/Austin/PM_R1", "AcmeCareers", "/AcmeCareers"),
    ("https://wd3.myworkdaysite.com/recruiting/acme/External", "External", "/recruiting/acme/External"),
])
def test_parse_site(raw, site, prefix):
    s = workday.parse_site(raw)
    assert s["site"] == site and s["prefix"] == prefix
    assert s["tenant"] == "acme"


def test_parse_site_rejects_other_urls():
    with pytest.raises(workday.WorkdayURLError):
        workday.parse_site("https://boards.greenhouse.io/acme")
    assert workday.is_workday_url(URL) and not workday.is_workday_url("Acme")


def test_posted_days():
    assert [workday.posted_days(t) for t in ("Posted Today", "Posted Yesterday", "Posted 4 Days Ago",
                                              "Posted 30+ Days Ago", "")] == [0, 1, 4, 30, None]


def test_fetch_filters_titles_before_loading_postings():
    site = FakeSite([posting("Pharmacy Technician", 0, 1), posting("Senior Product Manager", 0, 2),
                     posting("Director, Product Manager", 0, 3), posting("Product Manager", 1, 4)])
    jobs = workday.fetch({"url": URL, "name": "Acme"}, cfg(), site, TODAY, pause=0)
    assert [j.title for j in jobs] == ["Senior Product Manager", "Product Manager"]
    assert len(site.details) == 2          # only the matching titles were opened
    j = jobs[0]
    assert j.source == "workday" and j.company == "Acme" and j.country == "US" and j.remote is None
    assert j.posted == "2026-11-17" and j.url == f"{URL}/job/Austin-TX/Senior-Product-Manager_R2"
    assert site.searches[0]["searchText"] == "product manager"


def test_fetch_stops_paging_on_a_newest_first_site():
    rows = [posting("Product Manager", 0, i) for i in range(20)] + \
           [posting("Product Manager", 30, 100 + i) for i in range(60)]
    site = FakeSite(rows)
    workday.fetch({"url": URL}, cfg(), site, TODAY, pause=0)
    assert len(site.searches) == 2         # page 2 was all too old, so pages 3-4 were skipped


def test_fetch_keeps_paging_on_a_relevance_sorted_site():
    rows = [posting("Product Manager", 30 if i % 2 else 2, i) for i in range(20)] + \
           [posting("Product Manager", 30, 100 + i) for i in range(20)] + \
           [posting("Senior Product Manager", 3, 200)]
    site = FakeSite(rows)
    jobs = workday.fetch({"url": URL, "max_details": 50}, cfg(), site, TODAY, pause=0)
    assert len(site.searches) == 3 and "Senior Product Manager" in [j.title for j in jobs]


def test_priority_company_keeps_old_postings():
    site = FakeSite([posting("Product Manager", 30, 1)])
    jobs = workday.fetch({"url": URL, "name": "Acme"}, cfg(priority_companies=["Acme"]), site, TODAY, pause=0)
    assert len(jobs) == 1


def test_a_posting_that_wont_load_falls_back_to_the_listing():
    rows = [posting("Product Manager", 0, 1), posting("Senior Product Manager", 2, 2)]
    site = FakeSite(rows, fail_details={rows[0]["externalPath"]})
    jobs = workday.fetch({"url": URL, "name": "Acme"}, cfg(), site, TODAY, pause=0)
    assert len(jobs) == 2
    assert jobs[0].flags == ["description not loaded"] and jobs[0].posted == "2026-11-18"
    assert jobs[0].location == "Austin, TX" and jobs[1].flags == []


def test_categories_filter_the_search():
    facets = [{"facetParameter": "jobFamilyGroup", "descriptor": "Job Category", "values": [
        {"descriptor": "Product, Marketing, and Advtsg", "id": "p1", "count": 61},
        {"descriptor": "Retail Store & Pharmacy", "id": "r1", "count": 11787}]}]
    site = FakeSite([posting("Pharmacy Technician", 0, 1), posting("Product Manager", 0, 2)], facets)
    workday.fetch({"url": URL, "categories": ["product"]}, cfg(), site, TODAY, pause=0)
    assert site.searches[-1]["appliedFacets"] == {"jobFamilyGroup": ["p1"]}
    with pytest.raises(ValueError, match="Retail Store"):
        workday.fetch({"url": URL, "categories": ["nursing"]}, cfg(), site, TODAY, pause=0)


def test_scan_runs_workday_boards(tmp_path):
    site = FakeSite([posting("Senior Product Manager", 0, 1)])
    c = cfg(companies={"workday": [{"url": URL, "name": "Acme"}]},
            sources={"remoteok": False, "remotive": False, "himalayas": False, "hackernews": False})
    res = pipeline.run(c, home=tmp_path, get=site, today=TODAY, remember=False)
    assert res.stats == {"workday:acme/AcmeCareers": 1}
    assert [j.title for j in res.jobs] == ["Senior Product Manager"] and res.jobs[0].pay


def test_boards_add_workday_url(tmp_path, monkeypatch, capsys):
    facets = [{"facetParameter": "jobFamilyGroup", "descriptor": "Job Category",
               "values": [{"descriptor": "Technology", "id": "t1", "count": 137}]}]
    monkeypatch.setattr(net, "get", FakeSite([posting("Product Manager", 0, 1)], facets))
    home = tmp_path / "private"
    home.mkdir()
    assert cli.main(["--home", str(home), "boards", "add", URL + "/job/x", "--name", "Acme"]) == 0
    assert cli.main(["--home", str(home), "boards", "add", URL, "--name", "Acme"]) == 0
    out = capsys.readouterr().out
    assert "Acme: workday" in out and "Technology (137)" in out and "already tracked" in out
    saved = json.loads((home / "config.json").read_text(encoding="utf-8"))
    assert saved["companies"]["workday"] == [{"url": URL, "name": "Acme"}]
