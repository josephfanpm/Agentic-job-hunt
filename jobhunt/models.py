"""The one record every source produces and every later step consumes."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class Job:
    source: str                 # e.g. "greenhouse", "remoteok"
    company: str
    title: str
    url: str
    location: str = ""
    country: str = ""           # ISO-2 code when the source states it outright
    remote: bool | None = None  # None = the source doesn't say
    posted: str = ""            # yyyy-mm-dd, or "" when unknown
    pay: str = ""               # display text taken from the posting; never guessed
    pay_min: float | None = None
    pay_max: float | None = None
    description: str = ""       # raw text or HTML; cleaned lazily by the pipeline
    job_id: str = ""
    # Filled in by the pipeline
    score: int = 0
    why: str = ""
    flags: list[str] = field(default_factory=list)

    def to_dict(self, with_description: bool = False) -> dict:
        d = asdict(self)
        if not with_description:
            d.pop("description")
        return d
