"""Dark figure style (same palette as the Kister Space dashboard) and bilingual labels.

Categorical colours are the eight dark-surface steps of a palette validated for
colour-vision deficiency on adjacent pairs; the stacking order below follows the
validated slot order so neighbouring bands stay distinguishable. A ninth group
folds into a neutral grey ("Other").
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

BG = "#0b0e14"
INK = "#e6e9ef"
MUTED = "#8b93a7"
GRID = "#2a3142"
HIGHLIGHT = "#ffd34d"

# Figure groups, bottom-to-top stacking order = validated palette slot order.
FIG_GROUPS = ["SpaceX", "China (commercial)", "Europe", "China (state)", "Japan", "India",
              "USA (other)", "USSR/Russia", "Other"]
COLORS = {
    "SpaceX": "#3987e5", "China (commercial)": "#d95926", "Europe": "#199e70",
    "China (state)": "#c98500", "Japan": "#d55181", "India": "#0ca30c",
    "USA (other)": "#9085e9", "USSR/Russia": "#e66767", "Other": "#6b7280",
}

LABELS = {
    "en": {
        "SpaceX": "SpaceX", "China (commercial)": "China (commercial)", "Europe": "Europe",
        "China (state)": "China (state)", "Japan": "Japan", "India": "India",
        "USA (other)": "USA (other, incl. Rocket Lab)", "USSR/Russia": "USSR / Russia",
        "Other": "Other countries",
    },
    "es": {
        "SpaceX": "SpaceX", "China (commercial)": "China (comercial)", "Europe": "Europa",
        "China (state)": "China (estatal)", "Japan": "Japón", "India": "India",
        "USA (other)": "EE. UU. (otros, incl. Rocket Lab)", "USSR/Russia": "URSS / Rusia",
        "Other": "Otros países",
    },
}

SOURCE = {
    "en": "Data: J. McDowell, GCAT (planet4589.org), CC BY 4.0 · update {upd}",
    "es": "Datos: J. McDowell, GCAT (planet4589.org), CC BY 4.0 · actualización {upd}",
}


def fig_group(group: str) -> str:
    """Map the ten analysis groups onto the nine figure groups."""
    return "USA (other)" if group == "Rocket Lab" else group


def apply() -> None:
    plt.rcParams.update({
        "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
        "text.color": INK, "axes.labelcolor": MUTED, "axes.edgecolor": GRID,
        "xtick.color": MUTED, "ytick.color": MUTED, "font.size": 11,
        "axes.titlesize": 14, "axes.titleweight": "bold", "axes.titlelocation": "left",
        "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False,
        "grid.color": GRID, "grid.linewidth": 0.6,
    })


apply()
