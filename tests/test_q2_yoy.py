"""Q2 contract. Tests for TODO functions are skipped until member B implements them."""
import numpy as np
import pandas as pd
import pytest

import q2_yoy
from conftest import call_or_skip


def test_window_is_fair(clean_df):
    assert q2_yoy.comparison_window(clean_df) == (3, 11)
    rows = q2_yoy.select_rows(clean_df)
    days = rows.drop_duplicates(["year_be", "date"]).groupby("year_be")["date"]
    assert days.nunique().to_dict() == {2568: 70, 2569: 70}
    assert days.apply(lambda d: (d.dt.dayofweek >= 5).sum()).to_dict() == {2568: 20, 2569: 20}


def test_select_rows_keeps_missing_and_zero_series(clean_df):
    rows = q2_yoy.select_rows(clean_df)
    assert rows["missing_flag"].any()
    assert "รถหมวด 3" in set(rows["service"])
    assert set(rows["unit"]) == {"คน"} and not rows["is_aggregate"].any()


@pytest.mark.parametrize("code", list(q2_yoy.SCENARIOS))
def test_scenarios_leave_no_nan_and_do_not_mutate(clean_df, code):
    rows = q2_yoy.select_rows(clean_df)
    before = rows.copy()
    out = call_or_skip(q2_yoy.apply_scenario, rows, code)
    pd.testing.assert_frame_equal(rows, before)
    assert not out["value"].isna().any()


def test_s2_removes_long_zero_runs(clean_df):
    out = call_or_skip(q2_yoy.apply_scenario, q2_yoy.select_rows(clean_df), "S2")
    assert not out["zero_long_run"].any()


def test_unknown_scenario(clean_df):
    rows = q2_yoy.select_rows(clean_df)
    call_or_skip(q2_yoy.apply_scenario, rows, "S1")
    with pytest.raises(ValueError):
        q2_yoy.apply_scenario(rows, "S9")


def test_yoy_table_formula():
    dates = list(pd.date_range("2025-01-01", periods=3)) + list(pd.date_range("2026-01-01", periods=3))
    rows = pd.DataFrame({"date": dates * 2, "service": ["up"] * 6 + ["down"] * 6,
                         "purpose": "intercity", "mode": "road",
                         "year_be": ([2568] * 3 + [2569] * 3) * 2,
                         "value": [100.0] * 3 + [150.0] * 3 + [200.0] * 3 + [100.0] * 3})
    t = call_or_skip(q2_yoy.yoy_table, rows).set_index("service")
    assert np.isclose(t.loc["up", "yoy_change_pct"], 50) and np.isclose(t.loc["down", "yoy_change_pct"], -50)
    assert np.isclose(t.loc["up", "abs_change"], 50)
    assert t.loc["up", "rank"] == 1 and t.loc["down", "rank"] == 2


def test_run_scenarios_covers_all(clean_df):
    sens = call_or_skip(q2_yoy.run_scenarios, q2_yoy.select_rows(clean_df))
    assert set(sens["scenario"]) == set(q2_yoy.SCENARIOS)
    assert {"scenario", "service", "yoy_change_pct", "rank"} <= set(sens.columns)


def test_rank_stability_reference_matches_itself(clean_df):
    sens = call_or_skip(q2_yoy.run_scenarios, q2_yoy.select_rows(clean_df))
    stab = q2_yoy.rank_stability(sens).set_index("scenario")
    assert set(stab.index) == set(q2_yoy.SCENARIOS)
    assert np.isclose(stab.loc["S1", "spearman_vs_reference"], 1)
    assert stab.loc["S1", "n_services_moved_2plus"] == 0


def test_stopped_reporting_is_not_a_100pct_drop(clean_df):
    # รถหมวด 3 reports zeros for all of 2569: S2 must not call that a -100% change
    table = call_or_skip(q2_yoy.yoy_table, q2_yoy.apply_scenario(q2_yoy.select_rows(clean_df), "S2"))
    row = table.set_index("service").loc["รถหมวด 3"]
    assert np.isnan(row["yoy_change_pct"])
