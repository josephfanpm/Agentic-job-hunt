"""People search, sheet requests, CSV tracker, ATS check, keywords, setup, CLI."""
import datetime as dt
import json
import re
import urllib.parse

import pytest

from jobhunt import cli, config, discover, keywords, people, sheet, tracker, wizard
from jobhunt.models import Job

TODAY = dt.date(2026, 11, 15)


def cfg(**over):
    c = config._merge(config.DEFAULTS, {"titles": {"include": ["product manager"]}})
    return config._merge(c, over)


def job(**kw):
    base = dict(source="ashby", company="Jobber", title="Senior Product Manager, New Starts",
                url="https://jobs.example/1", location="Toronto, ON", posted="2026-11-13",
                pay="CAD 145,900–197,400", why="Matches onboarding.", job_id="b47c", score=60)
    base.update(kw)
    return Job(**base)


# ---- people ------------------------------------------------------------------
def _bare_or(query: str) -> bool:
    """True if an OR sits outside parentheses."""
    depth = 0
    for tok in re.findall(r"\(|\)|\bOR\b", query):
        depth += tok == "("
        depth -= tok == ")"
        if tok == "OR" and depth == 0:
            return True
    return False


def test_every_or_group_is_parenthesised_and_links_round_trip():
    rows = people.searches(["Joist", "EverPro"], team=["care navigation", "AI"], big=True)
    assert [r[0] for r in rows] == ["Recruiters", "Hiring managers", "Peers"]
    for _, q, url in rows:
        assert not _bare_or(q)
        assert urllib.parse.unquote(url.split("keywords=")[1]) == q
    assert rows[0][1] == ('(recruiter OR "talent acquisition" OR sourcer) AND '
                          '(product OR tech OR technical) AND (Joist OR EverPro)')
    assert rows[2][1] == '"product manager" AND (Joist OR EverPro) AND ("care navigation" OR AI)'


@pytest.mark.parametrize("peer,expected", [
    ("product manager", "director of product"), ("software engineer", "director of engineering"),
    ("data scientist", "data science manager"), ("product designer", "head of design"),
    ("registered nurse", "registered nurse manager"),
])
def test_manager_titles_fit_the_function(peer, expected):
    assert expected in people.manager_titles([peer])


def test_team_terms_and_job_search_use_config():
    assert people.team_terms("Sr. Product Manager, Seller Onboarding Risk", ["product manager"]) == [
        "seller", "onboarding", "risk"]
    assert people.team_terms("Product Manager II", ["product manager"]) == []
    rows = people.for_job("CVS Health", "Product Manager, Care Navigation",
                          cfg(big_companies=["CVS Health"], linkedin={"manager_titles": ["VP product"]}))
    assert '(product OR tech OR technical) AND "CVS Health"' in rows[0][1]
    assert rows[1][1] == '"VP product" AND "CVS Health" AND (care OR navigation)'


def test_sheet_cell_link_runs_start_at_each_line():
    rows = people.searches("DoorDash", team=["merchant"])
    cell = people.cell(rows)
    text = cell["userEnteredValue"]["stringValue"]
    starts = [0] + [m.end() for m in re.finditer("\n", text)]
    assert [r["startIndex"] for r in cell["textFormatRuns"]] == starts
    assert text.count("\n") == 2 and not text.endswith("\n")


# ---- sheet -------------------------------------------------------------------
def test_create_requests_cover_every_tab_and_drop_sheet1():
    schema = sheet.load_schema()
    reqs = sheet.create_requests(rows=20)
    added = [r["addSheet"]["properties"] for r in reqs if "addSheet" in r]
    assert [a["title"] for a in added] == [t["name"] for t in schema["tabs"]]
    assert [a["sheetId"] for a in added] == [1, 2, 3]
    assert reqs[-1] == {"deleteSheet": {"sheetId": 0}}
    formulas = [r for r in reqs if "updateCells" in r and "formulaValue" in json.dumps(r)]
    assert formulas and formulas[0]["updateCells"]["rows"][0]["values"][0][
        "userEnteredValue"]["formulaValue"] == '=IF(L2="","",L2+7)'


def test_row_requests_insert_under_the_header_in_schema_order():
    jobs = [job(), job(company="Acme", title="Product Manager", url='https://x/"q"', pay="")]
    reqs = sheet.row_requests(jobs, cfg(), TODAY)
    ins, upd = reqs[0]["insertDimension"], reqs[1]["updateCells"]
    assert ins["range"] == {"sheetId": 1, "dimension": "ROWS", "startIndex": 1, "endIndex": 3}
    assert ins["inheritFromBefore"] is False and upd["start"]["rowIndex"] == 1
    names = [c["name"] for c in sheet.columns("Daily jobs")]
    first = dict(zip(names, upd["rows"][0]["values"]))
    assert len(upd["rows"][0]["values"]) == len(names)
    assert first["Applied"]["userEnteredValue"] == {"boolValue": False}
    assert first["Applied"]["dataValidation"]["condition"]["type"] == "BOOLEAN"
    assert first["Rank"]["userEnteredValue"] == {"numberValue": 1}
    assert first["Company"]["userEnteredValue"] == {"stringValue": "Jobber"}
    assert first["Link"]["userEnteredValue"]["formulaValue"] == '=HYPERLINK("https://jobs.example/1","Open")'
    assert first["Notes"]["userEnteredValue"]["stringValue"] == "via ashby · ID b47c"
    assert len(first["LinkedIn search"]["textFormatRuns"]) == 3
    second = dict(zip(names, upd["rows"][1]["values"]))
    assert '"q"' not in second["Link"]["userEnteredValue"]["formulaValue"]
    assert sheet.row_requests([], cfg()) == []


# ---- CSV tracker -------------------------------------------------------------
def test_tracker_round_trip(tmp_path):
    assert len(tracker.init(tmp_path)) == 3 and tracker.init(tmp_path) == []
    tracker.add_jobs(tmp_path, [job(company="Old Co")], cfg(), TODAY - dt.timedelta(days=1))
    tracker.add_jobs(tmp_path, [job(), job(company="Acme", title="Product Manager")], cfg(), TODAY)
    rows = tracker.read(tmp_path, "Daily jobs")
    assert [r["Company"] for r in rows] == ["Jobber", "Acme", "Old Co"]   # newest on top
    assert rows[0]["Applied"] == "FALSE" and rows[0]["LinkedIn search"].count("https://") == 3

    assert [r["Company"] for r in tracker.find_job(tmp_path, "jobb")] == ["Jobber"]
    row = tracker.mark_applied(tmp_path, "jobber", "Sr Product Manager, New Starts",
                               channel="Referral", today=TODAY)
    assert row["Follow up on"] == "2026-11-22" and row["Pay"] == "CAD 145,900–197,400"
    assert tracker.read(tmp_path, "Daily jobs")[0]["Applied"] == "TRUE"
    with pytest.raises(ValueError):
        tracker.mark_applied(tmp_path, "Jobber", "Senior Product Manager, New Starts", today=TODAY)

    assert tracker.due(tmp_path, TODAY) == []
    assert [d["who"] for d in tracker.due(tmp_path, dt.date(2026, 11, 22))] == [
        "jobber — Sr Product Manager, New Starts"]
    tracker.mark_applied(tmp_path, "Acme", "Product Manager", today=TODAY)
    applied = tracker.read(tmp_path, "Applied")
    applied[0]["Status"] = "Interviewing"
    tracker.write(tmp_path, "Applied", applied)
    stats = {s["channel"]: s for s in tracker.channel_stats(tmp_path)}
    assert stats["Cold application"]["interviews"] == 1 and stats["Referral"]["interviews"] == 0


def test_network_follow_ups(tmp_path):
    tracker.init(tmp_path)
    tracker.write(tmp_path, "Network", [
        {"Name": "Ada", "Company": "Acme", "Status": "Messaged", "Messaged on": "2026-11-01"},
        {"Name": "Bo", "Company": "Acme", "Status": "Replied", "Messaged on": "2026-11-01"}])
    assert [d["who"] for d in tracker.due(tmp_path, TODAY)] == ["Ada (Acme)"]


# ---- ATS check ---------------------------------------------------------------
pymupdf = pytest.importorskip("pymupdf")
from jobhunt import ats  # noqa: E402

GOOD = ["Ada Lovelace", "555-555-5555 | ada@example.com | linkedin.com/in/ada", "", "Experience",
        "Senior Product Manager", "Jan 2022 – Present",
        "Launched a marketplace that grew weekly bookings 40% with A/B tests and SQL analysis",
        "Led onboarding redesign that raised activation from 20% to 31% across three markets",
        "Built an experimentation practice used by four product teams every single week",
        "Education", "MBA, Example University", "2019"]


def make_pdf(path, lines, pages=1, columns=False):
    doc = pymupdf.open()
    for _ in range(pages):
        page = doc.new_page()
        y = 72
        for ln in lines:
            if ln:
                page.insert_text((72, y), ln, fontsize=10)
            y += 16
        if columns:
            for i, ln in enumerate(["Skills", "Python and SQL daily", "Figma for prototypes"] * 3):
                page.insert_text((380, 72 + 16 * i), ln, fontsize=10)
    doc.save(path)
    return path


def test_good_resume_passes(tmp_path):
    rep = ats.check(make_pdf(tmp_path / "ok.pdf", GOOD))
    assert rep.ok and rep.warnings == [], ats.render(rep)


def test_failures_are_caught(tmp_path):
    two = ats.check(make_pdf(tmp_path / "two.pdf", GOOD, pages=2))
    assert any("2 pages" in f for f in two.fails)
    assert any("fused letters" in f for f in ats.text_fails("Staﬀed the oﬃce"))
    assert any("unreadable" in f for f in ats.text_fails("�" * 5))
    assert ats.text_fails("Staffed the office") == []
    blank = ats.check(make_pdf(tmp_path / "blank.pdf", ["Hi"]))
    assert any("almost no selectable text" in f for f in blank.fails)
    no_mail = ats.check(make_pdf(tmp_path / "nomail.pdf", [ln.replace("ada@example.com", "") for ln in GOOD]))
    assert any("no email" in f for f in no_mail.fails)


def test_structure_warnings_and_letter_mode(tmp_path):
    bare = [ln for ln in GOOD if ln not in ("Experience", "Education", "Jan 2022 – Present")]
    rep = ats.check(make_pdf(tmp_path / "bare.pdf", bare))
    assert rep.ok and len([w for w in rep.warnings if "heading" in w]) == 2
    assert any("date ranges" in w for w in rep.warnings)
    assert ats.check(tmp_path / "bare.pdf", letter=True).warnings == []
    cols = ats.check(make_pdf(tmp_path / "cols.pdf", GOOD, columns=True))
    assert any("out of reading order" in w for w in cols.warnings)


def test_short_wrap_is_flagged(tmp_path):
    doc = pymupdf.open()
    page = doc.new_page()
    y = 72
    for ln in GOOD[:6]:
        if ln:
            page.insert_text((72, y), ln, fontsize=10)
        y += 16
    page.insert_textbox(pymupdf.Rect(72, y, 300, y + 60), "Launched a marketplace that grew weekly "
                        "bookings by forty percent using careful tests and analysis here ok", fontsize=10)
    doc.save(tmp_path / "wrap.pdf")
    rep = ats.check(tmp_path / "wrap.pdf")
    assert any("line wraps with only" in f for f in rep.fails), ats.render(rep)


def test_keyword_report_in_check(tmp_path):
    jd = ("We need SQL and experimentation skills. You will run experimentation programs, own the "
          "pricing roadmap and the pricing strategy. Kubernetes experience helps; Kubernetes is core.")
    rep = ats.check(make_pdf(tmp_path / "ok.pdf", GOOD), jd_text=jd)
    k = rep.keywords
    assert "SQL" in k["covered"] and "experimentation" in k["covered"]
    assert "kubernetes" in [m.lower() for m in k["missing"]] and "pricing" in " ".join(k["missing"])
    assert "not in resume" in ats.render(rep)


# ---- keywords ----------------------------------------------------------------
def test_extract_terms_skips_filler_boilerplate_and_company():
    jd = ("Acme builds a marketplace. Acme wants marketplace growth. You have strong experience with "
          "A/B testing; A/B testing matters. We offer dental insurance, dental coverage and growth stipends.")
    terms = keywords.extract_terms(jd, ignore=("Acme",))
    low = [t.lower() for t in terms]
    assert "marketplace" in low and "a/b" in " ".join(low)
    assert not {"acme", "dental", "experience", "strong"} & set(low)


def test_coverage_matches_plurals():
    out = keywords.coverage("Run experiments. More experiments. Own dashboards and dashboards.",
                            "I ran an experiment and built a dashboard")
    assert out["missing"] == [] and out["percent"] == 100


# ---- setup -------------------------------------------------------------------
RESUME = """Ada Lovelace
555-555-5555 | ada@example.com | linkedin.com/in/ada | github.com/ada

Experience
Senior Product Manager
Acme, Toronto
Education
MBA, Example University
Skills
SQL, Figma
"""


def test_wizard_builds_profile_config_and_tracker(tmp_path):
    resume = tmp_path / "cv.txt"
    resume.write_text(RESUME, encoding="utf-8")
    home = tmp_path / "private"
    answers = {"titles": ["product manager"], "exclude": ["intern"], "boost": ["health"],
               "countries": ["us", "ca"], "pay_floor": 101000.0, "priority": ["Acme"]}
    done = wizard.run(answers, home=home, resume=resume, find_boards=False, log=lambda *_: None)
    profile = (home / "profile.md").read_text(encoding="utf-8")
    assert "- Name: Ada Lovelace" in profile and "- Email: ada@example.com" in profile
    assert "- LinkedIn: linkedin.com/in/ada" in profile and "- Pay floor: 101,000" in profile
    assert "Senior Product Manager\nAcme, Toronto" in profile and "SQL, Figma" in profile
    c = config.load(home / "config.json")
    assert c["titles"]["include"] == ["product manager"] and c["locations"]["countries"] == ["US", "CA"]
    assert c["mode"] == "lean" and c["priority_companies"] == ["Acme"]
    assert c["sources"]["remoteok"] is True          # defaults still apply
    assert (home / "tracker" / "applied.csv").exists() and len(done["created"]) >= 5

    (home / "profile.md").write_text("mine", encoding="utf-8")
    again = wizard.run({"titles": ["engineer"]}, home=home, find_boards=False)
    assert (home / "profile.md").read_text(encoding="utf-8") == "mine"
    assert config.load(home / "config.json")["titles"]["include"] == ["product manager"]
    assert len(again["kept"]) == 2


def test_config_validation(tmp_path):
    assert any("titles" in m for m in config.problems(config.load(tmp_path / "none.json")))
    (tmp_path / "bad.json").write_text('{"mode": "turbo"}', encoding="utf-8")
    with pytest.raises(ValueError):
        config.load(tmp_path / "bad.json")


# ---- board discovery ---------------------------------------------------------
def test_slug_candidates_and_find():
    assert discover.slug_candidates("Hugging Face")[:3] == ["huggingface", "hugging-face", "hugging"]
    assert "doordashusa" in discover.slug_candidates("DoorDash")

    def get(url, **kw):
        if "greenhouse.io/v1/boards/doordashusa/" in url:
            return json.dumps({"jobs": [{"id": 1, "title": "Account Executive", "absolute_url": "u",
                                         "company_name": "DoorDash USA"}]}).encode()
        raise discover.net.FetchError("HTTP 404")

    hits = discover.find("DoorDash", get=get)
    assert [(h["ats"], h["slug"], h["jobs"]) for h in hits] == [("greenhouse", "doordashusa", 1)]
    user = {}
    assert discover.add_to_config(user, "DoorDash", hits[0]) is True
    assert discover.add_to_config(user, "DoorDash", hits[0]) is False
    assert user == {"companies": {"greenhouse": [{"slug": "doordashusa", "name": "DoorDash"}]}}


# ---- CLI ---------------------------------------------------------------------
def test_cli_mode_people_and_guards(tmp_path, capsys):
    home = str(tmp_path)
    assert cli.main(["--home", home, "init", "--titles", "product manager", "--no-boards"]) == 0
    assert cli.main(["--home", home, "mode", "standard"]) == 0
    assert config.load(tmp_path / "config.json")["mode"] == "standard"
    capsys.readouterr()
    assert cli.main(["--home", home, "people", "Jobber", "Senior Product Manager, New Starts"]) == 0
    out = capsys.readouterr().out
    assert out.count("https://www.linkedin.com/search/results/people/") == 3
    assert cli.main(["--home", home, "due"]) == 0
    assert cli.main(["--home", home, "applied", "Nobody"]) == 2
    empty = tmp_path / "empty"
    assert cli.main(["--home", str(empty), "scan"]) == 2        # no titles configured
    assert "cannot scan" in capsys.readouterr().out
