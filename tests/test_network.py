"""LinkedIn export -> network index -> company lookup."""
import csv

from jobhunt import cli, network

ME = "https://www.linkedin.com/in/me-myself"


def _csv(path, header, rows, preamble=""):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        f.write(preamble)
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def export(tmp_path):
    d = tmp_path / "Basic_LinkedInDataExport"
    _csv(d / "Connections.csv",
         ["First Name", "Last Name", "URL", "Email Address", "Company", "Position", "Connected On"],
         [["Ana", "Ruiz", "https://www.linkedin.com/in/ana-ruiz", "", "Optum", "Senior Product Manager", "01 Jan 2024"],
          ["Ben", "Cole", "https://www.linkedin.com/in/ben-cole", "", "UnitedHealth Group", "Recruiter", "02 Jan 2024"],
          ["Cy", "Diaz", "https://www.linkedin.com/in/cy-diaz", "", "Jobber", "Engineer", "03 Jan 2024"],
          ["Di", "Eng", "https://www.linkedin.com/in/di-eng", "", "Jobberwocky Labs", "PM", "04 Jan 2024"],
          ["", "", "", "", "Hidden Co", "", "05 Jan 2024"]],
         preamble='Notes:\n"Some emails are missing."\n\n')
    msg_cols = ["CONVERSATION ID", "FROM", "SENDER PROFILE URL", "TO", "RECIPIENT PROFILE URLS", "DATE", "CONTENT"]
    _csv(d / "messages.csv", msg_cols,
         [["1", "Me", ME, "Ana", "https://www.linkedin.com/in/ana-ruiz", "2025-03-01 10:00:00 UTC", "hi"],
          ["1", "Ana", "https://www.linkedin.com/in/ana-ruiz", "Me", ME, "2025-03-02 10:00:00 UTC", "hey"],
          ["2", "Me", ME, "Ben", "https://www.linkedin.com/in/ben-cole", "2024-06-01 10:00:00 UTC", "hello?"]])
    _csv(d / "Endorsement_Received_Info.csv",
         ["Endorsement Date", "Skill Name", "Endorser First Name", "Endorser Last Name", "Endorser Public Url", "Endorsement Status"],
         [["2025/01/01", "SQL", "Cy", "Diaz", "www.linkedin.com/in/cy-diaz", "ACCEPTED"]])
    _csv(d / "Recommendations_Received.csv",
         ["First Name", "Last Name", "Company", "Job Title", "Text", "Creation Date", "Status"],
         [["Ana", "Ruiz", "Optum", "PM", "Great PM", "04/13/26, 05:16 PM", "VISIBLE"]])
    _csv(d / "Invitations.csv",
         ["From", "To", "Sent At", "Message", "Direction", "inviterProfileUrl", "inviteeProfileUrl"],
         [["Me", "Fay Gu", "11/13/26, 10:35 PM", "Hi Fay, I applied for Jobber's Senior PM role.", "OUTGOING", ME,
           "https://www.linkedin.com/in/fay-gu"],
          ["Me", "Cy Diaz", "10/01/26, 9:00 AM", "", "OUTGOING", ME, "https://www.linkedin.com/in/cy-diaz"]])
    return d


def test_build_counts_warmth_and_pending(tmp_path):
    n = network.build(export(tmp_path), tmp_path / "private")
    assert n == {"connections": 4, "messaged": 2, "endorsed_or_recommended": 2, "pending": 1,
                 "folder": str(tmp_path / "private" / "network")}
    rows = {r["name"]: r for r in csv.DictReader((tmp_path / "private/network/contacts.csv").open(encoding="utf-8"))}
    assert rows["Ana Ruiz"]["messages"] == "2" and rows["Ana Ruiz"]["received"] == "1"
    assert rows["Ana Ruiz"]["last_message"] == "2025-03-02"
    assert rows["Ana Ruiz"]["recommended_you"] == "04/13/26"
    assert rows["Ben Cole"]["sent"] == "1" and rows["Ben Cole"]["received"] == "0"
    assert rows["Cy Diaz"]["endorsed_you"] == "yes"
    assert rows["Cy Diaz"]["invitation"] == "you invited them 10/01/26"   # accepted, so not pending


def test_find_uses_aliases_and_word_boundaries(tmp_path):
    home = tmp_path / "private"
    network.build(export(tmp_path), home)
    optum = network.find("Optum", home)
    assert [r["name"] for r in optum["contacts"]] == ["Ana Ruiz", "Ben Cole"]   # replied first
    jobber = network.find("Jobber", home)
    assert [r["name"] for r in jobber["contacts"]] == ["Cy Diaz"]               # not Jobberwocky
    assert [p["name"] for p in jobber["pending"]] == ["Fay Gu"]                 # named in the note
    custom = network.find("Wocky", home, aliases={"Wocky": ["jobberwocky"]})
    assert [r["name"] for r in custom["contacts"]] == ["Di Eng"]


def test_plain_flags_no_reply_and_empty(tmp_path):
    home = tmp_path / "private"
    network.build(export(tmp_path), home)
    text = network.plain(network.find("Optum", home))
    assert "recommended you" in text and "no reply" in text
    assert "nobody yet" in network.plain(network.find("Acme", home))


def test_cli_build_and_find(tmp_path, capsys):
    folder = export(tmp_path)
    home = tmp_path / "private"
    assert cli.main(["--home", str(home), "network", "build", str(folder)]) == 0
    assert "4 connections" in capsys.readouterr().out
    assert cli.main(["--home", str(home), "network", "find", "Optum", "Jobber"]) == 0
    out = capsys.readouterr().out
    assert "Optum: 2 connection(s)" in out and "Jobber: 1 connection(s)" in out
    assert cli.main(["--home", str(home), "network", "find"]) == 2


def test_cli_find_before_build(tmp_path, capsys):
    assert cli.main(["--home", str(tmp_path / "private"), "network", "find", "Optum"]) == 2
    assert "file not found" in capsys.readouterr().out
