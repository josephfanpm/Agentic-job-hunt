"""Pick checkbox, `jobhunt picks`, the who-you-know column, and the email setting."""
import datetime as dt
import json

from jobhunt import cli, config, network, sheet, tracker, webhook
from jobhunt.models import Job
from tests.test_network import export

TODAY = dt.date(2026, 11, 18)


def cfg(**over):
    c = config._merge(config.DEFAULTS, {"titles": {"include": ["product manager"]}})
    return config._merge(c, over)


def job(company="Optum", title="Senior Product Manager", **kw):
    return Job(source="greenhouse", company=company, title=title, url=f"https://jobs.example/{company}", **kw)


class Resp:
    def __init__(self, body): self.body = body
    def read(self): return self.body
    def __enter__(self): return self
    def __exit__(self, *a): return False


def test_schema_puts_pick_first_and_adds_who_you_know():
    names = [c["name"] for c in sheet.columns("Daily jobs")]
    assert names[:2] == ["Pick", "Applied"] and "Who you know" in names
    v = sheet.job_values(job(known="Ana Ruiz (warm)"), 1, cfg(), TODAY)
    assert v["Pick"] is False and v["Who you know"] == "Ana Ruiz (warm)"


def test_summary_marks_warm_contacts_and_pending(tmp_path):
    home = tmp_path / "private"
    assert network.summary("Optum", home) == ""                    # no index yet
    network.build(export(tmp_path), home)
    assert network.summary("Optum", home) == "Ana Ruiz (warm), Ben Cole"
    assert network.summary("Optum", home, limit=1) == "Ana Ruiz (warm), +1 more"
    assert network.summary("Jobber", home) == "Cy Diaz (warm); 1 invitation not accepted"
    assert network.summary("Acme", home) == ""


def test_csv_picks_only_ticked_and_unapplied(tmp_path):
    tracker.add_jobs(tmp_path, [job("A"), job("B"), job("C"), job("D")], cfg(), TODAY)
    rows = tracker.read(tmp_path, "Daily jobs")
    rows[0]["Pick"] = "TRUE"
    rows[1]["Pick"] = "x"                          # typed by hand in Excel
    rows[2]["Pick"], rows[2]["Applied"] = "TRUE", "TRUE"
    tracker.write(tmp_path, "Daily jobs", rows)
    assert [r["Company"] for r in tracker.picks(tmp_path)] == ["A", "B"]


def test_cli_picks_csv(tmp_path, capsys):
    home = tmp_path / "private"
    home.mkdir()
    (home / "config.json").write_text(json.dumps({"titles": {"include": ["pm"]}, "tracker": "csv"}))
    assert cli.main(["--home", str(home), "picks"]) == 0
    assert "No picks yet" in capsys.readouterr().out
    tracker.add_jobs(home, [job("Acme", "Senior PM")], cfg(), TODAY)
    rows = tracker.read(home, "Daily jobs")
    rows[0]["Pick"] = "TRUE"
    tracker.write(home, "Daily jobs", rows)
    (home / "jds").mkdir()
    (home / "jds" / "Acme__Senior_PM.txt").write_text("Senior PM\nAcme\nhttps://x\n\nJD")
    assert cli.main(["--home", str(home), "picks"]) == 0
    out = capsys.readouterr().out
    assert "1. Acme — Senior PM  [to do]" in out and "Acme__Senior_PM.txt" in out
    assert cli.main(["--home", str(home), "picks", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)[0]["Company"] == "Acme"


def test_cli_picks_sheet_without_receiver(tmp_path, capsys):
    home = tmp_path / "private"
    home.mkdir()
    (home / "config.json").write_text(json.dumps({"titles": {"include": ["pm"]}, "tracker": "sheet"}))
    assert cli.main(["--home", str(home), "picks"]) == 2
    assert "Pick ticked" in capsys.readouterr().out


def test_webhook_picks_and_email_flag(monkeypatch):
    sent = []

    def fake(req, timeout):
        body = json.loads(req.data)
        sent.append(body)
        if body.get("action") == "picks":
            return Resp(b'{"ok": true, "picks": [{"Company": "Acme", "Role": "PM"}]}')
        return Resp(b'{"ok": true, "added": 1, "emailed": 1}')

    monkeypatch.setattr(webhook.urllib.request, "urlopen", fake)
    assert webhook.picks("https://x/exec", "t") == [{"Company": "Acme", "Role": "PM"}]
    assert sent[0] == {"token": "t", "action": "picks"}
    webhook.send("https://x/exec", "t", [], email=True, email_top=5)
    assert sent[1]["email"] is True and sent[1]["email_top"] == 5
    assert config.DEFAULTS["email_digest"] is False      # opt-in
