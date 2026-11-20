"""Static figures, in English (repo) or Spanish (dashboard).

``render_all(tables, facts, lang, save)`` calls ``save(fig, file, title, caption)``
for each figure; the default saver writes PNGs into ``worldspace.FIGURES``.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch
from matplotlib.ticker import MaxNLocator

from . import FIGURES
from .style import BG, COLORS, FIG_GROUPS, GRID, HIGHLIGHT, INK, LABELS, MUTED, SOURCE, fig_group

T = {
    "en": {
        "per_year_t": "Every orbital launch attempt, 1957–2026",
        "per_year_y": "orbital launch attempts per year",
        "partial": "2026: to {d}",
        "ussr_peak": "USSR peak: {n} (1982)",
        "record": "{y}: {n}\nworld record",
        "share_t": "One company's share of the world's launches and of the mass it lifts",
        "share_launches": "share of orbital launch attempts",
        "share_mass": "share of payload mass to orbit",
        "share_y": "SpaceX share (%)",
        "china_t": "China: the commercial wave",
        "china_y": "Chinese orbital launch attempts",
        "state": "state (CASC & military)", "soe": "commercial arms of state groups",
        "private": "private start-ups",
        "mass_t": "Payload mass reaching orbit each year (successful launches)",
        "mass_y": "tonnes per year",
        "starlink": "of which Starlink",
        "mass_note": "Shuttle orbiter, Buran and Starship ship masses removed",
        "reuse_t": "Falcon boosters: each dot is one flight of one first stage",
        "reuse_y": "flight number of that booster (1 = first flight)",
        "turn_t": "Median days between two flights of the same booster",
        "turn_y": "days",
        "succ_t": "Success rate by decade (attempts in brackets)",
        "rest_t": "2025: SpaceX vs the rest of the planet",
        "rest_spx": "SpaceX", "rest_world": "Everyone else",
        "launches": "orbital launch attempts",
    },
    "es": {
        "per_year_t": "Todos los intentos de lanzamiento orbital, 1957–2026",
        "per_year_y": "intentos de lanzamiento orbital por año",
        "partial": "2026: hasta {d}",
        "ussr_peak": "Máximo URSS: {n} (1982)",
        "record": "{y}: {n}\nrécord mundial",
        "share_t": "La parte de una sola empresa en los lanzamientos y la masa del mundo",
        "share_launches": "% de los intentos de lanzamiento orbital",
        "share_mass": "% de la masa de carga puesta en órbita",
        "share_y": "parte de SpaceX (%)",
        "china_t": "China: la ola comercial",
        "china_y": "intentos de lanzamiento orbital chinos",
        "state": "estatal (CASC y militar)", "soe": "filiales comerciales de grupos estatales",
        "private": "startups privadas",
        "mass_t": "Masa de carga que llega a órbita cada año (lanzamientos exitosos)",
        "mass_y": "toneladas por año",
        "starlink": "de ella, Starlink",
        "mass_note": "Sin la masa del orbitador del Shuttle, Buran ni la nave Starship",
        "reuse_t": "Propulsores Falcon: cada punto es un vuelo de una primera etapa",
        "reuse_y": "número de vuelo de ese propulsor (1 = primer vuelo)",
        "turn_t": "Días (mediana) entre dos vuelos del mismo propulsor",
        "turn_y": "días",
        "succ_t": "Tasa de éxito por década (intentos entre corchetes)",
        "rest_t": "2025: SpaceX contra el resto del planeta",
        "rest_spx": "SpaceX", "rest_world": "Todos los demás",
        "launches": "intentos de lanzamiento orbital",
    },
}


def _default_save(fig, file, title, caption):
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(Path(FIGURES) / file, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return file


def _source(fig, lang, facts, y=-0.02):
    upd = facts["gcat_updated"][:11]
    fig.text(0.01, y, SOURCE[lang].format(upd=upd), color=MUTED, fontsize=8, ha="left", va="top")


def _fig_table(by_year: pd.DataFrame) -> pd.DataFrame:
    t = by_year.T.groupby(fig_group).sum().T
    return t.reindex(columns=FIG_GROUPS, fill_value=0)


def _legend(ax, lang, groups, **kw):
    handles = [Patch(color=COLORS[g], label=LABELS[lang][g]) for g in groups][::-1]
    ax.legend(handles=handles, loc="upper left", fontsize=9, labelcolor=INK, **kw)


def per_year(t, f, lang, save):
    L = T[lang]
    Y = _fig_table(t["by_year"])
    fig, ax = plt.subplots(figsize=(12, 6))
    bottom = np.zeros(len(Y))
    for g in FIG_GROUPS:
        ax.bar(Y.index, Y[g], bottom=bottom, width=0.86, color=COLORS[g], linewidth=0)
        bottom += Y[g].values
    world = Y.sum(axis=1)
    ax.annotate(L["ussr_peak"].format(n=f["ussr_record"]), (1982, world[1982]), xytext=(1975, 175),
                color=INK, fontsize=9, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ry = f["record_year"]
    ax.annotate(L["record"].format(y=ry, n=f["record_year_attempts"]), (ry - 0.5, world[ry] - 4),
                xytext=(2004, 290), color=INK, fontsize=9, ha="center",
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    last = t["launches"].date.max().strftime("%Y-%m-%d")
    ax.annotate(L["partial"].format(d=last), (2026, world[2026]), xytext=(2013, 240), color=MUTED,
                fontsize=8, ha="center", arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.6))
    ax.set_xlim(1956, 2027)
    ax.set_ylabel(L["per_year_y"])
    ax.grid(axis="y")
    ax.set_axisbelow(True)
    ax.set_title(L["per_year_t"])
    _legend(ax, lang, FIG_GROUPS, ncol=1, bbox_to_anchor=(0.0, 0.98))
    _source(fig, lang, f)
    cap = {"en": "Stacked by launch operator. Rocket Lab is folded into USA (other).",
           "es": "Barras apiladas por operador del lanzamiento. Rocket Lab se suma a EE. UU. (otros). "
                 "La URSS dominó durante 30 años con hasta 108 intentos al año; en 2025 SpaceX sola "
                 f"hizo {f['years']['2025' if '2025' in f['years'] else 2025]['SpaceX']}."}
    return save(fig, f"{'world_' if lang == 'es' else ''}launches_per_year.png",
                "Lanzamientos orbitales por año" if lang == "es" else "Orbital launches per year",
                cap[lang])


def spacex_share(t, f, lang, save):
    L = T[lang]
    Y, M = t["by_year"], t["mass_by_year"]
    yrs = range(2008, 2027)
    sl = [100 * Y.loc[y, "SpaceX"] / Y.loc[y].sum() for y in yrs]
    sm = [100 * M.loc[y, "SpaceX"] / M.loc[y].sum() for y in yrs]
    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.plot(list(yrs), sm, color=COLORS["SpaceX"], lw=2.2, marker="o", ms=5, label=L["share_mass"])
    ax.plot(list(yrs), sl, color=HIGHLIGHT, lw=2.2, marker="o", ms=5, label=L["share_launches"])
    for y, v in zip(yrs, sm):
        if y in (2015, 2020, 2024):
            ax.annotate(f"{v:.0f}%", (y, v), xytext=(0, 8), textcoords="offset points", ha="center",
                        color=INK, fontsize=9)
    for y, v in zip(yrs, sl):
        if y in (2015, 2020, 2025):
            ax.annotate(f"{v:.0f}%", (y, v), xytext=(0, -16), textcoords="offset points", ha="center",
                        color=INK, fontsize=9)
    ax.set_ylim(0, 100)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_ylabel(L["share_y"])
    ax.grid(axis="y")
    ax.legend(loc="upper left", labelcolor=INK)
    ax.set_title(L["share_t"])
    _source(fig, lang, f)
    cap = {"en": "", "es": "Línea amarilla: % de los intentos de lanzamiento orbital del mundo. Línea azul: % "
                          "de la masa de carga útil que llegó a órbita (GCAT OrbPay). Desde 2023 SpaceX "
                          "sube más del 80 % de la masa mundial."}
    return save(fig, f"{'world_' if lang == 'es' else ''}spacex_share.png",
                "La parte de SpaceX" if lang == "es" else "SpaceX share", cap[lang])


def china(t, f, lang, save):
    L = T[lang]
    c = t["china_by_year"].reindex(range(2010, 2027), fill_value=0)
    cols = [("state", COLORS["China (state)"], L["state"]),
            ("state-owned commercial", "#b8653a", L["soe"]),
            ("private", COLORS["China (commercial)"], L["private"])]
    fig, ax = plt.subplots(figsize=(11, 5.5))
    bottom = np.zeros(len(c))
    for col, colr, lab in cols:
        vals = c.get(col, pd.Series(0, index=c.index)).values
        ax.bar(c.index, vals, bottom=bottom, color=colr, width=0.8, label=lab,
               edgecolor=BG, linewidth=1.5, hatch="///" if col == "private" else None)
        bottom += vals
    for y in c.index:
        ax.text(y, bottom[list(c.index).index(y)] + 1.5, f"{int(bottom[list(c.index).index(y)])}",
                ha="center", color=MUTED, fontsize=8)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_ylabel(L["china_y"])
    ax.grid(axis="y")
    ax.set_axisbelow(True)
    ax.legend(loc="upper left", labelcolor=INK)
    ax.set_title(L["china_t"])
    _source(fig, lang, f)
    cap = {"en": "", "es": "Estatal = CASC y lanzadores militares (código de servicio G de GCAT). Filiales "
                          "comerciales = China Rocket (CASC), ExPace (CASIC), CAS Space. Privadas = LandSpace, "
                          "Galactic Energy, iSpace, Space Pioneer, Orienspace, OneSpace. 2026 parcial."}
    return save(fig, f"{'world_' if lang == 'es' else ''}china_state_vs_commercial.png",
                "China estatal frente a comercial" if lang == "es" else "China state vs commercial",
                cap[lang])


def mass(t, f, lang, save):
    L = T[lang]
    M = _fig_table(t["mass_by_year"])
    sl = t["starlink_mass_by_year"]["starlink_t"].reindex(M.index, fill_value=0)
    fig, ax = plt.subplots(figsize=(12, 6))
    x = M.index.values
    bottom = np.zeros(len(M))
    for g in FIG_GROUPS:
        ax.bar(x, M[g].values, bottom=bottom, width=0.86, color=COLORS[g], linewidth=0)
        if g == "SpaceX":
            ax.bar(x, sl.values, bottom=0, width=0.86, color="none", edgecolor="#cfe0ff",
                   hatch="////", linewidth=0)
        bottom += M[g].values
    ax.set_xlim(1956, 2027)
    ax.set_ylabel(L["mass_y"])
    ax.grid(axis="y")
    ax.set_axisbelow(True)
    ax.set_title(L["mass_t"])
    handles = [Patch(color=COLORS[g], label=LABELS[lang][g]) for g in FIG_GROUPS][::-1]
    handles.append(Patch(facecolor=COLORS["SpaceX"], edgecolor="#cfe0ff", hatch="////", label=L["starlink"]))
    ax.legend(handles=handles, loc="upper left", fontsize=9, labelcolor=INK)
    ax.text(0.99, 0.97, L["mass_note"], transform=ax.transAxes, ha="right", va="top", color=MUTED, fontsize=8)
    _source(fig, lang, f)
    m25 = f["mass"]["2025"] if "2025" in f["mass"] else f["mass"][2025]
    cap = {"en": "", "es": f"Toneladas de carga útil en órbita por año según la columna OrbPay de GCAT. En 2025: "
                          f"{m25['world_t']:.0f} t en total, {m25['spacex_t']:.0f} t de SpaceX "
                          f"({100 * m25['spacex_share']:.0f} %), {m25['starlink_t']:.0f} t de Starlink."}
    return save(fig, f"{'world_' if lang == 'es' else ''}mass_to_orbit.png",
                "Masa a órbita" if lang == "es" else "Mass to orbit", cap[lang])


def reuse(t, f, lang, save):
    L = T[lang]
    b = t["boosters"]
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(13, 5.5), gridspec_kw={"width_ratios": [2.2, 1]})
    ax.scatter(b.date, b.flight_no, s=9, color=COLORS["SpaceX"], linewidths=0, alpha=0.85)
    top = f["booster_most_flights"]
    rec = b[b.booster.eq(top["booster"])]
    ax.plot(rec.date, rec.flight_no, color=HIGHLIGHT, lw=1.4)
    ax.annotate(f"{top['booster']}: {top['flights']}", (rec.date.iloc[-1], rec.flight_no.iloc[-1]),
                xytext=(-95, -4), textcoords="offset points", color=HIGHLIGHT, fontsize=10)
    ax.set_ylabel(L["reuse_y"])
    ax.grid(axis="y")
    ax.set_axisbelow(True)
    ax.set_title(L["reuse_t"], fontsize=12)
    med = pd.Series(f["median_turnaround_days"]).rename(index=int)
    med = med[med.index >= 2018]
    ax2.bar(med.index, med.values, color=COLORS["SpaceX"], width=0.7)
    for y, v in med.items():
        ax2.text(y, v + 2, f"{v:.0f}", ha="center", color=INK, fontsize=8)
    ax2.set_ylabel(L["turn_y"])
    ax2.set_title(L["turn_t"], fontsize=11)
    ax2.set_xticks(med.index[::2])
    _source(fig, lang, f)
    fast = f["fastest_turnaround"]
    cap = {"en": "", "es": f"{f['falcon_core_flights']} vuelos de primeras etapas Falcon con número de serie en GCAT; "
                          f"{f['falcon_core_flights_reflown']} fueron re-vuelos. Récord: {top['booster']} con "
                          f"{top['flights']} vuelos. Re-vuelo más rápido: {fast['booster']} en {fast['days']:.1f} días."}
    return save(fig, f"{'world_' if lang == 'es' else ''}falcon_reuse.png",
                "Reutilización de propulsores" if lang == "es" else "Booster reuse", cap[lang])


def success(t, f, lang, save):
    L = T[lang]
    d = t["launches"].assign(decade=lambda x: (x.year // 10) * 10)
    groups = ["USSR/Russia", "USA (other)", "Rocket Lab", "SpaceX", "Europe", "China (state)",
              "China (commercial)", "Japan", "India", "Other"]
    lab = dict(LABELS[lang])
    lab["USA (other)"] = "EE. UU. (otros)" if lang == "es" else "USA (other)"
    lab["Rocket Lab"] = "Rocket Lab"
    rate = d.pivot_table(index="group", columns="decade", values="success", aggfunc="mean").reindex(groups)
    n = d.pivot_table(index="group", columns="decade", values="tag", aggfunc="count").reindex(groups)
    fig, ax = plt.subplots(figsize=(11, 6))
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("blue", ["#1b2a45", "#2a5ea8", "#3987e5", "#9cc6ff"])
    ax.imshow(rate.values, cmap=cmap, vmin=0.4, vmax=1.0, aspect="auto")
    for i in range(rate.shape[0]):
        for j in range(rate.shape[1]):
            v, k = rate.values[i, j], n.values[i, j]
            if np.isnan(v):
                continue
            pct = f"{100 * v:.1f}" if 0.995 <= v < 1 else f"{100 * v:.0f}"
            ax.text(j, i, f"{pct}%\n[{int(k)}]", ha="center", va="center", fontsize=8,
                    color="#0b0e14" if v > 0.84 else INK)
    ax.set_xticks(range(rate.shape[1]))
    ax.set_xticklabels([f"{c}s" if lang == "en" else f"{c}s" for c in rate.columns])
    ax.set_yticks(range(len(groups)))
    ax.set_yticklabels([lab[g] for g in groups])
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)
    ax.set_title(L["succ_t"])
    _source(fig, lang, f)
    cap = {"en": "", "es": "Porcentaje de intentos con éxito (código S de GCAT) por operador y década; "
                          "entre corchetes, número de intentos. La década de 2020 incluye 2026 hasta noviembre."}
    return save(fig, f"{'world_' if lang == 'es' else ''}success_by_decade.png",
                "Tasa de éxito por década" if lang == "es" else "Success by decade", cap[lang])


def spacex_vs_rest(t, f, lang, save, year=2025):
    L = T[lang]
    Y = _fig_table(t["by_year"]).loc[year]
    fig, ax = plt.subplots(figsize=(11, 4.2))
    ax.barh([1], [Y["SpaceX"]], color=COLORS["SpaceX"], height=0.6)
    left = 0
    rest = [g for g in FIG_GROUPS if g != "SpaceX"]
    small = []
    for g in rest:
        ax.barh([0], [Y[g]], left=left, color=COLORS[g], height=0.6, edgecolor=BG, linewidth=1.5)
        if Y[g] >= 10:
            ax.text(left + Y[g] / 2, 0, f"{SHORT[lang].get(g, g)}\n{int(Y[g])}", ha="center",
                    va="center", fontsize=7.5, color="#0b0e14")
        elif Y[g] > 0:
            small.append((left + Y[g] / 2, g))
        left += Y[g]
    # Segments too narrow for an inside label: label below the bar with a leader line, staggered.
    for i, (x, g) in enumerate(small):
        name = SHORT[lang].get(g, g).replace("\n", " ")
        yl = -0.55 - 0.28 * (i % 2)
        ax.plot([x, x], [-0.31, yl + 0.08], color=COLORS[g], lw=1)
        upper = i % 2 == 0  # upper-row labels start at their line so lower-row lines never cross them
        ax.text(x - 0.6 if upper else x, yl, f"{name} {int(Y[g])}", ha="left" if upper else "center", va="top",
                fontsize=8, color=COLORS[g], weight="bold")
    ax.set_ylim(-1.05, 1.45)
    ax.text(Y["SpaceX"] + 3, 1, f"{int(Y['SpaceX'])}", va="center", color=INK, fontsize=13, weight="bold")
    ax.text(left + 3, 0, f"{int(left)}", va="center", color=INK, fontsize=13, weight="bold")
    ax.set_yticks([0, 1])
    ax.set_yticklabels([L["rest_world"], L["rest_spx"]], fontsize=12)
    ax.set_xlabel(L["launches"] + f" ({year})")
    ax.set_xlim(0, max(Y["SpaceX"], left) * 1.12)
    ax.set_title(L["rest_t"])
    ax.tick_params(axis="y", length=0)
    _source(fig, lang, f, y=-0.06)
    cap = {"en": "", "es": f"En {year} SpaceX hizo {int(Y['SpaceX'])} intentos de lanzamiento orbital "
                          f"(incluidos {f['years']['2025' if '2025' in f['years'] else 2025]['spacex_starship']} "
                          f"vuelos de Starship) y el resto del mundo junto, {int(left)}."}
    return save(fig, f"{'world_' if lang == 'es' else ''}spacex_vs_rest_{year}.png",
                f"SpaceX contra el resto ({year})" if lang == "es" else "SpaceX vs rest", cap[lang])


SHORT = {"en": {"China (commercial)": "China\ncommercial", "China (state)": "China state",
                "USA (other)": "USA other\n+ Rocket Lab", "USSR/Russia": "Russia", "Other": "Others"},
         "es": {"China (commercial)": "China\ncomercial", "China (state)": "China estatal",
                "USA (other)": "EE. UU. otros\n+ Rocket Lab", "USSR/Russia": "Rusia", "Europe": "Europa",
                "Japan": "Japón", "Other": "Otros"}}

ALL = [per_year, spacex_share, china, mass, reuse, success, spacex_vs_rest]


def render_all(tables, facts, lang="en", save=None):
    save = save or _default_save
    return [fn(tables, facts, lang, save) for fn in ALL]
