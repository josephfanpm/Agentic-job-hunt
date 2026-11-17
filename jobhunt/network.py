"""Your LinkedIn network, from LinkedIn's data export: who you know at a company.

`build` reads the export folder once and writes private/network/:
  contacts.csv  one row per connection, with how warm they are
  pending.csv   invitations nobody has accepted yet

`find` looks up a company in contacts.csv and pending.csv. It needs no AI.
"""
from __future__ import annotations

import csv
import io
import re
from collections import Counter
from pathlib import Path

CONTACT_COLS = ["name", "company", "position", "url", "connected_on", "messages", "sent", "received",
                "last_message", "endorsed_you", "you_endorsed", "recommended_you", "you_recommended",
                "invitation"]
PENDING_COLS = ["direction", "name", "url", "sent", "note"]

# Company names that differ from what people write on their profile
ALIASES = {
    "optum": ["optum", "unitedhealth", "unitedhealthcare"],
    "unitedhealth group": ["optum", "unitedhealth", "unitedhealthcare"],
    "cvs health": ["cvs", "aetna"],
    "aetna": ["aetna", "cvs"],
    "elevance health": ["elevance", "anthem", "carelon"],
    "twitch": ["twitch", "amazon"],
    "aws": ["aws", "amazon web services", "amazon"],
    "google": ["google", "youtube", "alphabet"],
    "youtube": ["youtube", "google"],
    "meta": ["meta", "facebook", "instagram"],
}
_STOP = {"inc", "llc", "ltd", "corp", "corporation", "co", "company", "the", "group", "plc",
         "health", "healthcare", "technologies", "technology", "labs"}


def _slug(url: str) -> str:
    m = re.search(r"linkedin\.com/in/([^/?#\s]+)", url or "")
    return m.group(1).lower() if m else ""


def _read(folder: Path, name: str) -> list[dict]:
    """Read one export CSV. Connections.csv starts with a few lines of notes."""
    path = next((p for p in folder.rglob(name)), None)
    if not path:
        return []
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    if name == "Connections.csv":
        start = text.find("First Name,")
        text = text[start:] if start >= 0 else text
    return list(csv.DictReader(io.StringIO(text)))


def _full(first: str, last: str) -> str:
    return f"{first or ''} {last or ''}".strip()


def build(export: Path, home: Path) -> dict:
    """Index a LinkedIn export folder into home/network/. Returns counts."""
    export = Path(export)
    conns = _read(export, "Connections.csv")
    if not conns:
        raise FileNotFoundError(str(export / "Connections.csv"))
    messages = _read(export, "messages.csv")

    # Your own profile is whoever sends the most messages
    senders = Counter(_slug(m.get("SENDER PROFILE URL", "")) for m in messages)
    senders.pop("", None)
    me = senders.most_common(1)[0][0] if senders else ""

    people: dict[str, dict] = {}
    by_name: dict[str, list[str]] = {}
    for c in conns:
        name = _full(c.get("First Name"), c.get("Last Name"))
        if not name:
            continue   # LinkedIn hides some names; those rows can't be used
        key = _slug(c.get("URL", "")) or name.lower()
        people[key] = {col: "" for col in CONTACT_COLS} | {
            "name": name, "company": c.get("Company", ""), "position": c.get("Position", ""),
            "url": c.get("URL", ""), "connected_on": c.get("Connected On", ""),
            "messages": 0, "sent": 0, "received": 0}
        by_name.setdefault(name.lower(), []).append(key)

    for m in messages:
        sender = _slug(m.get("SENDER PROFILE URL", ""))
        others = {_slug(u) for u in (m.get("RECIPIENT PROFILE URLS") or "").split(",")} | {sender}
        date = (m.get("DATE") or "")[:10]
        for o in others - {"", me}:
            p = people.get(o)
            if not p:
                continue
            p["messages"] += 1
            p["sent" if sender == me else "received"] += 1
            p["last_message"] = max(p["last_message"], date)

    def person(url: str, first: str, last: str) -> dict | None:
        if url and not url.startswith("http"):
            url = "https://" + url
        if _slug(url) in people:
            return people[_slug(url)]
        keys = by_name.get(_full(first, last).lower(), [])
        return people[keys[0]] if len(keys) == 1 else None   # skip ambiguous names

    for e in _read(export, "Endorsement_Received_Info.csv"):
        if p := person(e.get("Endorser Public Url", ""), e.get("Endorser First Name"), e.get("Endorser Last Name")):
            p["endorsed_you"] = "yes"
    for e in _read(export, "Endorsement_Given_Info.csv"):
        if p := person(e.get("Endorsee Public Url", ""), e.get("Endorsee First Name"), e.get("Endorsee Last Name")):
            p["you_endorsed"] = "yes"
    for r in _read(export, "Recommendations_Received.csv"):
        if p := person("", r.get("First Name"), r.get("Last Name")):
            p["recommended_you"] = (r.get("Creation Date") or "yes").split(",")[0]
    for r in _read(export, "Recommendations_Given.csv"):
        if p := person("", r.get("First Name"), r.get("Last Name")):
            p["you_recommended"] = (r.get("Creation Date") or "yes").split(",")[0]

    pending = []
    for i in _read(export, "Invitations.csv"):
        outgoing = i.get("Direction", "").upper() == "OUTGOING"
        url = i.get("inviteeProfileUrl" if outgoing else "inviterProfileUrl", "")
        sent = (i.get("Sent At") or "").split(",")[0]
        if _slug(url) in people:   # accepted since
            people[_slug(url)]["invitation"] = ("you invited them " if outgoing else "they invited you ") + sent
        else:
            pending.append({"direction": "outgoing" if outgoing else "incoming",
                            "name": i.get("To" if outgoing else "From", ""), "url": url,
                            "sent": i.get("Sent At", ""), "note": i.get("Message", "")})

    out = Path(home) / "network"
    out.mkdir(parents=True, exist_ok=True)
    rows = sorted(people.values(), key=lambda p: (-p["messages"], p["name"].lower()))
    _write(out / "contacts.csv", CONTACT_COLS, rows)
    _write(out / "pending.csv", PENDING_COLS, pending)
    return {"connections": len(rows), "messaged": sum(1 for p in rows if p["messages"]),
            "endorsed_or_recommended": sum(1 for p in rows if p["endorsed_you"] or p["recommended_you"]),
            "pending": len(pending), "folder": str(out)}


def _write(path: Path, cols: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, cols)
        w.writeheader()
        w.writerows({c: r.get(c, "") for c in cols} for r in rows)


def keys(company: str, aliases: dict | None = None) -> list[str]:
    """The names to look for when searching for a company."""
    c = company.lower().strip()
    table = {**ALIASES, **{k.lower(): v for k, v in (aliases or {}).items()}}
    if c in table:
        return [k.lower() for k in table[c]]
    words = [w for w in re.split(r"[^a-z0-9&.']+", c) if w and w not in _STOP]
    return [" ".join(words)] if words else [c]


def matches(text: str, company: str, aliases: dict | None = None) -> bool:
    t = (text or "").lower()
    return any(re.search(r"(^|[^a-z0-9])" + re.escape(k) + r"($|[^a-z0-9])", t) for k in keys(company, aliases))


def find(company: str, home: Path, aliases: dict | None = None) -> dict:
    """Connections at a company (warmest first) and invitations still waiting."""
    folder = Path(home) / "network"
    contacts_file = folder / "contacts.csv"
    if not contacts_file.exists():
        raise FileNotFoundError(str(contacts_file))
    with contacts_file.open(encoding="utf-8") as f:
        contacts = [r for r in csv.DictReader(f) if matches(r["company"], company, aliases)]
    contacts.sort(key=warmth, reverse=True)
    pending = []
    if (folder / "pending.csv").exists():
        with (folder / "pending.csv").open(encoding="utf-8") as f:
            # An invitation has no company field, so only the note can name it
            pending = [r for r in csv.DictReader(f) if matches(r["note"], company, aliases)]
    return {"company": company, "contacts": contacts, "pending": pending}


def warmth(r: dict) -> tuple:
    """Sort key: people who replied, then endorsed or recommended you, then any messages."""
    return (int(r.get("received") or 0) > 0, bool(r.get("recommended_you") or r.get("endorsed_you")),
            int(r.get("messages") or 0), r.get("last_message", ""))


def plain(res: dict) -> str:
    lines = [f"{res['company']}: {len(res['contacts'])} connection(s)"]
    for r in res["contacts"]:
        n = int(r["messages"] or 0)
        talk = f"{n} message{'s' if n != 1 else ''}, last {r['last_message']}" if n else "never messaged"
        if n and not int(r["received"] or 0):
            talk += ", no reply"
        extra = [x for x in ("endorsed you" if r["endorsed_you"] else "",
                             "recommended you" if r["recommended_you"] else "") if x]
        lines.append(f"  - {r['name']}, {r['position']} | {talk}"
                     + (f" | {', '.join(extra)}" if extra else "") + f" | {r['url']}")
    for p in res["pending"]:
        lines.append(f"  - invitation to {p['name']} not accepted yet (sent {p['sent'].split(',')[0]}) | {p['url']}")
    if not res["contacts"] and not res["pending"]:
        lines.append("  nobody yet: use `python -m jobhunt people` to find someone to reach out to")
    return "\n".join(lines)
