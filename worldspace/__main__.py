"""python -m worldspace [--refresh] [--figures DIR] [--lang en|es] [--video] [--no-crosscheck]

1. download GCAT files (only if missing, or with --refresh)
2. build tables and facts -> data/world_space/derived/
3. figures -> --figures (default ./figures)
4. --lang es: Spanish labels (figures get a world_ prefix)
5. --video: racing-bar MP4s (1080x1920 Short, 1920x1080 long-form)
6. Wikipedia cross-check for 2024-2025 -> derived/crosscheck_wikipedia.csv
"""

import argparse
import os
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--refresh", action="store_true", help="re-download GCAT files")
    p.add_argument("--figures", type=Path, help="output folder for figures")
    p.add_argument("--lang", default="en", choices=["en", "es"], help="figure language")
    p.add_argument("--video", action="store_true", help="render the MP4 animations")
    p.add_argument("--no-crosscheck", action="store_true")
    a = p.parse_args()
    if a.figures:
        os.environ["WORLDSPACE_FIGURES"] = str(a.figures)

    import worldspace
    if a.figures:
        worldspace.FIGURES = a.figures
    from worldspace import analysis, figures, gcat

    figures.FIGURES = worldspace.FIGURES
    gcat.download(force=a.refresh)
    t = analysis.build()
    f = analysis.facts(t)
    analysis.save(t, f)
    print(f"GCAT update {f['gcat_updated']}: {f['attempts_total']} orbital attempts, "
          f"{f['successes_total']} successes")
    print("figures:", figures.render_all(t, f, a.lang))
    if not a.no_crosscheck:
        from worldspace import crosscheck
        c = crosscheck.compare(t["launches"])
        c.to_csv(worldspace.DERIVED / "crosscheck_wikipedia.csv")
        print(c)
    if a.video:
        from worldspace import animate
        for path in animate.render_all(t, f, a.lang):
            print("video:", path)


if __name__ == "__main__":
    main()
