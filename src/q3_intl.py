"""Question 3 — international arrivals vs departures (owner: member C).

Question: How do international arrivals and departures differ by mode of travel, month by
month, and how volatile is each within the year?

Status: select_rows() and coverage_table() are done. Functions marked TODO(C) define the
contract and are checked by tests/test_q3_intl.py once implemented.
"""
from __future__ import annotations

import pandas as pd

import features
import prep

OUTPUT_FILE = "q3_international_monthly.csv"


def select_rows(df: pd.DataFrame) -> pd.DataFrame:
    """International passenger rows; every port must have both an arrival and a departure series."""
    rows = prep.passenger_rows(df)
    rows = rows[rows["purpose"] == "international"].copy()
    directions = rows.groupby("port")["direction"].agg(set)
    unpaired = directions[directions != {"arrival", "departure"}]
    if len(unpaired):
        raise ValueError(f"ports without both directions: {unpaired.to_dict()}")
    return rows


def coverage_table(rows: pd.DataFrame) -> pd.DataFrame:
    """Months where some days have no value — decide total vs avg_daily before aggregating."""
    monthly = features.monthly_from_daily(rows, ["year_be", "mode", "port", "direction"])
    return monthly[monthly["coverage"] < 1]


def monthly_flows(rows: pd.DataFrame, year_be: int = 2568) -> pd.DataFrame:
    """TODO(C): one row per mode x year_month with arrivals and departures side by side.

    Output columns: mode, year_month, arrival, departure (monthly passengers summed over the
    ports of that mode). Use features.monthly_from_daily(); for months with coverage < 1 use
    avg_daily * days so a missing day does not look like a drop.
    """
    raise NotImplementedError("TODO(C): monthly_flows")


def add_flow_features(monthly: pd.DataFrame) -> pd.DataFrame:
    """TODO(C): add the Q3 features to monthly_flows() output.

        net_flow        = arrival - departure
        arr_dep_ratio   = arrival / departure                 (NaN if departure == 0)
        mom_pct_arrival = month-over-month % change of arrival within each mode
        mom_pct_departure = same for departure
        mode_share      = (arrival + departure) / total of all modes in that month
    This table is saved as data/prepared/q3_international_monthly.csv.
    """
    raise NotImplementedError("TODO(C): add_flow_features")


def volatility_table(monthly: pd.DataFrame) -> pd.DataFrame:
    """TODO(C): within-year volatility per mode x direction.

    Output columns: mode, direction, mean_monthly, std_monthly, cv_within_year
    where cv_within_year = std_monthly / mean_monthly.
    """
    raise NotImplementedError("TODO(C): volatility_table")


def plot_arrival_departure(monthly: pd.DataFrame):
    """TODO(C): monthly arrivals vs departures, one panel per mode (own y-axis each). Returns a Figure."""
    raise NotImplementedError("TODO(C): plot_arrival_departure")


def plot_volatility(vol: pd.DataFrame):
    """TODO(C): bar chart of cv_within_year by mode and direction. Returns a Figure."""
    raise NotImplementedError("TODO(C): plot_volatility")


def main(df: pd.DataFrame) -> pd.DataFrame:
    """Build features, save the prepared CSV and figures. Called by run_all.py."""
    import plots

    monthly = add_flow_features(monthly_flows(select_rows(df)))
    vol = volatility_table(monthly)
    monthly.to_csv(prep.PREPARED_DIR / OUTPUT_FILE, index=False, encoding="utf-8-sig")
    plots.save_fig(plot_arrival_departure(monthly), "q3_arrival_departure")
    plots.save_fig(plot_volatility(vol), "q3_volatility")
    return monthly
