"""Question 3 — international arrivals vs departures (owner: member C).

Question: How do international arrivals and departures differ by mode of travel, month by
month, and how volatile is each within the year?

Contract (inputs, output columns, formulas) is in each docstring and checked by
tests/test_q3_intl.py.
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
    """One row per mode x year_month with arrivals and departures side by side.

    Output columns: mode, year_month, month, arrival, departure (monthly passengers summed over
    the ports of that mode). A month with missing days uses avg_daily * days, so a missing
    day does not look like a drop; when coverage is 1 this equals the plain monthly sum.
    """
    data = rows[rows["year_be"] == year_be]
    per_port = features.monthly_from_daily(data, ["mode", "port", "direction"])
    per_port["estimated"] = per_port["avg_daily"] * per_port["days"]
    flows = (per_port.pivot_table(index=["mode", "year_month"], columns="direction",
                                  values="estimated", aggfunc="sum")
                     .reindex(columns=["arrival", "departure"])
                     .reset_index())
    flows.columns.name = None
    flows["month"] = flows["year_month"].str[-2:].astype(int)
    return flows[["mode", "year_month", "month", "arrival", "departure"]]


def add_flow_features(monthly: pd.DataFrame) -> pd.DataFrame:
    """Add the Q3 features to monthly_flows() output.

        net_flow          = arrival - departure
        arr_dep_ratio     = arrival / departure                 (NaN if departure == 0)
        mom_pct_arrival   = month-over-month % change of arrival within each mode
        mom_pct_departure = same for departure
        mode_share        = (arrival + departure) / total of all modes in that month
    This table is saved as data/prepared/q3_international_monthly.csv.
    """
    out = monthly.sort_values(["mode", "year_month"]).copy()
    out["net_flow"] = out["arrival"] - out["departure"]
    out["arr_dep_ratio"] = out["arrival"] / out["departure"].where(out["departure"] != 0)
    for direction in ["arrival", "departure"]:
        previous = out.groupby("mode")[direction].shift(1)
        out[f"mom_pct_{direction}"] = features.safe_pct_change(out[direction], previous)
    both = out["arrival"] + out["departure"]
    out["mode_share"] = both / both.groupby(out["year_month"]).transform("sum")
    return out.reset_index(drop=True)


def volatility_table(monthly: pd.DataFrame) -> pd.DataFrame:
    """Within-year volatility per mode x direction.

    Output columns: mode, direction, mean_monthly, std_monthly, cv_within_year, peak_month,
    low_month where cv_within_year = std_monthly / mean_monthly (sample std, ddof=1).
    CV lets modes of very different size be compared on one scale.
    """
    long = monthly.melt(id_vars=["mode", "month"], value_vars=["arrival", "departure"],
                        var_name="direction", value_name="passengers")
    grouped = long.groupby(["mode", "direction"])
    vol = grouped["passengers"].agg(mean_monthly="mean", std_monthly="std").reset_index()
    vol["cv_within_year"] = vol["std_monthly"] / vol["mean_monthly"]
    peaks = long.loc[grouped["passengers"].idxmax(), ["mode", "direction", "month"]]
    lows = long.loc[grouped["passengers"].idxmin(), ["mode", "direction", "month"]]
    vol = (vol.merge(peaks.rename(columns={"month": "peak_month"}), on=["mode", "direction"])
              .merge(lows.rename(columns={"month": "low_month"}), on=["mode", "direction"]))
    return vol.sort_values("cv_within_year", ascending=False).reset_index(drop=True)


def plot_arrival_departure(monthly: pd.DataFrame):
    """Monthly arrivals vs departures, one panel per mode (own y-axis each). Returns a Figure."""
    import matplotlib.pyplot as plt
    import plots

    fig, axes = plt.subplots(2, 2, figsize=(12, 7.5), sharex=True)
    for ax, mode in zip(axes.flat, plots.MODE_ORDER):
        data = monthly[monthly["mode"] == mode].sort_values("month")
        for direction in ["arrival", "departure"]:
            ax.plot(data["month"], data[direction] / 1000, marker="o", linewidth=2,
                    color=plots.DIRECTION_COLORS[direction], label=plots.DIRECTION_LABEL_TH[direction])
        ax.set_title(plots.MODE_LABEL_TH[mode])
        ax.set_ylabel("พันคน/เดือน")
        ax.set_xticks(range(1, 13), plots.MONTH_TH, fontsize=8.5)
    axes.flat[0].legend(frameon=False)
    fig.suptitle("ผู้โดยสารระหว่างประเทศ ขาเข้า vs ขาออก รายเดือน ปี 2568 (แกน y แยกแต่ละรูปแบบ)", fontsize=13)
    fig.tight_layout()
    return fig


def plot_arr_dep_ratio(monthly: pd.DataFrame):
    """arr_dep_ratio by month, one line per mode, on a shared scale. Returns a Figure."""
    import matplotlib.pyplot as plt
    import plots

    fig, ax = plt.subplots(figsize=(9.5, 4.5))
    for mode in plots.MODE_ORDER:
        data = monthly[monthly["mode"] == mode].sort_values("month")
        ax.plot(data["month"], data["arr_dep_ratio"], marker="o", linewidth=2, label=plots.MODE_LABEL_TH[mode])
    ax.axhline(1, color="#555", linewidth=1, linestyle="--")
    ax.set_xticks(range(1, 13), plots.MONTH_TH)
    ax.set_ylabel("ขาเข้า ÷ ขาออก  (> 1 = เข้ามากกว่าออก)")
    ax.set_title("อัตราส่วนขาเข้าต่อขาออก รายเดือน ปี 2568")
    ax.legend(frameon=False, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.12))
    return fig


def plot_volatility(vol: pd.DataFrame):
    """Bar chart of cv_within_year by mode and direction. Returns a Figure."""
    import matplotlib.pyplot as plt
    import numpy as np
    import plots

    modes = [m for m in plots.MODE_ORDER if m in set(vol["mode"])]
    x = np.arange(len(modes))
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for i, direction in enumerate(["arrival", "departure"]):
        values = vol.set_index(["mode", "direction"]).loc[[(m, direction) for m in modes], "cv_within_year"]
        bars = ax.bar(x + (i - 0.5) * 0.38, values, width=0.38, color=plots.DIRECTION_COLORS[direction],
                      label=plots.DIRECTION_LABEL_TH[direction])
        ax.bar_label(bars, fmt="%.2f", fontsize=9)
    ax.set_xticks(x, [plots.MODE_LABEL_TH[m] for m in modes])
    ax.set_ylabel("CV = std / mean ของยอดรายเดือน")
    ax.set_title("ความผันผวนภายในปี 2568 ของผู้โดยสารระหว่างประเทศ")
    ax.legend(frameon=False)
    ax.grid(axis="x", visible=False)
    return fig


def main(df: pd.DataFrame) -> pd.DataFrame:
    """Build features, save the prepared CSV and figures. Called by run_all.py."""
    import matplotlib.pyplot as plt
    import plots

    monthly = add_flow_features(monthly_flows(select_rows(df)))
    vol = volatility_table(monthly)
    monthly.to_csv(prep.PREPARED_DIR / OUTPUT_FILE, index=False, encoding="utf-8-sig")
    for name, fig in [("q3_arrival_departure", plot_arrival_departure(monthly)),
                      ("q3_arr_dep_ratio", plot_arr_dep_ratio(monthly)),
                      ("q3_volatility", plot_volatility(vol))]:
        plots.save_fig(fig, name)
        plt.close(fig)
    return monthly
