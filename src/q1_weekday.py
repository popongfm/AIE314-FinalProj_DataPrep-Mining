"""Question 1 — weekday vs weekend usage (owner: member A).

Question: How does daily usage differ between weekdays and Sat/Sun, how does it vary by
day of week, and does the pattern change from month to month?

Status: select_rows() is done. Functions marked TODO(A) define the contract (inputs,
output columns, formulas) and are checked by tests/test_q1_weekday.py once implemented.
"""
from __future__ import annotations

import pandas as pd

import features
import prep

OUTPUT_FILE = "q1_daily_features.csv"


def select_rows(df: pd.DataFrame, year_be: int = 2568) -> pd.DataFrame:
    """Passenger rows for one full year, keeping only days with a real value.

    Drops: unit=คัน, excluded series, aggregates (via prep.passenger_rows), NaN values and
    zeros that belong to a long zero run (not reported, so they must not pull averages down).
    """
    rows = prep.passenger_rows(df)
    return rows[(rows["year_be"] == year_be) & (~rows["missing_flag"]) & (~rows["zero_long_run"])].copy()


def build_daily_features(rows: pd.DataFrame) -> pd.DataFrame:
    """TODO(A): one row per service x date with the Q1 features.

    Output = input columns + features.add_calendar_features() columns + dow_index, where
        dow_index = value / mean(value of that service over the whole year) * 100
    so a service at its yearly average scores 100 on any day. This is the table saved as
    data/prepared/q1_daily_features.csv.
    """
    raise NotImplementedError("TODO(A): build_daily_features")


def weekend_ratio_table(daily: pd.DataFrame, by: tuple[str, ...] = ("service", "month")) -> pd.DataFrame:
    """TODO(A): weekday vs weekend averages per group.

    Output columns: *by, weekday_mean, weekend_mean, weekend_ratio, pct_diff_weekend where
        weekend_ratio    = weekend_mean / weekday_mean      (< 1: commuter-like, > 1: leisure-like)
        pct_diff_weekend = (weekend_ratio - 1) * 100
    Groups with no weekday or no weekend days get NaN, not 0 or inf.
    """
    raise NotImplementedError("TODO(A): weekend_ratio_table")


def plot_dow_index(daily: pd.DataFrame, group: str = "purpose"):
    """TODO(A): mean dow_index Monday->Sunday, one line or bar group per `group`. Returns a Figure."""
    raise NotImplementedError("TODO(A): plot_dow_index")


def plot_month_dow_heatmap(daily: pd.DataFrame, purpose: str | None = None):
    """TODO(A): heatmap month (rows) x day of week (cols) of mean dow_index. Returns a Figure."""
    raise NotImplementedError("TODO(A): plot_month_dow_heatmap")


def main(df: pd.DataFrame) -> pd.DataFrame:
    """Build features, save the prepared CSV and figures. Called by run_all.py."""
    import plots

    daily = build_daily_features(select_rows(df))
    daily.to_csv(prep.PREPARED_DIR / OUTPUT_FILE, index=False, encoding="utf-8-sig")
    plots.save_fig(plot_dow_index(daily), "q1_dow_index")
    plots.save_fig(plot_month_dow_heatmap(daily), "q1_month_dow_heatmap")
    return daily
