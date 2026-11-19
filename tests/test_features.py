import numpy as np
import pandas as pd

import features


def test_calendar_features():
    out = features.add_calendar_features(pd.DataFrame({"date": pd.to_datetime(["2025-01-03", "2025-01-04"])}))
    assert out["day_of_week"].tolist() == [4, 5]
    assert out["is_weekend"].tolist() == [False, True]
    assert out["day_name_th"].astype(str).tolist() == ["ศุกร์", "เสาร์"]
    assert out["year_month"].tolist() == ["2025-01", "2025-01"]


def test_safe_pct_change():
    assert features.safe_pct_change(110, 100) == 10
    assert np.isnan(features.safe_pct_change(5, 0))
    s = features.safe_pct_change(pd.Series([50.0, 3.0]), pd.Series([100.0, 0.0]))
    assert s.iloc[0] == -50 and np.isnan(s.iloc[1])


def test_monthly_from_daily_tracks_coverage():
    df = pd.DataFrame({"date": pd.date_range("2025-02-01", periods=28), "k": "a", "value": 10.0})
    df.loc[0, "value"] = np.nan
    m = features.monthly_from_daily(df, ["k"]).iloc[0]
    assert (m["days"], m["valid_days"], m["total"], m["avg_daily"]) == (28, 27, 270, 10)
    assert np.isclose(m["coverage"], 27 / 28)
