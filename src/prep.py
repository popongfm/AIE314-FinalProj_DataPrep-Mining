"""Shared data-preparation functions for AIE314/AIE315 Topic 4 (passenger volume).

Every notebook imports from here so that loading and cleaning happen in exactly one place.
Owner: member A. Change this file only after the whole team agrees (after milestone M2).

Plotting helpers (Thai font, save_fig) live in plots.py.

Pipeline:
    raw CSV --load_raw--> raw rows (empty rows dropped)
            --to_standard--> English column names, parsed date and value
            --add_direction--> port + direction split out of the service name
            --add_quality_flags--> missing / zero / long-zero-run / duplicate flags
    build_service_catalog() describes the 43 services (unit, aggregate, exclusion reason)
    clean() runs everything for both years and returns the shared long table.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths (relative to the project root, so the project runs on any machine)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PREPARED_DIR = PROJECT_ROOT / "data" / "prepared"
FIG_DIR = PROJECT_ROOT / "figures"

RAW_FILES = {
    2568: RAW_DIR / "4_passengers68.csv",
    2569: RAW_DIR / "4_passengers69.csv",
}

# ---------------------------------------------------------------------------
# Column names and category mappings
# ---------------------------------------------------------------------------
RAW_COLUMNS = [
    "รูปแบบการเดินทาง", "วัตถุประสงค์", "สาธารณะ/ส่วนบุคคล", "หน่วยงาน",
    "ยานพาหนะ/ท่า", "วันที่", "หน่วย", "ปริมาณ",
]

COLUMN_MAP = {
    "รูปแบบการเดินทาง": "mode_th",
    "วัตถุประสงค์": "purpose_th",
    "สาธารณะ/ส่วนบุคคล": "public_private",
    "หน่วยงาน": "agency",
    "ยานพาหนะ/ท่า": "service_raw",
    "วันที่": "date_raw",
    "หน่วย": "unit",
    "ปริมาณ": "value_raw",
}

MODE_MAP = {"ทางถนน": "road", "ทางน้ำ": "water", "ทางราง": "rail", "ทางอากาศ": "air"}
PURPOSE_MAP = {
    "การเดินทางระหว่างจังหวัด": "intercity",
    "การเดินทางภายในจังหวัด/กรุงเทพ": "intracity",
    "การเดินทางระหว่างประเทศ": "international",
}

# Quality issue #9: the same airport group is spelled two ways in the raw data.
SERVICE_NAME_FIX = {
    "ท่าอากาศอื่น ๆ ของ ทอท.": "ท่าอากาศยานอื่น ๆ ของ ทอท.",
}

DIRECTION_PATTERN = r"\s*ขา(เข้า|ออก)ประเทศ\s*$"
DIRECTION_MAP = {"เข้า": "arrival", "ออก": "departure"}

# "รถยนต์ทุกประเภท" already contains "รถยนต์เฉพาะ 4 ล้อ" -> never add them together.
AGGREGATE_KEYWORD = "รถยนต์ทุกประเภท"

# A run of zeros at least this long is treated as "not reported", not "no passengers".
LONG_ZERO_RUN_DAYS = 7

WEEKDAY_TH = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------
def load_raw(path: str | Path) -> pd.DataFrame:
    """Read one raw CSV as text and drop rows that are empty in every column.

    keep_default_na=False stops pandas from silently turning text into NaN;
    empty strings are converted to NaN explicitly in parse_quantity().
    """
    df = pd.read_csv(path, encoding="utf-8-sig", dtype=str, keep_default_na=False)
    missing_cols = set(RAW_COLUMNS) - set(df.columns)
    if missing_cols:
        raise ValueError(f"{path}: missing columns {sorted(missing_cols)}")
    df = df[RAW_COLUMNS]
    is_blank_row = (df.apply(lambda col: col.str.strip()) == "").all(axis=1)
    return df.loc[~is_blank_row].reset_index(drop=True)


def parse_quantity(s: pd.Series) -> pd.Series:
    """'127,551' -> 127551.0 ; '' -> NaN. Raises if any other text cannot be parsed."""
    cleaned = s.astype(str).str.replace(",", "", regex=False).str.strip()
    cleaned = cleaned.replace("", np.nan)
    out = pd.to_numeric(cleaned, errors="coerce")
    bad = out.isna() & cleaned.notna()
    if bad.any():
        raise ValueError(f"Unparseable quantities: {cleaned[bad].unique()[:10]}")
    return out.astype(float)


def to_standard(raw: pd.DataFrame, year_be: int) -> pd.DataFrame:
    """Rename to English columns, parse date and value, map mode/purpose codes."""
    df = raw.rename(columns=COLUMN_MAP).copy()
    df["date"] = pd.to_datetime(df["date_raw"], format="%d/%m/%Y")
    df["value"] = parse_quantity(df["value_raw"])
    df["year_be"] = year_be
    df["mode"] = df["mode_th"].map(MODE_MAP)
    df["purpose"] = df["purpose_th"].map(PURPOSE_MAP)
    if df["mode"].isna().any() or df["purpose"].isna().any():
        raise ValueError("Unknown mode or purpose label in raw data")
    df["service"] = df["service_raw"].str.strip().replace(SERVICE_NAME_FIX)
    return df.drop(columns=["date_raw", "value_raw"])


def add_direction(df: pd.DataFrame) -> pd.DataFrame:
    """Split 'ท่าอากาศยานสุวรรณภูมิ ขาเข้าประเทศ' into port + direction (arrival/departure/none)."""
    df = df.copy()
    word = df["service"].str.extract(DIRECTION_PATTERN, expand=False)
    df["direction"] = word.map(DIRECTION_MAP).fillna("none")
    df["port"] = df["service"].str.replace(DIRECTION_PATTERN, "", regex=True).str.strip()
    return df


def _zero_run_length(values: pd.Series) -> pd.Series:
    """For each row, the length of the consecutive run of zeros it belongs to (0 if not zero)."""
    is_zero = values.eq(0)
    run_id = (is_zero != is_zero.shift()).cumsum()
    run_len = is_zero.groupby(run_id).transform("sum")
    return run_len.where(is_zero, 0).astype(int)


def add_quality_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Add missing_flag, zero_flag, zero_run_len, zero_long_run. Values are NOT changed here."""
    df = df.sort_values(["service", "date"]).copy()
    df["missing_flag"] = df["value"].isna()
    df["zero_flag"] = df["value"].eq(0)
    df["zero_run_len"] = df.groupby("service", group_keys=False)["value"].apply(_zero_run_length)
    df["zero_long_run"] = df["zero_run_len"] >= LONG_ZERO_RUN_DAYS
    return df


# ---------------------------------------------------------------------------
# Service catalog (data dictionary of the 43 services)
# ---------------------------------------------------------------------------
def build_service_catalog(df: pd.DataFrame) -> pd.DataFrame:
    """One row per service with its attributes and why it is excluded (if it is)."""
    keys = ["service", "port", "direction", "mode", "purpose", "public_private", "agency", "unit"]
    stats = (
        df.groupby(keys, dropna=False)
        .agg(
            n_days=("value", "size"),
            n_missing=("missing_flag", "sum"),
            n_zero=("zero_flag", "sum"),
            n_zero_long_run=("zero_long_run", "sum"),
            mean_value=("value", "mean"),
        )
        .reset_index()
    )
    stats["is_aggregate"] = stats["service"].str.contains(AGGREGATE_KEYWORD, regex=False)

    def reason(row) -> str:
        if row["unit"] != "คน":
            return "unit=คัน (not passengers)"
        if row["n_zero"] == row["n_days"]:
            return "all-zero series (not reported)"
        return ""

    stats["exclude_reason"] = stats.apply(reason, axis=1)
    return stats.sort_values(["purpose", "mode", "service"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Full cleaning
# ---------------------------------------------------------------------------
OUTPUT_COLUMNS = [
    "date", "year_be", "mode", "purpose", "public_private", "agency",
    "service", "port", "direction", "unit", "is_aggregate", "exclude_reason",
    "value", "missing_flag", "zero_flag", "zero_run_len", "zero_long_run", "had_duplicate",
]


def clean(raw_by_year: dict[int, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (clean_long, service_catalog) for both years combined.

    Steps: standardise -> drop exact duplicate (service, date) rows -> split direction
    -> quality flags (per year, so a zero run never crosses the year boundary)
    -> attach catalog attributes. Missing values and zeros are kept and flagged, not filled.
    """
    parts = []
    for year_be, raw in raw_by_year.items():
        df = to_standard(raw, year_be)
        dup_mask = df.duplicated(["service", "date"], keep="first")
        dup_rows = df[df.duplicated(["service", "date"], keep=False)]
        conflicting = dup_rows.groupby(["service", "date"])["value"].nunique(dropna=False).gt(1)
        if conflicting.any():
            raise ValueError(f"{year_be}: duplicate keys with different values: {conflicting[conflicting].index.tolist()}")
        df = df.loc[~dup_mask]
        df = add_direction(df)
        df = add_quality_flags(df)
        df["had_duplicate"] = False
        if dup_mask.any():
            dropped_keys = set(map(tuple, dup_rows[["service", "date"]].values))
            df["had_duplicate"] = [(s, d) in dropped_keys for s, d in zip(df["service"], df["date"])]
        parts.append(df)

    combined = pd.concat(parts, ignore_index=True)
    catalog = build_service_catalog(combined)

    # A series that is zero in every row of BOTH years is excluded; recompute per service.
    attrs = catalog[["service", "is_aggregate", "exclude_reason"]]
    out = combined.merge(attrs, on="service", how="left", validate="many_to_one")
    out = out[OUTPUT_COLUMNS].sort_values(["year_be", "service", "date"]).reset_index(drop=True)
    validate_clean(out)
    return out, catalog


def validate_clean(df: pd.DataFrame) -> None:
    """Assertions every member can rely on."""
    assert not df.duplicated(["service", "date"]).any(), "duplicate (service, date) keys"
    assert df["value"].dtype == float, "value must be float"
    assert (df["value"].dropna() >= 0).all(), "negative values"
    assert set(df["unit"].unique()) <= {"คน", "คัน"}, "unexpected unit"
    per_year = df.groupby("year_be")["service"].nunique()
    assert per_year.nunique() == 1, f"service count differs between years: {per_year.to_dict()}"


def quality_report(raw_by_year: dict[int, pd.DataFrame], raw_rows_by_year: dict[int, int],
                   clean_df: pd.DataFrame) -> pd.DataFrame:
    """Before/after table for the report: rows, blanks, duplicates, missing, zeros."""
    rows = []
    for year_be, raw in raw_by_year.items():
        c = clean_df[clean_df["year_be"] == year_be]
        rows.append({
            "year_be": year_be,
            "rows_in_file": raw_rows_by_year[year_be],
            "blank_rows_removed": raw_rows_by_year[year_be] - len(raw),
            "rows_after_blank_removal": len(raw),
            "duplicate_rows_removed": len(raw) - len(c),
            "rows_clean": len(c),
            "n_services": c["service"].nunique(),
            "first_date": c["date"].min().date(),
            "last_date": c["date"].max().date(),
            "n_days": c["date"].nunique(),
            "missing_values": int(c["missing_flag"].sum()),
            "zero_values": int(c["zero_flag"].sum()),
            "zero_in_long_runs": int(c["zero_long_run"].sum()),
            "rows_unit_kan": int((c["unit"] == "คัน").sum()),
            "rows_excluded_any_reason": int((c["exclude_reason"] != "").sum()),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Helpers for the analysis notebooks
# ---------------------------------------------------------------------------
def load_clean(path: str | Path | None = None) -> pd.DataFrame:
    """Read the shared prepared file with correct dtypes."""
    path = path or PREPARED_DIR / "passengers_clean_long.csv"
    df = pd.read_csv(path, encoding="utf-8-sig", parse_dates=["date"], keep_default_na=False,
                     na_values={"value": [""]})
    df["value"] = df["value"].astype(float)
    df["exclude_reason"] = df["exclude_reason"].astype(str)
    for col in ["is_aggregate", "missing_flag", "zero_flag", "zero_long_run", "had_duplicate"]:
        df[col] = df[col].astype(str).eq("True")
    return df


def passenger_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Rows usable as passenger counts: unit=คน, not excluded, not an aggregate."""
    return df[(df["unit"] == "คน") & (df["exclude_reason"] == "") & (~df["is_aggregate"])].copy()


def build_all(save: bool = True) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Run the whole cleaning stage: raw files -> (clean_long, service_catalog, quality_log).

    With save=True the three tables are written to data/prepared/ (utf-8-sig so Excel shows Thai).
    """
    rows_in_file, raw = {}, {}
    for year_be, path in RAW_FILES.items():
        rows_in_file[year_be] = len(pd.read_csv(path, encoding="utf-8-sig", dtype=str, keep_default_na=False))
        raw[year_be] = load_raw(path)
    clean_df, catalog = clean(raw)
    quality_log = quality_report(raw, rows_in_file, clean_df)
    if save:
        PREPARED_DIR.mkdir(parents=True, exist_ok=True)
        clean_df.to_csv(PREPARED_DIR / "passengers_clean_long.csv", index=False, encoding="utf-8-sig")
        catalog.to_csv(PREPARED_DIR / "service_catalog.csv", index=False, encoding="utf-8-sig")
        quality_log.to_csv(PREPARED_DIR / "quality_log.csv", index=False, encoding="utf-8-sig")
    return clean_df, catalog, quality_log
