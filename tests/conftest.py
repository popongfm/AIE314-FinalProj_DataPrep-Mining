"""Shared fixtures. Tests build the clean table from the raw files (they never read data/prepared/)."""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import prep  # noqa: E402


@pytest.fixture(scope="session")
def clean_df() -> pd.DataFrame:
    df, _, _ = prep.build_all(save=False)
    return df


@pytest.fixture(scope="session")
def catalog() -> pd.DataFrame:
    _, cat, _ = prep.build_all(save=False)
    return cat


def call_or_skip(fn, *args, **kwargs):
    """Run fn; skip the test (instead of failing) while fn is still a TODO stub."""
    try:
        return fn(*args, **kwargs)
    except NotImplementedError as exc:
        pytest.skip(f"not implemented yet: {exc}")
