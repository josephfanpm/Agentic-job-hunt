"""The parts of auto-apply that need no browser: the answer bank, code emails, site rules."""
from jobhunt.apply import answers as bank
from jobhunt.apply import forms, mailcode, run

BANK = [
    {"is": ["name", "full name"], "answer": "Ada Lovelace"},
    {"is": ["first name"], "answer": "Ada"},
    {"ask": ["linkedin"], "answer": "https://www.linkedin.com/in/example"},
    {"ask": ["authorized to work", "united states"], "answer": "Yes"},
    {"ask": ["sponsorship"], "country": "US", "answer": "Yes", "text": "TN eligible."},
    {"ask": ["sponsorship"], "country": "CA", "answer": "No"},
    {"ask": ["gender"], "not": ["transgender"], "answer": ["Decline", "Prefer not"]},
    {"ask": ["disability"], "answer": ["No, I do not have a disability", "No"]},
    {"ask": ["race"], "answer": ["Asian"]},
]


def test_norm_spells_out_the_country_but_leaves_the_word_us():
    assert bank.norm("Are you a US Citizen?*") == "are you a united states citizen?"
    assert bank.norm("Authorized to work in the U.S.?") == "authorized to work in the united states?"
    assert bank.norm("Why us?") == "why us?"


def test_exact_label_beats_a_phrase_match():
    assert bank.resolve("First Name*", BANK)[0] == "Ada"
    assert bank.resolve("Name", BANK)[0] == "Ada Lovelace"
    assert bank.resolve("Company name", BANK)[0] is None


def test_unknown_question_has_no_answer():
    assert bank.resolve("How many years have you managed a team?", BANK) == (None, None)


def test_country_answers_need_the_jobs_country():
    q = "Will you now or in the future require sponsorship?"
    assert bank.resolve(q, BANK, ["Yes", "No"])[0] is None
    assert bank.resolve(q, BANK, ["Yes", "No"], country="US")[0] == ["Yes"]
    assert bank.resolve(q, BANK, ["Yes", "No"], country="CA")[0] == ["No"]
    assert bank.resolve(q, BANK, country="US")[0] == "TN eligible."


def test_question_about_this_roles_country_uses_the_jobs_country():
    q = "Are you authorized to work in the country this role is listed in?"
    assert bank.resolve(q, BANK, ["Yes", "No"], country="US")[0] == ["Yes"]
    assert bank.resolve(q, BANK, ["Yes", "No"], country="CA")[0] is None


def test_choice_answers_map_to_the_forms_wording():
    opts = ["Yes, I have a disability", "No, I do not have a disability and have not had one in the past", "I don't want to answer"]
    assert bank.resolve("Disability", BANK, opts)[0] == [opts[1]]
    assert bank.resolve("Gender", BANK, ["Male", "Female", "Decline To Self Identify"])[0] == ["Decline To Self Identify"]
    assert bank.resolve("I identify as transgender", BANK, ["Yes", "No"])[0] is None


def test_ambiguous_options_are_not_guessed():
    assert bank.choose("No", ["No, I am not a veteran", "No, I do not have a disability"]) == []
    assert bank.choose("Asian", ["East Asian", "South Asian", "White"]) == []
    assert bank.choose("Asian", ["Asian (not Hispanic or Latino)", "White"]) == ["Asian (not Hispanic or Latino)"]
    assert bank.choose("Yes", ["Yes", "No"]) == ["Yes"]


def test_job_answers_come_before_the_bank():
    job = forms.job_entries({"why do you want to work": "Because of the nurses."})
    assert bank.resolve("Why do you want to work at Example?", job)[0] == "Because of the nurses."


def test_pending_questions_are_saved_once_and_answered(tmp_path, monkeypatch):
    monkeypatch.setenv("JOBHUNT_HOME", str(tmp_path))
    bank.add_pending("Do you have a driver's licence?*", ["Yes", "No"], "Example", "https://example.com/1")
    bank.add_pending("Do you have a driver's licence?", ["Yes", "No"], "Other Co", "https://example.com/2")
    items = bank.load_pending()
    assert len(items) == 1 and items[0]["companies"] == ["Example", "Other Co"]
    bank.answer_pending(1, "Yes")
    assert bank.load_pending() == []
    assert bank.resolve("Do you have a driver's licence?", bank.load(), ["Yes", "No"])[0] == ["Yes"]


def test_code_is_read_from_an_email():
    body = "Hi Ada,\n\nCopy and paste this code into the security code field on your application:\n\nxK9mP2qL\n\nThanks"
    assert mailcode.extract_code(body) == "xK9mP2qL"
    assert mailcode.extract_code("Your verification code is 482913. It expires in 10 minutes.") == "482913"
    html = "<html><style>p{color:#123456}</style><p>Your security code:</p><h1>Zt4kQ9wX</h1><p>Thanks</p></html>"
    assert mailcode.extract_code(mailcode.html_to_text(html)) == "Zt4kQ9wX"


def test_no_code_is_better_than_a_wrong_one():
    assert mailcode.extract_code("Hello\nThanks\nRegards") is None
    assert mailcode.extract_code("Order 482913 shipped. Order 771204 is delayed.") is None


def test_site_rules():
    assert run.site_for("https://job-boards.greenhouse.io/acme/jobs/1")[0] == "greenhouse"
    assert run.site_for("https://www.amazon.jobs/en/jobs/1/pm")[0] == "amazon"
    assert run.site_for("https://careers.example.com/jobs/1")[0] == "other"
    name, site = run.site_for("https://jobs.lever.co/acme/abc")
    assert run.form_url("https://jobs.lever.co/acme/abc", site) == "https://jobs.lever.co/acme/abc/apply"
    assert run.form_url("https://jobs.lever.co/acme/abc/apply", site) == "https://jobs.lever.co/acme/abc/apply"
    _, ashby = run.site_for("https://jobs.ashbyhq.com/acme/abc?utm=x")
    assert run.form_url("https://jobs.ashbyhq.com/acme/abc?utm=x", ashby) == "https://jobs.ashbyhq.com/acme/abc/application?utm=x"


def test_agreements_the_tool_must_not_accept():
    assert any(w in "i agree to binding arbitration of disputes" for w in forms.AGREEMENT_STOP)
