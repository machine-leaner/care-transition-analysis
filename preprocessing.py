"""
preprocessing.py
=================
Validation, cleaning, and transformation of the raw UAC dataframe into a
clean, typed, analysis-ready dataframe.

Pipeline stage: Raw CSV -> Validation -> Cleaning -> Transformation

Key known data-quality issues handled here (discovered during initial
inspection of the real CSV):
  1. The raw export contains 450 fully-blank trailing rows (a CSV
     artifact, not real missing observations) which must be dropped.
  2. "Children in HHS Care" is stored as a comma-formatted string
     (e.g. "2,484") and must be converted to numeric.
  3. Dates are stored as strings like "December 21, 2025" and must be
     parsed to real datetimes.
  4. The reporting cadence itself skips Friday/Saturday almost entirely
     -- this is preserved as a documented characteristic of the data
     (see docs/03_EDA_Findings.md), not "fixed" by interpolation.

Nothing in this module invents data. Missing calendar days are left
missing; they are not forward-filled or interpolated, since doing so
would fabricate observations for days the program did not report.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from src.config import (
    RAW_COLUMNS,
    DATE_COL,
    RAW_DATE_FORMAT,
    NUMERIC_COLS,
    HHS_CARE_COL,
)

logger = logging.getLogger(__name__)


def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename raw HHS column headers to canonical snake_case names."""
    missing = set(RAW_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Expected raw columns not found in dataframe: {missing}")
    return df.rename(columns=RAW_COLUMNS)


def drop_fully_blank_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drop rows where every column is null. The raw HHS export contains
    trailing blank rows (an artifact of how the source CSV was generated),
    not genuine missing observations, so these are safe to drop entirely
    rather than treat as missing data requiring imputation.
    """
    before = len(df)
    df = df.dropna(how="all").reset_index(drop=True)
    dropped = before - len(df)
    logger.info("Dropped %d fully-blank rows", dropped)
    return df


def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Parse the date column (e.g. 'December 21, 2025') into datetime64."""
    df = df.copy()
    parsed = pd.to_datetime(df[DATE_COL], format=RAW_DATE_FORMAT, errors="coerce")
    n_failed = parsed.isna().sum() - df[DATE_COL].isna().sum()
    if n_failed > 0:
        logger.warning("%d date values failed to parse and became NaT", n_failed)
    df[DATE_COL] = parsed
    return df


def convert_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert all count columns to numeric, handling comma-formatted strings
    (e.g. "Children in HHS Care" = "2,484") in any numeric column that may
    contain them.
    """
    df = df.copy()
    for col in NUMERIC_COLS:
        # Always normalize through string form first (strip thousands separators
        # and whitespace) before converting to numeric. This is deliberately
        # unconditional rather than gated on dtype: pandas may represent the
        # column as classic numpy 'object' or as a newer 'str'/StringDtype
        # depending on version/settings, and a dtype check can silently skip
        # the comma-stripping step (e.g. "Children in HHS Care" = "2,484").
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.strip()
            .replace({"nan": np.nan, "": np.nan, "None": np.nan})
        )
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def validate_numeric_ranges(df: pd.DataFrame) -> Dict[str, int]:
    """
    Check for impossible values (negative counts) in numeric columns.
    Does NOT remove anything -- only reports counts so a human/analyst can
    decide how to handle any flagged rows.
    """
    issues = {}
    for col in NUMERIC_COLS:
        issues[f"{col}_negative_count"] = int((df[col] < 0).sum())
        issues[f"{col}_null_count"] = int(df[col].isna().sum())
    return issues


def check_duplicate_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Return any rows sharing a duplicate date (after blank-row removal)."""
    dupes = df[df[DATE_COL].duplicated(keep=False)].sort_values(DATE_COL)
    return dupes


def check_date_continuity(df: pd.DataFrame) -> Dict[str, object]:
    """
    Assess date continuity against the full calendar range. The program
    does not report every calendar day (notably almost never on Friday or
    Saturday), so this reports the gap structure rather than assuming
    daily reporting is expected.
    """
    dates = df[DATE_COL].dropna().sort_values()
    full_range = pd.date_range(dates.min(), dates.max(), freq="D")
    missing_days = full_range.difference(dates)
    weekday_counts = dates.dt.day_name().value_counts().to_dict()
    missing_weekday_counts = pd.Series(missing_days).dt.day_name().value_counts().to_dict() if len(missing_days) else {}
    return {
        "date_min": dates.min(),
        "date_max": dates.max(),
        "n_calendar_days": len(full_range),
        "n_reported_days": len(dates),
        "n_missing_days": len(missing_days),
        "weekday_counts_reported": weekday_counts,
        "weekday_counts_missing": missing_weekday_counts,
        "missing_days": missing_days,
    }


def sort_and_deduplicate(df: pd.DataFrame) -> pd.DataFrame:
    """Sort chronologically and drop exact duplicate rows (keep first)."""
    df = df.sort_values(DATE_COL).reset_index(drop=True)
    before = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    dropped = before - len(df)
    if dropped:
        logger.info("Dropped %d exact duplicate rows", dropped)
    return df


def drop_unparseable_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drop rows where the date failed to parse. These cannot be placed in
    the time series and are logged, not silently discarded.
    """
    before = len(df)
    bad = df[df[DATE_COL].isna()]
    if len(bad) > 0:
        logger.warning("Dropping %d rows with unparseable dates", len(bad))
    df = df.dropna(subset=[DATE_COL]).reset_index(drop=True)
    return df


def run_preprocessing_pipeline(raw_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, object]]:
    """
    Execute the full validation + cleaning + transformation pipeline on a
    raw dataframe (as returned by data_loader.load_raw_data).

    Returns
    -------
    (clean_df, report) : Tuple[pd.DataFrame, dict]
        The cleaned, typed, analysis-ready dataframe and a report dict
        documenting what was done (useful for logging / the Data Quality
        dashboard page).
    """
    report: Dict[str, object] = {}

    df = rename_columns(raw_df)
    report["initial_shape"] = df.shape

    df = drop_fully_blank_rows(df)
    report["shape_after_blank_row_removal"] = df.shape

    df = parse_dates(df)
    df = drop_unparseable_rows(df)
    report["shape_after_date_parsing"] = df.shape

    df = convert_numeric_columns(df)

    duplicate_dates = check_duplicate_dates(df)
    report["duplicate_date_rows"] = len(duplicate_dates)

    df = sort_and_deduplicate(df)
    report["shape_after_deduplication"] = df.shape

    report["numeric_validation"] = validate_numeric_ranges(df)
    report["date_continuity"] = check_date_continuity(df)

    return df, report
