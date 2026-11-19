"""Q3 contract. Tests for TODO functions are skipped until member C implements them."""
import numpy as np

import q3_intl
from conftest import call_or_skip


def test_select_rows_pairs(clean_df):
    rows = q3_intl.select_rows(clean_df)
    assert rows["port"].nunique() == 7
    assert set(rows["mode"]) == {"air", "road", "rail", "water"}


def test_monthly_flows_shape(clean_df):
    m = call_or_skip(q3_intl.monthly_flows, q3_intl.select_rows(clean_df))
    assert {"mode", "year_month", "arrival", "departure"} <= set(m.columns)
    assert len(m) == 4 * 12


def test_flow_features(clean_df):
    m = call_or_skip(q3_intl.monthly_flows, q3_intl.select_rows(clean_df))
    f = q3_intl.add_flow_features(m)
    assert np.allclose(f["net_flow"], f["arrival"] - f["departure"])
    assert np.allclose(f.groupby("year_month")["mode_share"].sum(), 1)


def test_volatility_is_cv(clean_df):
    m = call_or_skip(q3_intl.monthly_flows, q3_intl.select_rows(clean_df))
    v = q3_intl.volatility_table(q3_intl.add_flow_features(m))
    assert np.allclose(v["cv_within_year"], v["std_monthly"] / v["mean_monthly"])
    assert len(v) == 4 * 2
