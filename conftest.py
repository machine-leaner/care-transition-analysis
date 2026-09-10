"""
conftest.py
===========
Shared pytest fixtures for the UAC analytics test suite.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import RAW_COLUMNS


@pytest.fixture
def raw_csv_text() -> str:
    """A small synthetic raw CSV, mirroring real quirks: comma-formatted
    HHS Care values, quoted date strings, and trailing fully-blank rows."""
    header = ",".join(RAW_COLUMNS.keys())
    rows = [
        header,
        '"January 02, 2024",10,50,20,"2,000",15',
        '"January 03, 2024",8,45,18,"1,995",12',
        '"January 04, 2024",12,55,22,"2,010",18',
        '"January 05, 2024",0,40,0,"1,980",0',
        '"January 08, 2024",5,30,5,"1,970",5',
        ",,,,,",  # fully blank row (CSV artifact)
        ",,,,,",
    ]
    return "\n".join(rows) + "\n"


@pytest.fixture
def raw_df(tmp_path, raw_csv_text) -> pd.DataFrame:
    path = tmp_path / "synthetic_raw.csv"
    path.write_text(raw_csv_text)
    return pd.read_csv(path, dtype=str)


@pytest.fixture
def clean_df() -> pd.DataFrame:
    """A small, already-clean, typed dataframe for testing metrics/analysis
    modules directly without going through preprocessing."""
    dates = pd.date_range("2024-01-01", periods=40, freq="D")
    rng = np.random.default_rng(42)
    df = pd.DataFrame({
        "date": dates,
        "apprehensions": rng.integers(5, 50, size=40),
        "cbp_custody": rng.integers(20, 200, size=40),
        "transfers": rng.integers(5, 60, size=40),
        "hhs_care": rng.integers(1500, 3000, size=40),
        "discharges": rng.integers(0, 40, size=40),
    })
    return df
