"""Question 2 — early 2569 vs the same period of 2568 (owner: member B).

Question: How did usage change from the same period last year, and how do different ways of
handling missing values and zeros change the ranking or the conclusion?

Contract (inputs, output columns, formulas) is in each docstring and checked by
tests/test_q2_yoy.py.
"""
from __future__ import annotations

import pandas as pd

import features
import prep

OUTPUT_FILE = "q2_yoy_comparison.csv"
SENSITIVITY_FILE = "q2_missing_sensitivity.csv"
BASE_YEAR, NEW_YEAR = 2568, 2569
# Main scenario for the headline numbers. S2 because a run of >= 7 zero days means the
# agency stopped reporting, not that nobody travelled. Team to confirm at milestone M2.
MAIN_SCENARIO = "S2"

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
    """Return the rows with `value` handled according to SCENARIOS[code].

    Rows removed by the scenario are dropped; rows filled by the scenario get the filled
    value. Must not modify `rows` in place. Unknown code -> ValueError.
    """
    if code not in SCENARIOS:
        raise ValueError(f"unknown scenario {code!r}; expected one of {list(SCENARIOS)}")
    out = rows.copy()
    if code == "S5":                       # the wrong way: a missing day counts as 0 passengers
        out["value"] = out["value"].fillna(0.0)
        return out
    if code in ("S2", "S3"):               # long zero runs = not reported -> treat as missing
        out = out[~out["zero_long_run"]]
    if code == "S4":                       # impute from the same service, year, month and weekday
        key = [out["service"], out["year_be"], out["date"].dt.month, out["date"].dt.dayofweek]
        out["value"] = out["value"].fillna(out.groupby(key)["value"].transform("median"))
    out = out.dropna(subset=["value"])
    if code == "S3":                       # keep only calendar days valid in BOTH years
        month_day = out["date"].dt.strftime("%m-%d")
        both = out.groupby([out["service"], month_day])["year_be"].transform("nunique") == 2
        out = out[both]
    return out


def _window_days(rows: pd.DataFrame) -> dict[int, int]:
    """Number of calendar days from 1 Jan to the last date of the window, per year."""
    days = {}
    for year_be, d in rows.groupby("year_be")["date"]:
        days[year_be] = len(pd.date_range(f"{d.max().year}-01-01", d.max()))
    return days


def yoy_table(rows: pd.DataFrame) -> pd.DataFrame:
    """One row per service with the Q2 features (rows already passed through a scenario).

    Output columns: service, purpose, mode, avg_daily_68, avg_daily_69, abs_change,
    yoy_change_pct, coverage_68, coverage_69, rank where
        avg_daily_YY   = mean of the valid daily values of that year in the window
        abs_change     = avg_daily_69 - avg_daily_68
        yoy_change_pct = features.safe_pct_change(avg_daily_69, avg_daily_68)
        coverage_YY    = valid days / days in the window for that year
        rank           = rank of yoy_change_pct, 1 = largest increase (NaN stays NaN)
    """
    keys = ["service", "purpose", "mode"]
    valid = rows.dropna(subset=["value"])
    stats = valid.groupby(keys + ["year_be"])["value"].agg(["mean", "count"]).unstack("year_be")
    window = _window_days(rows)
    table = pd.DataFrame(index=stats.index)
    for year_be, suffix in [(BASE_YEAR, "68"), (NEW_YEAR, "69")]:
        table[f"avg_daily_{suffix}"] = stats.get(("mean", year_be))
        table[f"coverage_{suffix}"] = stats.get(("count", year_be)) / window.get(year_be, float("nan"))
    table = table.reset_index()
    table["abs_change"] = table["avg_daily_69"] - table["avg_daily_68"]
    table["yoy_change_pct"] = features.safe_pct_change(table["avg_daily_69"], table["avg_daily_68"])
    table["rank"] = table["yoy_change_pct"].rank(ascending=False, method="min")
    cols = keys + ["avg_daily_68", "avg_daily_69", "abs_change", "yoy_change_pct",
                   "coverage_68", "coverage_69", "rank"]
    return table[cols].sort_values("rank", na_position="last").reset_index(drop=True)


def run_scenarios(rows: pd.DataFrame, codes: tuple[str, ...] = tuple(SCENARIOS)) -> pd.DataFrame:
    """Long table of yoy_table() under every scenario.

    Output columns: scenario, service, yoy_change_pct, rank (+ the other yoy_table columns).
    Saved as q2_missing_sensitivity.csv.
    """
    parts = [yoy_table(apply_scenario(rows, code)).assign(scenario=code) for code in codes]
    out = pd.concat(parts, ignore_index=True)
    return out[["scenario"] + [c for c in out.columns if c != "scenario"]]


def rank_stability(sensitivity: pd.DataFrame, reference: str = "S1") -> pd.DataFrame:
    """How much each scenario's ranking differs from the reference.

    Output columns: scenario, spearman_vs_reference, n_services_moved_2plus, n_services_ranked.
    Only services ranked in both the scenario and the reference are compared, and ranks are
    recomputed on that common set so a dropped service does not shift everyone by one.
    """
    pct = sensitivity.pivot_table(index="service", columns="scenario", values="yoy_change_pct")
    rows = []
    for code in pct.columns:
        # build the pair explicitly: pct[[reference, code]] would duplicate a column when code == reference
        common = pd.concat({"ref": pct[reference], "new": pct[code]}, axis=1).dropna()
        r_ref = common["ref"].rank(ascending=False)
        r_new = common["new"].rank(ascending=False)
        rows.append({
            "scenario": code,
            "spearman_vs_reference": r_ref.corr(r_new) if len(common) > 1 else float("nan"),
            "n_services_moved_2plus": int(((r_ref - r_new).abs() >= 2).sum()),
            "n_services_ranked": int(sensitivity.loc[sensitivity["scenario"] == code, "rank"].notna().sum()),
        })
    return pd.DataFrame(rows)


def plot_yoy_bars(table: pd.DataFrame, title_note: str = ""):
    """Diverging horizontal bar of yoy_change_pct per service. Returns a Figure."""
    import matplotlib.pyplot as plt
    import plots

    data = table.dropna(subset=["yoy_change_pct"]).sort_values("yoy_change_pct")
    colors = [plots.POS_COLOR if v >= 0 else plots.NEG_COLOR for v in data["yoy_change_pct"]]
    fig, ax = plt.subplots(figsize=(9.5, 0.3 * len(data) + 1.6))
    ax.barh(data["service"], data["yoy_change_pct"], color=colors)
    ax.axvline(0, color="#333", linewidth=1)
    for y, v in enumerate(data["yoy_change_pct"]):
        ax.text(v + (0.6 if v >= 0 else -0.6), y, f"{v:+.1f}%", va="center",
                ha="left" if v >= 0 else "right", fontsize=8.5)
    lo, hi = data["yoy_change_pct"].min(), data["yoy_change_pct"].max()
    pad = (hi - lo) * 0.15
    ax.set_xlim(min(lo, 0) - pad, max(hi, 0) + pad)
    ax.set_xlabel("% เปลี่ยนแปลงของผู้โดยสารเฉลี่ยต่อวัน (2569 เทียบ 2568)")
    ax.set_title("การเปลี่ยนแปลงช่วง 1 ม.ค.–11 มี.ค. ปี 2569 เทียบปี 2568" + title_note)
    ax.grid(axis="y", visible=False)
    return fig


def plot_rank_by_scenario(sensitivity: pd.DataFrame, reference: str = "S1"):
    """Heatmap of rank per service across S1–S5 (services ordered by the reference). Returns a Figure."""
    import matplotlib.pyplot as plt
    import seaborn as sns

    ranks = sensitivity.pivot_table(index="service", columns="scenario", values="rank")
    ranks = ranks.reindex(columns=list(SCENARIOS)).sort_values(reference, na_position="last")
    fig, ax = plt.subplots(figsize=(8, 0.3 * len(ranks) + 1.8))
    sns.heatmap(ranks, annot=True, fmt=".0f", cmap="viridis_r", linewidths=0.4,
                cbar_kws={"label": "อันดับ (1 = เพิ่มขึ้นมากที่สุด)"}, ax=ax)
    ax.set_title("อันดับ % เปลี่ยนแปลง ภายใต้วิธีจัดการค่าว่าง/ศูนย์ S1–S5\n(ช่องว่าง = บริการถูกตัดออกหรือคำนวณไม่ได้)")
    ax.set_xlabel("วิธีจัดการ")
    ax.set_ylabel("")
    ax.grid(False)
    return fig


def main(df: pd.DataFrame) -> pd.DataFrame:
    """Build tables, save the prepared CSVs and figures. Called by run_all.py."""
    import plots

    import matplotlib.pyplot as plt

    rows = select_rows(df)
    table = yoy_table(apply_scenario(rows, MAIN_SCENARIO))
    sensitivity = run_scenarios(rows)
    table.to_csv(prep.PREPARED_DIR / OUTPUT_FILE, index=False, encoding="utf-8-sig")
    sensitivity.to_csv(prep.PREPARED_DIR / SENSITIVITY_FILE, index=False, encoding="utf-8-sig")
    for name, fig in [("q2_yoy_bars", plot_yoy_bars(table, f" ({MAIN_SCENARIO})")),
                      ("q2_rank_by_scenario", plot_rank_by_scenario(sensitivity))]:
        plots.save_fig(fig, name)
        plt.close(fig)
    return table
