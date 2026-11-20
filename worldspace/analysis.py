"""Tables and headline numbers, all computed from the GCAT files in data/world_space/raw.

Every number quoted in the report, README, outline and Short scripts comes from
``derived/facts.json`` written here, so it can be regenerated when GCAT updates.
"""

from __future__ import annotations

import json

import pandas as pd

from . import DERIVED, gcat

LAST_FULL_YEAR = 2025   # 2026 is partial (GCAT data update 2026 Nov 19)


def build() -> dict[str, pd.DataFrame]:
    launches = gcat.orbital_launches()
    pay = gcat.payload_counts()
    launches = launches.join(pay, on="tag")
    for c in ("payloads", "starlink_payloads", "vehicle_t", "cargo_cat_t"):
        launches[c] = launches[c].fillna(0)
    # Cargo mass. GCAT's OrbPay counts a Shuttle orbiter / Buran / Starship ship
    # as payload. Shuttle & Buran: OrbPay minus the orbiter's catalogue mass.
    # Starship: catalogued standard payloads only (Starlinks on flights 14-15;
    # mass simulators are 'PX' and excluded). Everything else: OrbPay.
    shuttle = launches["lv"].isin(["Space Shuttle", "Energiya/Buran"])
    launches["cargo_t"] = launches["orbpay_t"]
    launches.loc[shuttle, "cargo_t"] = (launches["orbpay_t"] - launches["vehicle_t"]).clip(lower=0)[shuttle]
    launches.loc[launches.starship, "cargo_t"] = launches.loc[launches.starship, "cargo_cat_t"]
    boosters = gcat.booster_flights(launches)

    by_year = launches.pivot_table(index="year", columns="group", values="tag", aggfunc="count",
                                   fill_value=0).reindex(columns=gcat.GROUPS, fill_value=0)
    ok_year = launches[launches.success].pivot_table(
        index="year", columns="group", values="tag", aggfunc="count",
        fill_value=0).reindex(index=by_year.index, columns=gcat.GROUPS, fill_value=0)
    # Mass: cargo tonnes of successful launches (OrbPay minus reusable vehicle).
    m = launches[launches.success]
    mass_year = m.pivot_table(index="year", columns="group", values="cargo_t", aggfunc="sum",
                              fill_value=0).reindex(index=by_year.index, columns=gcat.GROUPS,
                                                    fill_value=0)
    starlink_mass = m[m.starlink_mission].groupby("year")["cargo_t"].sum().reindex(
        by_year.index, fill_value=0)
    china = launches[launches.state.eq("CN")].pivot_table(
        index="year", columns="china_tier", values="tag", aggfunc="count", fill_value=0)
    payloads_year = launches[launches.success].groupby("year")[["payloads", "starlink_payloads"]].sum()

    tables = {"launches": launches, "boosters": boosters, "by_year": by_year,
              "successes_by_year": ok_year, "mass_by_year": mass_year,
              "starlink_mass_by_year": starlink_mass.to_frame("starlink_t"),
              "china_by_year": china, "payloads_by_year": payloads_year}
    return tables


def facts(t: dict[str, pd.DataFrame]) -> dict:
    L, B, Y = t["launches"], t["boosters"], t["by_year"]
    world = Y.sum(axis=1)
    f: dict = {"gcat_updated": gcat.updated(), "satcat_updated": gcat.updated("satcat.tsv")}
    f["attempts_total"] = int(len(L))
    f["successes_total"] = int(L.success.sum())
    f["first_year"], f["last_year"] = int(L.year.min()), int(L.year.max())
    f["record_year"], f["record_year_attempts"] = int(world.idxmax()), int(world.max())

    # Totals per group, all time
    g = L.groupby("group").agg(attempts=("tag", "size"), successes=("success", "sum"))
    g["success_rate"] = (g.successes / g.attempts).round(4)
    f["by_group_all_time"] = g.reindex(gcat.GROUPS).fillna(0).astype({"attempts": int, "successes": int}).to_dict("index")

    # Year snapshots
    snap = {}
    for y in (1957, 1967, 1982, 1990, 2000, 2010, 2015, 2020, 2021, 2022, 2023, 2024, 2025, 2026):
        row = Y.loc[y]
        ly = L[L.year == y]
        snap[y] = {"world": int(row.sum()), "successes": int(ly.success.sum()),
                   **{k: int(v) for k, v in row.items()},
                   "spacex_share": round(row["SpaceX"] / row.sum(), 4),
                   "spacex_starship": int((ly.starship).sum()),
                   "falcon": int(ly.lv.str.startswith("Falcon").sum()),
                   "falcon9": int(ly.lv.eq("Falcon 9").sum()),
                   "rest_of_world": int(row.sum() - row["SpaceX"])}
    f["years"] = snap

    ussr = Y["USSR/Russia"]
    f["ussr_record_year"], f["ussr_record"] = int(ussr.idxmax()), int(ussr.max())
    us_total = Y["SpaceX"] + Y["USA (other)"] + Y["Rocket Lab"]
    # The year SpaceX alone first out-launched the rest of the world combined
    beat = Y.index[(Y["SpaceX"] > world - Y["SpaceX"])]
    f["spacex_beats_rest_years"] = [int(y) for y in beat]
    f["spacex_cumulative"] = int(Y["SpaceX"].sum())
    f["spacex_first_orbital_attempt"] = str(L[L.group.eq("SpaceX")].date.min().date())
    f["spacex_success_rate_falcon9"] = round(L[L.lv.eq("Falcon 9")].success.mean(), 4)
    f9 = L[L.lv.eq("Falcon 9")]
    f["falcon9_attempts"], f["falcon9_failures"] = int(len(f9)), int((~f9.success).sum())
    f["falcon9_failure_tags"] = f9[~f9.success][["tag", "date"]].astype(str).values.tolist()
    # Longest Falcon 9 run without failure
    run, best, best_end = 0, 0, None
    for r in f9.itertuples():
        run = run + 1 if r.success else 0
        if run > best:
            best, best_end = run, str(r.date.date())
    f["falcon9_longest_success_streak"] = best
    f["falcon9_streak_end"] = best_end

    # US vs USSR crossover (the US total overtakes USSR/Russia for good)
    f["us_total_by_year_2025"] = int(us_total.loc[2025])

    # China
    cn = L[L.state.eq("CN")]
    tiers = cn.groupby(["year", "china_tier"]).size().unstack(fill_value=0)
    f["china_tiers"] = {int(y): {k: int(v) for k, v in r.items()} for y, r in tiers.loc[2015:].iterrows()}
    priv = cn[cn.china_tier.eq("private")]
    first_ok = priv[priv.success].groupby("operator").date.min().sort_values()
    f["china_private_first_orbit"] = {k: str(v.date()) for k, v in first_ok.items()}
    f["china_private_attempts"] = int(len(priv))
    f["china_private_success_rate"] = round(priv.success.mean(), 4)
    f["china_private_by_company"] = (priv.groupby("operator").agg(attempts=("tag", "size"),
                                     successes=("success", "sum")).astype(int).to_dict("index"))
    comm = cn[cn.china_tier.ne("state")]
    f["china_commercial_by_operator"] = (comm.groupby("operator").agg(
        attempts=("tag", "size"), successes=("success", "sum")).astype(int).to_dict("index"))

    # Mass to orbit (successful, non-Starship)
    M = t["mass_by_year"]
    mw = M.sum(axis=1)
    sl = t["starlink_mass_by_year"]["starlink_t"]
    f["mass"] = {int(y): {"world_t": round(mw.loc[y], 1), "spacex_t": round(M.loc[y, "SpaceX"], 1),
                          "spacex_share": round(M.loc[y, "SpaceX"] / mw.loc[y], 4) if mw.loc[y] else 0,
                          "starlink_t": round(sl.loc[y], 1),
                          "starlink_share": round(sl.loc[y] / mw.loc[y], 4) if mw.loc[y] else 0}
                 for y in (1969, 1985, 2000, 2015, 2020, 2022, 2023, 2024, 2025, 2026)}
    f["mass_all_time_t"] = round(mw.sum(), 1)
    f["mass_spacex_all_time_t"] = round(M["SpaceX"].sum(), 1)
    f["starship_flights"] = L[L.starship][["tag", "date", "launch_code"]].astype(str).values.tolist()
    f["mass_peak_pre_spacex"] = {"year": int(mw.loc[:2009].idxmax()), "t": round(mw.loc[:2009].max(), 1)}
    f["shuttle_orbiter_t_removed"] = round(L[L.lv.eq("Space Shuttle") & L.success].vehicle_t.sum(), 1)

    # Payload counts (satellites placed in orbit by successful launches)
    P = t["payloads_by_year"]
    f["payloads_all_time"] = int(P.payloads.sum())
    f["starlink_payloads_all_time"] = int(P.starlink_payloads.sum())
    f["starlink_share_of_all_payloads"] = round(P.starlink_payloads.sum() / P.payloads.sum(), 4)
    f["payloads"] = {int(y): {"all": int(P.loc[y, "payloads"]), "starlink": int(P.loc[y, "starlink_payloads"])}
                     for y in (2019, 2020, 2022, 2024, 2025, 2026)}
    first_sl = L[(L.starlink_payloads > 0)].date.min()
    before = P.loc[:first_sl.year - 1, "payloads"].sum() + L[(L.year == first_sl.year) & L.success & (L.date < first_sl)].payloads.sum()
    f["payloads_before_first_starlink"] = int(before)
    f["first_starlink_launch"] = str(first_sl.date())

    # Reuse
    b = B
    f["falcon_core_flights"] = int(len(b))
    f["falcon_core_flights_reflown"] = int((b.flight_no > 1).sum())
    f["falcon_distinct_boosters"] = int(b.booster.nunique())
    top = b.groupby("booster").flight_no.max().sort_values(ascending=False)
    f["booster_most_flights"] = {"booster": top.index[0], "flights": int(top.iloc[0]),
                                 "top5": {k: int(v) for k, v in top.head(5).items()}}
    first_reflight = b[b.flight_no == 2].sort_values("jd").iloc[0]
    f["first_reflight"] = {"booster": first_reflight.booster, "date": str(first_reflight.date.date()),
                           "tag": first_reflight.tag}
    ta = b.dropna(subset=["turnaround_days"])
    fastest = ta.sort_values("turnaround_days").iloc[0]
    f["fastest_turnaround"] = {"booster": fastest.booster, "days": round(fastest.turnaround_days, 2),
                               "date": str(fastest.date.date()), "tag": fastest.tag}
    med = ta.groupby("year").turnaround_days.median()
    f["median_turnaround_days"] = {int(y): round(v, 1) for y, v in med.items()}
    reuse_share = L[L.lv.eq("Falcon 9")].assign(
        reflown=lambda d: d.flight_id.str.extract(r"B1\d{3}\.(\d+)")[0].astype(float) > 1)
    rs = reuse_share.groupby("year").reflown.mean()
    f["falcon9_reflown_share"] = {int(y): round(v, 4) for y, v in rs.items() if y >= 2017}
    return f


def save(t: dict[str, pd.DataFrame], f: dict) -> None:
    DERIVED.mkdir(parents=True, exist_ok=True)
    L = t["launches"].copy()
    L["date"] = L["date"].dt.strftime("%Y-%m-%d %H:%M:%S")
    L.to_csv(DERIVED / "orbital_launches.csv", index=False)
    t["boosters"].assign(date=t["boosters"].date.dt.strftime("%Y-%m-%d")).to_csv(
        DERIVED / "falcon_booster_flights.csv", index=False)
    for k in ("by_year", "successes_by_year", "mass_by_year", "starlink_mass_by_year",
              "china_by_year", "payloads_by_year"):
        t[k].round(3).to_csv(DERIVED / f"{k}.csv")
    (DERIVED / "facts.json").write_text(json.dumps(f, indent=1, default=str), encoding="utf-8")
