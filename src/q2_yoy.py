"""Question 2 — early 2569 vs the same period of 2568 (owner: member B).

Question: How did usage change from the same period last year, and how do different ways of
handling missing values and zeros change the ranking or the conclusion?

Status: comparison_window(), filter_window(), select_rows() and SCENARIOS are done.
Functions marked TODO(B) define the contract and are checked by tests/test_q2_yoy.py.
"""
from __future__ import annotations

import pandas as pd

import features  # noqa: F401  (used in yoy_table)
import prep

OUTPUT_FILE = "q2_yoy_comparison.csv"
SENSITIVITY_FILE = "q2_missing_sensitivity.csv"
BASE_YEAR, NEW_YEAR = 2568, 2569

# Ways of handling missing values / zeros. S1 is the reference; S5 shows what goes wrong.
SCENARIOS = {
    "S1": "ตัด NaN ออก, เก็บศูนย์ไว้เป็นค่าจริง",
    "S2": "ศูนย์ที่อยู่ในช่วงศูนย์ยาว (zero_long_run) ถือเป็น NaN แล้วตัดออก",
    "S3": "Paired days: ใช้เฉพาะวันที่ทั้งสองปีมีค่าที่ไม่ใช่ NaN และไม่ใช่ศูนย์ช่วงยาว",
    "S4": "เติม NaN ด้วย median ของวันเดียวกันในสัปดาห์ เดือนเดียวกัน บริการเดียวกัน",
    "S5": "แทน NaN ด้วย 0 (ตัวอย่างวิธีที่ผิด)",
}


def comparison_window(df: pd.DataFrame) -> tuple[int, int]:
    """(month, day) of the last date with data in NEW_YEAR, e.g. (3, 11).

    Computed from the data, so the window updates automatically if 2569 data is extended.
    """
    last = df.loc[df["year_be"] == NEW_YEAR, "date"].max()
    return last.month, last.day


def filter_window(df: pd.DataFrame, end: tuple[int, int]) -> pd.DataFrame:
    """Rows from 1 Jan to `end` (month, day) inclusive, in every year."""
    m, d = df["date"].dt.month, df["date"].dt.day
    return df[(m < end[0]) | ((m == end[0]) & (d <= end[1]))].copy()


def select_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Passenger-unit, non-aggregate rows inside the comparison window, both years.

    Unlike Q1, NaN rows and all-zero series are KEPT so the scenarios S1–S5 can treat them
    differently. The day/weekend counts of the window are checked in tests/test_q2_yoy.py.
    """
    rows = df[(df["unit"] == "คน") & (~df["is_aggregate"])]
    return filter_window(rows, comparison_window(df))


def apply_scenario(rows: pd.DataFrame, code: str) -> pd.DataFrame:
    """TODO(B): return the rows with `value` handled according to SCENARIOS[code].

    Rows removed by the scenario are dropped; rows filled by the scenario get the filled
    value. Must not modify `rows` in place. Unknown code -> ValueError.
    """
    raise NotImplementedError("TODO(B): apply_scenario")


def yoy_table(rows: pd.DataFrame) -> pd.DataFrame:
    """TODO(B): one row per service with the Q2 features (rows already passed through a scenario).

    Output columns: service, purpose, mode, avg_daily_68, avg_daily_69, abs_change,
    yoy_change_pct, coverage_68, coverage_69, rank where
        avg_daily_YY   = mean of the valid daily values of that year in the window
        abs_change     = avg_daily_69 - avg_daily_68
        yoy_change_pct = features.safe_pct_change(avg_daily_69, avg_daily_68)
        coverage_YY    = valid days / days in the window for that year
        rank           = rank of yoy_change_pct, 1 = largest increase (NaN stays NaN)
    """
    raise NotImplementedError("TODO(B): yoy_table")


def run_scenarios(rows: pd.DataFrame, codes: tuple[str, ...] = tuple(SCENARIOS)) -> pd.DataFrame:
    """TODO(B): long table of yoy_table() under every scenario.

    Output columns: scenario, service, yoy_change_pct, rank. Saved as q2_missing_sensitivity.csv.
    """
    raise NotImplementedError("TODO(B): run_scenarios")


def rank_stability(sensitivity: pd.DataFrame, reference: str = "S1") -> pd.DataFrame:
    """TODO(B): how much each scenario's ranking differs from the reference.

    Output columns: scenario, spearman_vs_reference, n_services_moved_2plus, n_services_ranked.
    """
    raise NotImplementedError("TODO(B): rank_stability")


def plot_yoy_bars(table: pd.DataFrame):
    """TODO(B): diverging horizontal bar of yoy_change_pct per service. Returns a Figure."""
    raise NotImplementedError("TODO(B): plot_yoy_bars")


def plot_rank_by_scenario(sensitivity: pd.DataFrame):
    """TODO(B): slope chart or heatmap of rank per service across S1–S5. Returns a Figure."""
    raise NotImplementedError("TODO(B): plot_rank_by_scenario")


def main(df: pd.DataFrame) -> pd.DataFrame:
    """Build tables, save the prepared CSVs and figures. Called by run_all.py."""
    import plots

    rows = select_rows(df)
    table = yoy_table(apply_scenario(rows, "S2"))  # TODO(B): confirm the main scenario with the team at M2
    sensitivity = run_scenarios(rows)
    table.to_csv(prep.PREPARED_DIR / OUTPUT_FILE, index=False, encoding="utf-8-sig")
    sensitivity.to_csv(prep.PREPARED_DIR / SENSITIVITY_FILE, index=False, encoding="utf-8-sig")
    plots.save_fig(plot_yoy_bars(table), "q2_yoy_bars")
    plots.save_fig(plot_rank_by_scenario(sensitivity), "q2_rank_by_scenario")
    return table
