"""Racing-bar animation: orbital launch attempts in the previous 12 months, by operator, 1958-2026.

Frames are drawn with matplotlib and piped to ffmpeg (libx264, yuv420p, 30 fps):
  * ``launch_race_short.mp4``    1080x1920 (YouTube Short), ~32 s
  * ``launch_race_longform.mp4`` 1920x1080 (long-form), ~60 s
Every frame carries the data source on screen.
"""

from __future__ import annotations

import shutil
import subprocess

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from . import VIDEO
from .style import BG, COLORS, FIG_GROUPS, INK, MUTED, fig_group

FPS = 30
VLABELS = {
    "en": {"SpaceX": "SpaceX", "China (state)": "China state", "China (commercial)": "China commercial",
           "USA (other)": "Other USA*", "USSR/Russia": "USSR / Russia", "Europe": "Europe",
           "Japan": "Japan", "India": "India", "Other": "Rest of world"},
    "es": {"SpaceX": "SpaceX", "China (state)": "China estatal", "China (commercial)": "China comercial",
           "USA (other)": "Resto de EE. UU.*", "USSR/Russia": "URSS / Rusia", "Europe": "Europa",
           "Japan": "Japón", "India": "India", "Other": "Resto del mundo"},
}
FOOT = {"en": "*incl. Rocket Lab", "es": "*incluye Rocket Lab"}


def monthly_rolling(launches: pd.DataFrame) -> pd.DataFrame:
    """Launch attempts in the 12 months ending with each month, per figure group."""
    d = launches.assign(g=launches.group.map(fig_group), m=launches.date.dt.to_period("M"))
    counts = d.pivot_table(index="m", columns="g", values="tag", aggfunc="count", fill_value=0)
    months = pd.period_range("1957-10", d.m.max() - 1, freq="M")   # drop the partial last month
    counts = counts.reindex(months, fill_value=0).reindex(columns=FIG_GROUPS, fill_value=0)
    roll = counts.rolling(12, min_periods=1).sum()
    cum = counts.sum(axis=1).cumsum()
    roll["_cum"] = cum
    return roll.loc[pd.Period("1958-09", "M"):]


def _ffmpeg(path, w, h):
    exe = shutil.which("ffmpeg") or "ffmpeg"
    return subprocess.Popen([exe, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba",
                             "-s", f"{w}x{h}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
                             "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                             "-movflags", "+faststart", str(path)], stdin=subprocess.PIPE)


def render(launches: pd.DataFrame, facts: dict, path, w=1080, h=1920, per_month=1, hold_s=4.0,
           lang="en") -> str:
    data = monthly_rolling(launches)
    groups = FIG_GROUPS
    vals = data[groups].to_numpy(float)
    cum = data["_cum"].to_numpy(float)
    months = data.index
    # Frame-level interpolation between months
    n = len(months)
    t = np.linspace(0, n - 1, (n - 1) * per_month + 1)
    i0 = np.floor(t).astype(int)
    i1 = np.minimum(i0 + 1, n - 1)
    a = (t - i0)[:, None]
    fv = vals[i0] * (1 - a) + vals[i1] * a
    fc = cum[i0] * (1 - a[:, 0]) + cum[i1] * a[:, 0]
    hold = int(hold_s * FPS)
    frames = list(range(len(t))) + [len(t) - 1] * hold

    vertical = h > w
    dpi = 100
    fig = plt.figure(figsize=(w / dpi, h / dpi), dpi=dpi, facecolor=BG)
    if vertical:
        ax = fig.add_axes([0.40, 0.20, 0.50, 0.55])
        title_y, year_y, fs = 0.93, 0.84, 1.0
    else:
        ax = fig.add_axes([0.24, 0.10, 0.50, 0.72])
        title_y, year_y, fs = 0.92, 0.50, 1.0
    lab = VLABELS[lang]
    vmax_run = 10.0
    pos = {g: k for k, g in enumerate(groups)}
    rank_of = dict(pos)
    sep = "\n" if vertical else " "
    txt = {"en": (f"Orbital launches,{sep}previous 12 months",
                  "total since Sputnik", "Data: J. McDowell, GCAT (planet4589.org), CC BY 4.0 · update {u}"),
           "es": (f"Lanzamientos orbitales,{sep}últimos 12 meses",
                  "total desde el Sputnik", "Datos: J. McDowell, GCAT (planet4589.org), CC BY 4.0 · {u}")}[lang]
    proc = _ffmpeg(path, w, h)
    try:
        for k in frames:
            v = fv[k]
            # Hysteresis: a bar must lead by more than half a launch to overtake, so
            # near-ties do not flicker; positions then ease towards their rank.
            order = sorted(range(len(groups)), key=lambda gi: rank_of[groups[gi]])
            swapped = True
            while swapped:          # bubble pass: swap neighbours only on a clear lead
                swapped = False
                for r in range(len(order) - 1):
                    if v[order[r + 1]] > v[order[r]] + 0.5:
                        order[r], order[r + 1] = order[r + 1], order[r]
                        swapped = True
            for rank, gi in enumerate(order):
                g = groups[gi]
                rank_of[g] = rank
                pos[g] += 0.45 * (rank - pos[g])
            vmax_run = max(vmax_run * 0.985, v.max() * 1.15, 10)
            ax.clear()
            ax.set_facecolor(BG)
            for gi, g in enumerate(groups):
                y = pos[g]
                ax.barh(y, v[gi], color=COLORS[g], height=0.78)
                ax.text(-vmax_run * 0.02, y, lab[g], ha="right", va="center", color=INK,
                        fontsize=(26 if vertical else 22) * fs)
                ax.text(v[gi] + vmax_run * 0.015, y, f"{v[gi]:.0f}", ha="left", va="center",
                        color=INK, fontsize=(28 if vertical else 22) * fs, weight="bold")
            ax.set_xlim(0, vmax_run)
            ax.set_ylim(len(groups) - 0.4, -0.6)
            ax.axis("off")
            for txt_obj in list(fig.texts):
                txt_obj.remove()
            m = months[int(round(t[min(k, len(t) - 1)]))]
            fig.text(0.5, title_y, txt[0], ha="center", va="top", color=INK,
                     fontsize=34 if vertical else 30, weight="bold", wrap=True)
            if vertical:
                fig.text(0.5, year_y, f"{m.year}", ha="center", va="top", color=INK, fontsize=120,
                         weight="bold", alpha=0.95)
                fig.text(0.5, 0.14, f"{fc[k]:,.0f}", ha="center", color=COLORS["SpaceX"], fontsize=64,
                         weight="bold")
                fig.text(0.5, 0.115, txt[1], ha="center", color=MUTED, fontsize=26)
            else:
                fig.text(0.87, 0.55, f"{m.year}", ha="center", va="center", color=INK, fontsize=110,
                         weight="bold")
                fig.text(0.87, 0.36, f"{fc[k]:,.0f}", ha="center", color=COLORS["SpaceX"], fontsize=54,
                         weight="bold")
                fig.text(0.87, 0.31, txt[1], ha="center", color=MUTED, fontsize=22)
            sep2 = "\n" if vertical else "   "
            fig.text(0.5, 0.03, txt[2].format(u=facts["gcat_updated"][:11]) + sep2 + FOOT[lang],
                     ha="center", color=MUTED, fontsize=19 if vertical else 16, linespacing=1.5)
            fig.canvas.draw()
            buf = np.asarray(fig.canvas.buffer_rgba())
            proc.stdin.write(buf.tobytes())
    finally:
        proc.stdin.close()
        proc.wait()
        plt.close(fig)
    return str(path)


def render_all(tables, facts, lang="en"):
    VIDEO.mkdir(parents=True, exist_ok=True)
    L = tables["launches"]
    sfx = "" if lang == "en" else f"_{lang}"
    return [render(L, facts, VIDEO / f"launch_race_short{sfx}.mp4", 1080, 1920, per_month=1, lang=lang),
            render(L, facts, VIDEO / f"launch_race_longform{sfx}.mp4", 1920, 1080, per_month=2, lang=lang)]
