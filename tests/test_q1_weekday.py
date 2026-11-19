"""Q1 contract. Tests for TODO functions are skipped until member A implements them."""
import numpy as np
import pandas as pd

import q1_weekday
from conftest import call_or_skip


def toy_rows():
    """Two weeks of one service: 100 on weekdays, 50 on weekends."""
    dates = pd.date_range("2025-01-06", periods=14)  # starts on a Monday
    return pd.DataFrame({"date": dates, "service": "s", "purpose": "intracity", "mode": "rail",
                         "value": np.where(dates.dayofweek >= 5, 50.0, 100.0)})


def test_select_rows(clean_df):
    rows = q1_weekday.select_rows(clean_df)
    assert set(rows["year_be"]) == {2568}
    assert not rows["missing_flag"].any() and not rows["zero_long_run"].any()
    assert set(rows["unit"]) == {"คน"}


def test_dow_index_averages_100_per_service():
    daily = call_or_skip(q1_weekday.build_daily_features, toy_rows())
    assert {"day_of_week", "is_weekend", "month", "dow_index"} <= set(daily.columns)
    assert np.isclose(daily.groupby("service")["dow_index"].mean().iloc[0], 100)


def test_weekend_ratio():
    daily = call_or_skip(q1_weekday.build_daily_features, toy_rows())
    t = q1_weekday.weekend_ratio_table(daily, by=("service",))
    assert np.isclose(t["weekend_ratio"].iloc[0], 0.5)
    assert np.isclose(t["pct_diff_weekend"].iloc[0], -50)


def test_weekend_ratio_is_nan_without_weekend_days():
    weekdays_only = toy_rows().query("date.dt.dayofweek < 5")
    daily = call_or_skip(q1_weekday.build_daily_features, weekdays_only)
    t = q1_weekday.weekend_ratio_table(daily, by=("service",))
    assert np.isnan(t["weekend_ratio"].iloc[0])
