"""Feature helpers shared by more than one question.

Question-specific features live in q1_weekday.py, q2_yoy.py and q3_intl.py.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

WEEKDAY_TH = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]


def add_calendar_features(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    """Add day_of_week (0=Mon), day_name_th, is_weekend (Sat/Sun), month (1-12), year_month ('2025-01').

    Returns a new DataFrame; the input is not modified.
    """
    out = df.copy()
    d = out[date_col]
    out["day_of_week"] = d.dt.dayofweek
    out["day_name_th"] = pd.Categorical(out["day_of_week"].map(dict(enumerate(WEEKDAY_TH))),
                                        categories=WEEKDAY_TH, ordered=True)
    out["is_weekend"] = out["day_of_week"] >= 5
    out["month"] = d.dt.month
    out["year_month"] = d.dt.to_period("M").astype(str)
    return out


def safe_pct_change(new, old):
    """(new - old) / old * 100, with NaN wherever old is 0 or missing (never ±inf)."""
    if np.ndim(old) == 0:
        old = float(old)
        return np.nan if (old == 0 or np.isnan(old)) else (new - old) / old * 100
    old = pd.Series(old, dtype=float)
    return (new - old) / old.where(old != 0) * 100


def monthly_from_daily(df: pd.DataFrame, keys: list[str], value_col: str = "value") -> pd.DataFrame:
    """Aggregate daily rows to months, keeping track of how complete each month is.

    Output columns: keys + year_month, days (rows in month), valid_days (non-NaN values),
    total (sum of valid values), avg_daily (total / valid_days), coverage (valid_days / days).
    Use avg_daily, not total, when coverage < 1 so a month with missing days is not understated.
    """
    tmp = df.assign(year_month=df["date"].dt.to_period("M").astype(str))
    out = (tmp.groupby(keys + ["year_month"], observed=True)[value_col]
              .agg(days="size", valid_days="count", total="sum")
              .reset_index())
    out["avg_daily"] = out["total"] / out["valid_days"].where(out["valid_days"] > 0)
    out["coverage"] = out["valid_days"] / out["days"]
    return out
