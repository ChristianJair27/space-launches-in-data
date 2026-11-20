"""Every orbital launch in history, from Jonathan McDowell's GCAT.

Data: McDowell, J., 2020: General Catalog of Artificial Space Objects,
https://planet4589.org/space/gcat (CC BY 4.0).

Run everything with ``python -m worldspace`` (download, tables, figures,
animations, cross-check). Paths can be redirected with the environment
variable ``WORLDSPACE_DATA`` (default: ``<project>/data/world_space``).
"""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("WORLDSPACE_DATA", ROOT / "data" / "world_space"))
RAW = DATA / "raw"            # untouched GCAT files
DERIVED = DATA / "derived"    # our tables (CSV/JSON)
FIGURES = Path(os.environ.get("WORLDSPACE_FIGURES", ROOT / "figures"))
VIDEO = Path(os.environ.get("WORLDSPACE_VIDEO", ROOT / "media"))
