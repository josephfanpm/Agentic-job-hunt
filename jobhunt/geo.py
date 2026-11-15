"""Work out which countries a free-text job location refers to.

Feeds describe location every way imaginable ("San Francisco, CA", "Toronto",
"USA Only", "Remote - Americas", "Shenzhen, CHN"). This module turns those
into ISO-2 country codes where it can, and returns an empty set when it
can't, so the pipeline can keep the job with a flag instead of silently
dropping it.
"""
from __future__ import annotations

import re

from jobhunt.text import norm

US_STATES = set("AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT "
                "NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC".split())
CA_PROVINCES = set("ON BC AB QC MB SK NS NB NL PE YT NT NU".split())

_NAMES = {
    "US": ["united states", "usa", "u s a", "u s", "us", "america"],
    "CA": ["canada"],
    "GB": ["united kingdom", "uk", "england", "scotland", "wales", "great britain"],
    "IE": ["ireland"], "DE": ["germany"], "FR": ["france"], "ES": ["spain"], "PT": ["portugal"],
    "NL": ["netherlands"], "PL": ["poland"], "SE": ["sweden"], "CH": ["switzerland"],
    "IT": ["italy"], "IN": ["india"], "SG": ["singapore"], "JP": ["japan"], "CN": ["china"],
    "AU": ["australia"], "NZ": ["new zealand"], "BR": ["brazil"], "MX": ["mexico"],
    "AR": ["argentina"], "CO": ["colombia"], "IL": ["israel"], "AE": ["united arab emirates", "uae"],
    "PH": ["philippines"], "ZA": ["south africa"], "KR": ["south korea", "korea"], "RO": ["romania"],
}
_US_STATE_NAMES = ["california", "new york", "texas", "washington", "massachusetts", "illinois",
                   "florida", "colorado", "georgia", "virginia", "pennsylvania", "north carolina",
                   "new jersey", "arizona", "oregon", "utah", "minnesota", "ohio", "michigan",
                   "tennessee", "maryland", "missouri", "wisconsin", "indiana", "connecticut"]
_CA_PROVINCE_NAMES = ["ontario", "british columbia", "alberta", "quebec", "manitoba",
                      "saskatchewan", "nova scotia", "new brunswick"]
_CITIES = {
    "US": ["san francisco", "new york city", "nyc", "seattle", "austin", "boston", "chicago",
           "los angeles", "denver", "atlanta", "san diego", "san jose", "palo alto",
           "mountain view", "menlo park", "sunnyvale", "bay area"],
    "CA": ["toronto", "vancouver", "montreal", "ottawa", "calgary", "edmonton", "waterloo",
           "kitchener", "mississauga"],
    "GB": ["london"], "IE": ["dublin"], "DE": ["berlin", "munich"], "FR": ["paris"],
    "NL": ["amsterdam"], "IN": ["bangalore", "bengaluru", "hyderabad", "mumbai", "pune"],
    "AU": ["sydney", "melbourne"], "IL": ["tel aviv"], "JP": ["tokyo"],
}
_ISO3 = {"USA": "US", "CAN": "CA", "GBR": "GB", "IRL": "IE", "DEU": "DE", "FRA": "FR",
         "ESP": "ES", "NLD": "NL", "POL": "PL", "IND": "IN", "SGP": "SG", "JPN": "JP",
         "CHN": "CN", "AUS": "AU", "BRA": "BR", "MEX": "MX", "ISR": "IL", "ITA": "IT",
         "CHE": "CH", "SWE": "SE", "LUX": "LU", "CRI": "CR", "ROU": "RO", "ZAF": "ZA"}
ISO2_TO_ISO3 = {v: k for k, v in _ISO3.items()}

EUROPE = {"GB", "IE", "DE", "FR", "ES", "PT", "NL", "PL", "SE", "CH", "IT", "RO"}
_REGIONS = {
    "north america": {"US", "CA", "MX"},
    "americas": {"US", "CA", "MX", "BR", "AR", "CO"},
    "latam": {"MX", "BR", "AR", "CO"}, "latin america": {"MX", "BR", "AR", "CO"},
    "europe": EUROPE, "emea": EUROPE | {"IL", "AE", "ZA"}, "eu": EUROPE,
    "apac": {"IN", "SG", "JP", "CN", "AU", "NZ", "PH", "KR"},
    "asia": {"IN", "SG", "JP", "CN", "PH", "KR"},
}
_ANYWHERE = ["worldwide", "anywhere", "global", "any location"]
ANY = "*"  # marker: open to every country


def is_remote(location: str) -> bool:
    n = f" {norm(location)} "
    return any(w in n for w in (" remote ", " anywhere ", " worldwide ", " distributed ",
                                " work from home "))


def countries(location: str, stated: str = "") -> set[str]:
    """ISO-2 codes this location covers. {ANY} = worldwide. Empty = can't tell."""
    found: set[str] = set()
    if stated:
        s = stated.strip().upper()
        if len(s) in (2, 3):
            found.add(_ISO3.get(s, s))
    if not location:
        return found
    n = f" {norm(location)} "
    if any(f" {w} " in n for w in _ANYWHERE):
        return {ANY}
    for region, codes in _REGIONS.items():
        if f" {region} " in n:
            found |= codes
    for code, names in _NAMES.items():
        if any(f" {name} " in n for name in names):
            found.add(code)
    for code, names in _CITIES.items():
        if any(f" {name} " in n for name in names):
            found.add(code)
    if any(f" {name} " in n for name in _US_STATE_NAMES):
        found.add("US")
    if any(f" {name} " in n for name in _CA_PROVINCE_NAMES):
        found.add("CA")
    # Two- and three-letter codes after a separator: "Austin, TX", "Shenzhen, CHN"
    codes = re.findall(r"(?:,|;|/|-|\|)\s*([A-Z]{2,3})\b", location)
    has_province = any(c in CA_PROVINCES for c in codes)
    for c in codes:
        if c in _ISO3:
            found.add(_ISO3[c])
        elif c in CA_PROVINCES:
            found.add("CA")
        elif c == "CA" and has_province:
            found.add("CA")
        elif c in US_STATES and not (found - {"US"}):
            # "Bangalore, IN" is India, not Indiana: only trust a state code
            # when nothing else in the string points at another country.
            found.add("US")
    return found
