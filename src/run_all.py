"""Rebuild every prepared dataset and figure from the raw files with one command.

    python src/run_all.py            # report which steps are still TODO, exit 0
    python src/run_all.py --strict   # fail if any step is unfinished (use before submitting)

Order: cleaning (prep) -> Q1 -> Q2 -> Q3. Each question reads only the shared clean table.
"""
from __future__ import annotations

import argparse
import sys
import traceback

import matplotlib

matplotlib.use("Agg")  # no windows when run from the terminal

import plots  # noqa: E402
import prep  # noqa: E402
import q1_weekday  # noqa: E402
import q2_yoy  # noqa: E402
import q3_intl  # noqa: E402

STEPS = [("Q1 weekday vs weekend", q1_weekday.main),
         ("Q2 year-over-year", q2_yoy.main),
         ("Q3 international", q3_intl.main)]


def main(strict: bool = False) -> int:
    plots.setup_style()
    clean_df, catalog, quality_log = prep.build_all(save=True)
    plots.save_fig(plots.plot_quality_heatmap(clean_df), "01_quality_heatmap")
    print(f"[done] cleaning: {len(clean_df):,} rows, {catalog['service'].nunique()} services")

    df = prep.load_clean()  # read back what was saved, exactly as the notebooks do
    status = {}
    for name, step in STEPS:
        try:
            step(df)
            status[name] = "done"
        except NotImplementedError as exc:
            status[name] = f"TODO ({exc})"
        except Exception:  # a real bug: show it and fail
            traceback.print_exc()
            status[name] = "ERROR"
        print(f"[{status[name].split()[0].lower()}] {name}: {status[name]}")

    if any(s == "ERROR" for s in status.values()):
        return 1
    if strict and any(s != "done" for s in status.values()):
        return 1
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--strict", action="store_true", help="fail if any step is still TODO")
    sys.exit(main(parser.parse_args().strict))
