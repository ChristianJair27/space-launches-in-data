"""Download GCAT files and turn the launch list into one clean row per orbital attempt.

Column meanings follow the GCAT documentation (release 1.8.9):
  * Launch list columns: https://planet4589.org/space/gcat/web/launch/lcols.html
  * LaunchCode first letter: O orbital, D deep space, ... ; second letter S/F
    (success/failure), E pad explosion, A pad abort; digits = success fraction
    https://planet4589.org/space/gcat/web/intro/success.html
  * Group (orbital launches) = launch service code G / CG / CO / CX / C, plus
    an 'M' megaconstellation flag
    https://planet4589.org/space/gcat/web/intro/service.html
  * OrbPay = payload tonnes delivered to orbit ("use with caution")
  * Agency = launch-service organisation, resolved through the orgs table
    https://planet4589.org/space/gcat/web/orgs/index.html
"""

from __future__ import annotations

import re
import urllib.request

import numpy as np
import pandas as pd

from . import RAW

BASE = "https://planet4589.org/space/gcat/tsv"
FILES = {
    "launch.tsv": f"{BASE}/launch/launch.tsv",   # all launches, ~14 MB
    "orgs.tsv": f"{BASE}/tables/orgs.tsv",       # organisations -> country
    "satcat.tsv": f"{BASE}/cat/satcat.tsv",      # main object catalogue, ~19 MB
    "auxcat.tsv": f"{BASE}/cat/auxcat.tsv",      # objects missing from the US catalogue
    "satcat100k.tsv": f"{BASE}/cat/satcat100k.tsv",  # US catalogue numbers above 100000 (2026-)
}

# --- operator groups -------------------------------------------------------
GROUPS = ["SpaceX", "USA (other)", "Rocket Lab", "USSR/Russia", "China (state)",
          "China (commercial)", "Europe", "Japan", "India", "Other"]
EUROPE = {"F", "I-ESA", "I-ELDO", "D", "UK", "I"}     # France/Arianespace, ESA, ELDO, Germany, UK, Italy
RUSSIA = {"SU", "RU"}
ROCKET_LAB = {"RLABN", "RLABU"}

# Chinese launch-service companies founded as private start-ups (GCAT org Parent = '-').
CHINA_PRIVATE = {
    "LANDSP": "LandSpace", "XIDO": "Galactic Energy", "XJRY": "iSpace",
    "TIANB": "Space Pioneer", "DFK": "Orienspace", "LYK": "OneSpace",
}
# Commercial arms of state groups (CASC, CASIC, Chinese Academy of Sciences).
CHINA_STATE_OWNED_COMMERCIAL = {
    "CZHJ": "China Rocket Co. (CASC)", "EXPACE": "ExPace (CASIC)",
    "ZKYT": "CAS Space (CAS)", "ZHSH": "CASC Commercial Rocket", "CGWIC": "CGWIC (CASC)",
}

BOOSTER_RE = re.compile(r"B(1\d{3})\.(\d+)")


def download(force: bool = False) -> None:
    """Fetch the GCAT files into data/world_space/raw (about 40 MB in total)."""
    RAW.mkdir(parents=True, exist_ok=True)
    for name, url in FILES.items():
        path = RAW / name
        if path.exists() and not force:
            continue
        req = urllib.request.Request(url, headers={"User-Agent": "space-launches-in-data"})
        with urllib.request.urlopen(req, timeout=300) as r:
            path.write_bytes(r.read())
        print(f"downloaded {name}: {path.stat().st_size / 1e6:.1f} MB")


def updated(name: str = "launch.tsv") -> str:
    """The '# Updated ...' stamp written by McDowell on line 2 of every TSV."""
    with open(RAW / name, encoding="utf-8", errors="replace") as f:
        f.readline()
        return f.readline().lstrip("#").replace("Updated", "").strip()


def read_tsv(name: str) -> pd.DataFrame:
    df = pd.read_csv(RAW / name, sep="\t", dtype=str, skiprows=[1], keep_default_na=False,
                     encoding="utf-8", encoding_errors="replace")
    df.columns = [c.lstrip("#") for c in df.columns]
    return df.apply(lambda s: s.str.strip())


def _org_table() -> pd.DataFrame:
    orgs = read_tsv("orgs.tsv")
    return orgs.drop_duplicates("Code").set_index("Code")


def _group(agency: str, state: str, lst: str) -> str:
    if agency == "SPX":
        return "SpaceX"
    if agency in ROCKET_LAB:
        return "Rocket Lab"
    if state == "US":
        return "USA (other)"
    if state in RUSSIA:
        return "USSR/Russia"
    if state == "CN":
        return "China (state)" if lst.startswith("G") else "China (commercial)"
    if state in EUROPE:
        return "Europe"
    if state == "J":
        return "Japan"
    if state == "IN":
        return "India"
    return "Other"


def _china_tier(agency: str, state: str, lst: str) -> str:
    if state != "CN":
        return ""
    if agency in CHINA_PRIVATE:
        return "private"
    if lst.startswith("G"):
        return "state"
    return "state-owned commercial"


def orbital_launches() -> pd.DataFrame:
    """One row per orbital launch attempt (LaunchCode O* or D*, outcome S or F).

    Pad explosions (OE) and pad aborts (OA) are not launches and are dropped.
    """
    raw = read_tsv("launch.tsv")
    code = raw["LaunchCode"]
    keep = code.str[0].isin(["O", "D"]) & code.str[1].isin(["S", "F"])
    d = raw[keep].copy()

    orgs = _org_table()
    d["agency"] = d["Agency"].str.split("/").str[0].str.rstrip("?")
    d["state"] = d["agency"].map(orgs["StateCode"]).fillna("")
    d["lst"] = d["Group"].str.split().str[0].fillna("")
    d["megaconst"] = d["Group"].str.split().str[1].fillna("").eq("M")
    d["group"] = [_group(a, s, l) for a, s, l in zip(d["agency"], d["state"], d["lst"])]
    d["china_tier"] = [_china_tier(a, s, l) for a, s, l in zip(d["agency"], d["state"], d["lst"])]
    d["operator"] = d["agency"].map(orgs["ShortName"]).fillna(d["agency"])

    d["jd"] = d["Launch_JD"].astype(float)
    # Calendar day from the text date (Launch_JD has only 0.01 d precision)
    day = pd.to_datetime(d["Launch_Date"].str[:11].str.replace(r"\s+", " ", regex=True),
                         format="%Y %b %d", errors="coerce")
    d["date"] = day.fillna(pd.to_datetime(d["jd"] - 2440587.5, unit="D").dt.floor("D"))
    d["year"] = d["Launch_Date"].str[:4].astype(int)
    d["success"] = code[keep].str[1].eq("S")
    frac = code[keep].str[2:].replace("", np.nan).astype(float) / 100
    d["success_fraction"] = frac.fillna(d["success"].astype(float))
    d["orbpay_t"] = pd.to_numeric(d["OrbPay"], errors="coerce").fillna(0.0)
    d["starship"] = d["LV_Type"].str.startswith("Starship")
    text = d["Flight"] + " " + d["Mission"] + " " + d["FlightCode"]
    d["starlink_mission"] = text.str.contains("Starlink", case=False)

    cols = ["Launch_Tag", "date", "jd", "year", "LV_Type", "Variant", "Flight_ID", "Flight", "Mission",
            "FlightCode", "Launch_Site", "agency", "operator", "state", "group", "china_tier", "lst",
            "megaconst", "LaunchCode", "success", "success_fraction", "orbpay_t", "starship",
            "starlink_mission"]
    out = d[cols].rename(columns={"Launch_Tag": "tag", "LV_Type": "lv", "Variant": "variant",
                                  "Flight_ID": "flight_id", "Flight": "flight", "Mission": "mission",
                                  "FlightCode": "flight_code", "Launch_Site": "site",
                                  "LaunchCode": "launch_code"})
    return out.sort_values("jd").reset_index(drop=True)


# Reusable orbital vehicles whose own mass GCAT includes in OrbPay.
VEHICLE_RE = r"^(Columbia|Challenger|Discovery|Atlantis|Endeavour|Buran|Starship)\b"


def payload_counts() -> pd.DataFrame:
    """Per launch tag, from satcat + auxcat:

    * ``payloads``: standard payloads (SatType byte 1 'P', byte 2 not 'A' alias
      or 'X' non-standard), i.e. what most satellite lists would count;
    * ``starlink_payloads``: of those, objects named 'Starlink ...';
    * ``vehicle_t``: own mass of a Shuttle orbiter, Buran or Starship ship,
      which GCAT's OrbPay includes; we subtract it to get cargo mass;
    * ``cargo_cat_t``: summed catalogue mass of standard payloads other than
      those vehicles (used for Starship flights).
    """
    frames = []
    for name in ("satcat.tsv", "satcat100k.tsv", "auxcat.tsv"):
        cat = read_tsv(name)
        cat = cat[cat["Type"].str[0].eq("P")]
        frames.append(cat[["JCAT", "Launch_Tag", "Type", "Name", "Mass"]])
    cat = pd.concat(frames).drop_duplicates("JCAT")
    cat["standard"] = ~cat["Type"].str[1].isin(["A", "X"])
    cat["starlink"] = cat["standard"] & cat["Name"].str.match(r"Starlink", case=False)
    cat["mass_kg"] = pd.to_numeric(cat["Mass"], errors="coerce").fillna(0.0)
    is_vehicle = cat["Name"].str.match(VEHICLE_RE)
    cat["vehicle_kg"] = cat["mass_kg"].where(is_vehicle, 0.0)
    cat["cargo_kg"] = cat["mass_kg"].where(cat["standard"] & ~is_vehicle, 0.0)
    g = cat.groupby("Launch_Tag")
    return pd.DataFrame({"payloads": g["standard"].sum(),
                         "starlink_payloads": g["starlink"].sum(),
                         "vehicle_t": g["vehicle_kg"].sum() / 1000,
                         "cargo_cat_t": g["cargo_kg"].sum() / 1000})


def booster_flights(launches: pd.DataFrame) -> pd.DataFrame:
    """Every Falcon first-stage flight: core serial (B10xx), its flight number, date.

    Falcon 9 cores sit in Flight_ID ('xxx/B1063.36 F699'); Falcon Heavy side
    cores in FlightCode ('B1064.6,B1065.6').
    """
    f = launches[launches["lv"].str.startswith("Falcon")]
    rows = []
    for r in f.itertuples():
        for field, role in ((r.flight_id, "core"), (r.flight_code, "side")):
            for serial, n in BOOSTER_RE.findall(field):
                rows.append({"tag": r.tag, "date": r.date, "jd": r.jd, "year": r.year, "lv": r.lv,
                             "booster": f"B{serial}", "flight_no": int(n), "role": role,
                             "success": r.success, "starlink_mission": r.starlink_mission})
    b = pd.DataFrame(rows).sort_values(["booster", "jd"]).reset_index(drop=True)
    b["turnaround_days"] = b.groupby("booster")["jd"].diff()
    return b
