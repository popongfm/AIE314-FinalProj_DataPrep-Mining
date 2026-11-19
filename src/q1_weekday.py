"""Question 1 — weekday vs weekend usage (owner: member A).

Question: How does daily usage differ between weekdays and Sat/Sun, how does it vary by
day of week, and does the pattern change from month to month?

Contract (inputs, output columns, formulas) is in each docstring and checked by
tests/test_q1_weekday.py.
"""
from __future__ import annotations

import numpy as np
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
    """One row per service x date with the Q1 features.

    Output = input columns + features.add_calendar_features() columns + dow_index, where
        dow_index = value / mean(value of that service over the whole year) * 100
    so a service at its yearly average scores 100 on any day. This is the table saved as
    data/prepared/q1_daily_features.csv.
    """
    daily = features.add_calendar_features(rows)
    # Normalise each service by its own yearly mean: lets a 5,000-passenger boat line and a
    # 800,000-passenger BTS line share one axis.
    service_mean = daily.groupby("service")["value"].transform("mean")
    daily["dow_index"] = daily["value"] / service_mean * 100
    return daily


def weekend_ratio_table(daily: pd.DataFrame, by: tuple[str, ...] = ("service", "month")) -> pd.DataFrame:
    """Weekday vs weekend averages per group.

    Output columns: *by, weekday_mean, weekend_mean, weekend_ratio, pct_diff_weekend where
        weekend_ratio    = weekend_mean / weekday_mean      (< 1: commuter-like, > 1: leisure-like)
        pct_diff_weekend = (weekend_ratio - 1) * 100
    Groups with no weekday or no weekend days get NaN, not 0 or inf.
    """
    by = list(by)
    part = np.where(daily["is_weekend"], "weekend_mean", "weekday_mean")
    table = (daily.assign(part=part)
                  .pivot_table(index=by, columns="part", values="value", aggfunc="mean", observed=True)
                  .reindex(columns=["weekday_mean", "weekend_mean"])
                  .reset_index())
    table.columns.name = None
    weekday = table["weekday_mean"].where(table["weekday_mean"] > 0)
    table["weekend_ratio"] = table["weekend_mean"] / weekday
    table["pct_diff_weekend"] = (table["weekend_ratio"] - 1) * 100
    return table


def plot_dow_index(daily: pd.DataFrame, group: str = "purpose"):
    """Mean dow_index Monday->Sunday, one line per `group`. Returns a Figure.

    Each service counts equally inside its group (mean of service indices), so one very
    large service cannot dominate the shape of its group.
    """
    import matplotlib.pyplot as plt
    import plots

    per_service = daily.groupby([group, "service", "day_of_week"], observed=True)["dow_index"].mean().reset_index()
    curve = per_service.groupby([group, "day_of_week"], observed=True)["dow_index"].mean().unstack(group)
    fig, ax = plt.subplots(figsize=(9, 4.8))
    for col in curve.columns:
        n = per_service.loc[per_service[group] == col, "service"].nunique()
        label = plots.PURPOSE_LABEL_TH.get(col, col) + f" ({n} บริการ)"
        ax.plot(curve.index, curve[col], marker="o", linewidth=2.2, label=label,
                color=plots.PURPOSE_COLORS.get(col))
    ax.axhline(100, color="#555", linewidth=1, linestyle="--")
    ax.axvspan(4.5, 6.5, color="#d9822b", alpha=0.08)
    ax.set_xticks(range(7), features.WEEKDAY_TH)
    ax.set_ylabel("ดัชนีวันในสัปดาห์ (ค่าเฉลี่ยทั้งปี = 100)")
    ax.set_title("รูปแบบการใช้บริการตามวันในสัปดาห์ ปี 2568")
    ax.legend(frameon=False)
    return fig


def plot_month_dow_heatmap(daily: pd.DataFrame, purpose: str | None = None):
    """Heatmap month (rows) x day of week (cols) of mean dow_index. Returns a Figure."""
    import matplotlib.pyplot as plt
    import seaborn as sns
    import plots

    data = daily if purpose is None else daily[daily["purpose"] == purpose]
    per_service = data.groupby(["service", "month", "day_of_week"])["dow_index"].mean().reset_index()
    heat = per_service.pivot_table(index="month", columns="day_of_week", values="dow_index", aggfunc="mean")
    heat.index = [plots.MONTH_TH[m - 1] for m in heat.index]
    heat.columns = features.WEEKDAY_TH
    fig, ax = plt.subplots(figsize=(8.5, 6))
    sns.heatmap(heat, annot=True, fmt=".0f", cmap="RdBu", center=100, linewidths=0.4,
                cbar_kws={"label": "ดัชนี (ค่าเฉลี่ยทั้งปี = 100)"}, ax=ax)
    scope = "ทุกบริการ" if purpose is None else plots.PURPOSE_LABEL_TH.get(purpose, purpose)
    ax.set_title(f"ดัชนีการใช้บริการ เดือน × วันในสัปดาห์ ({scope}) ปี 2568")
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.grid(False)
    return fig


def plot_weekend_ratio_monthly(ratio: pd.DataFrame):
    """weekend_ratio by month, one line per purpose (mean over services). Returns a Figure."""
    import matplotlib.pyplot as plt
    import plots

    curve = ratio.groupby(["purpose", "month"])["weekend_ratio"].mean().unstack("purpose")
    fig, ax = plt.subplots(figsize=(9, 4.5))
    for col in curve.columns:
        ax.plot(curve.index, curve[col], marker="o", linewidth=2.2,
                label=plots.PURPOSE_LABEL_TH.get(col, col), color=plots.PURPOSE_COLORS.get(col))
    ax.axhline(1, color="#555", linewidth=1, linestyle="--")
    ax.set_xticks(range(1, 13), plots.MONTH_TH)
    ax.set_ylabel("weekend ratio (เสาร์–อาทิตย์ ÷ วันธรรมดา)")
    ax.set_title("อัตราส่วนวันหยุดต่อวันธรรมดา รายเดือน ปี 2568")
    ax.legend(frameon=False)
    return fig


def output_table(daily: pd.DataFrame) -> pd.DataFrame:
    """Columns written to q1_daily_features.csv (source keys + Q1 features only)."""
    cols = ["date", "service", "purpose", "mode", "agency", "value", "day_of_week", "day_name_th",
            "is_weekend", "month", "year_month", "dow_index"]
    return daily[cols].sort_values(["service", "date"]).reset_index(drop=True)


def main(df: pd.DataFrame) -> pd.DataFrame:
    """Build features, save the prepared CSV and figures. Called by run_all.py."""
    import matplotlib.pyplot as plt
    import plots

    daily = build_daily_features(select_rows(df))
    ratio = weekend_ratio_table(daily, by=("purpose", "service", "month"))
    output_table(daily).to_csv(prep.PREPARED_DIR / OUTPUT_FILE, index=False, encoding="utf-8-sig")
    for name, fig in [("q1_dow_index", plot_dow_index(daily)),
                      ("q1_month_dow_heatmap", plot_month_dow_heatmap(daily)),
                      ("q1_weekend_ratio_monthly", plot_weekend_ratio_monthly(ratio))]:
        plots.save_fig(fig, name)
        plt.close(fig)
    return daily
