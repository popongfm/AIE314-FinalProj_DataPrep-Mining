"""Facts about the shared clean table that every question relies on."""
import numpy as np
import pandas as pd
import pytest

import prep


def test_blank_and_duplicate_rows_removed(clean_df):
    counts = clean_df.groupby("year_be").size().to_dict()
    assert counts == {2568: 43 * 365, 2569: 43 * 70}
    assert not clean_df.duplicated(["service", "date"]).any()


def test_known_duplicate_is_flagged(clean_df):
    row = clean_df[(clean_df["service"] == "ท่าอากาศยานภูมิภาค ขาออกประเทศ")
                   & (clean_df["date"] == "2025-10-21")]
    assert len(row) == 1 and row["had_duplicate"].item() and row["value"].item() == 1257


def test_date_ranges(clean_df):
    r = clean_df.groupby("year_be")["date"].agg(["min", "max", "nunique"])
    assert r.loc[2568, "min"] == pd.Timestamp("2025-01-01") and r.loc[2568, "nunique"] == 365
    assert r.loc[2569, "max"] == pd.Timestamp("2026-03-11") and r.loc[2569, "nunique"] == 70


def test_airport_name_spelling_fixed(clean_df):
    assert not clean_df["service"].str.contains("ท่าอากาศอื่น", regex=False).any()


def test_direction_only_on_international(clean_df):
    intl = clean_df["purpose"] == "international"
    assert set(clean_df.loc[intl, "direction"]) == {"arrival", "departure"}
    assert set(clean_df.loc[~intl, "direction"]) == {"none"}
    assert clean_df.loc[intl, "port"].nunique() == 7


def test_exclusions(catalog):
    excluded = catalog.loc[catalog["exclude_reason"] != "", "service"].tolist()
    assert len(excluded) == 5 and "รถร่วม (หมวด 1)" in excluded
    assert (catalog.loc[catalog["unit"] == "คัน", "exclude_reason"] != "").all()
    assert set(catalog.loc[catalog["is_aggregate"], "service"]) == {
        "รถยนต์ทุกประเภท (10 จุดสำรวจ)", "รถยนต์ทุกประเภท (ทางด่วน)"}


def test_stopped_reporting_is_a_long_zero_run(clean_df):
    cat3_69 = clean_df[(clean_df["service"] == "รถหมวด 3") & (clean_df["year_be"] == 2569)]
    assert cat3_69["zero_long_run"].all()


def test_passenger_rows_has_no_vehicles_or_aggregates(clean_df):
    rows = prep.passenger_rows(clean_df)
    assert set(rows["unit"]) == {"คน"}
    assert not rows["is_aggregate"].any() and (rows["exclude_reason"] == "").all()


def test_parse_quantity():
    out = prep.parse_quantity(pd.Series(["1,234", "", "0"]))
    assert out.iloc[0] == 1234.0 and np.isnan(out.iloc[1]) and out.iloc[2] == 0.0
    with pytest.raises(ValueError):
        prep.parse_quantity(pd.Series(["abc"]))


def test_saved_file_round_trip(clean_df, tmp_path):
    path = tmp_path / "clean.csv"
    clean_df.to_csv(path, index=False, encoding="utf-8-sig")
    back = prep.load_clean(path)
    assert len(back) == len(clean_df)
    assert back["missing_flag"].sum() == clean_df["missing_flag"].sum()
    assert np.isclose(back["value"].sum(), clean_df["value"].sum())
