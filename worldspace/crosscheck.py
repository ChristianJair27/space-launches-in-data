"""Compare GCAT yearly totals with Wikipedia's "<year> in spaceflight" by-country tables.

Wikipedia assigns each launch to the country of origin of the rocket (Electron
counts as USA; Vega as Italy; Ariane as France). GCAT assigns it to the
launch-service agency. We therefore compare at the level of USA (incl. Rocket
Lab), China, Russia, Europe (France + Italy + Germany + ESA), India, Japan and
others, which is where the two definitions coincide for recent years.
"""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request

import pandas as pd

from . import DATA

API = "https://en.wikipedia.org/w/api.php"
CC = {"USA": "USA", "CHN": "China", "RUS": "Russia", "FRA": "Europe", "ITA": "Europe",
      "GER": "Europe", "IND": "India", "JPN": "Japan"}


def _wikitext(year: int) -> str:
    path = DATA / "crosscheck" / f"wiki_{year}.json"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        q = urllib.parse.urlencode({"action": "parse", "page": f"{year}_in_spaceflight",
                                    "prop": "wikitext", "format": "json", "formatversion": 2})
        req = urllib.request.Request(f"{API}?{q}", headers={"User-Agent": "space-launches-in-data"})
        with urllib.request.urlopen(req, timeout=60) as r:
            path.write_bytes(r.read())
    return json.loads(path.read_text(encoding="utf-8"))["parse"]["wikitext"]


def wikipedia_by_country(year: int) -> pd.DataFrame:
    text = _wikitext(year)
    start = text.index("=== By country ===")
    block = text[start:text.index("|}", start)]
    block = re.sub(r"{{efn[^}]*}}", "", block)
    rows = re.findall(r"\{\{([A-Z]{3})\}\}[^\n]*\n\|\s*(\d+)[^|]*\|\|\s*(\d+)\s*\|\|\s*(\d+)\s*\|\|\s*(\d+)",
                      block)
    df = pd.DataFrame(rows, columns=["cc", "launches", "successes", "failures", "partial"])
    df[["launches", "successes", "failures", "partial"]] = df[
        ["launches", "successes", "failures", "partial"]].astype(int)
    df["region"] = df.cc.map(CC).fillna("Other")
    return df.groupby("region")[["launches", "successes"]].sum()


def gcat_by_region(launches: pd.DataFrame, year: int) -> pd.DataFrame:
    region = launches.group.map({
        "SpaceX": "USA", "USA (other)": "USA", "Rocket Lab": "USA", "USSR/Russia": "Russia",
        "China (state)": "China", "China (commercial)": "China", "Europe": "Europe",
        "Japan": "Japan", "India": "India", "Other": "Other"})
    y = launches.assign(region=region)[launches.year == year]
    return y.groupby("region").agg(launches=("tag", "size"), successes=("success", "sum"))


def compare(launches: pd.DataFrame, years=(2024, 2025)) -> pd.DataFrame:
    out = []
    for y in years:
        w = wikipedia_by_country(y)
        g = gcat_by_region(launches, y)
        t = g.join(w, lsuffix="_gcat", rsuffix="_wiki", how="outer").fillna(0).astype(int)
        t.loc["World"] = t.sum()
        t.insert(0, "year", y)
        out.append(t)
    return pd.concat(out)
