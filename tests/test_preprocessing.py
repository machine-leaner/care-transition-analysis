"""Tests for src.data_loader and src.preprocessing."""
import numpy as np
import pandas as pd
import pytest

from src.data_loader import load_raw_data, inspect_raw_data
from src.preprocessing import (
    rename_columns,
    drop_fully_blank_rows,
    parse_dates,
    convert_numeric_columns,
    validate_numeric_ranges,
    check_duplicate_dates,
    sort_and_deduplicate,
    run_preprocessing_pipeline,
)


def test_load_raw_data_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_raw_data(tmp_path / "does_not_exist.csv")


def test_load_raw_data_reads_all_rows(tmp_path, raw_csv_text):
    path = tmp_path / "raw.csv"
    path.write_text(raw_csv_text)
    df = load_raw_data(path)
    assert df.shape[0] == 7  # 5 real rows + 2 blank rows
    assert df.shape[1] == 6


def test_inspect_raw_data_reports_blank_rows(raw_df):
    summary = inspect_raw_data(raw_df)
    assert summary["fully_blank_rows"] == 2
    assert summary["shape"] == (7, 6)


def test_rename_columns(raw_df):
    df = rename_columns(raw_df)
    assert "date" in df.columns
    assert "hhs_care" in df.columns
    assert "apprehensions" in df.columns


def test_rename_columns_missing_column_raises():
    df = pd.DataFrame({"Date": ["x"]})
    with pytest.raises(ValueError):
        rename_columns(df)


def test_drop_fully_blank_rows(raw_df):
    df = rename_columns(raw_df)
    cleaned = drop_fully_blank_rows(df)
    assert len(cleaned) == 5
    assert cleaned.isnull().all(axis=1).sum() == 0


def test_date_parsing(raw_df):
    df = rename_columns(raw_df)
    df = drop_fully_blank_rows(df)
    df = parse_dates(df)
    assert pd.api.types.is_datetime64_any_dtype(df["date"])
    assert df["date"].iloc[0] == pd.Timestamp("2024-01-02")


def test_comma_removal_in_numeric_conversion(raw_df):
    """Directly tests the known 'Children in HHS Care' comma-formatting issue."""
    df = rename_columns(raw_df)
    df = drop_fully_blank_rows(df)
    df = parse_dates(df)
    df = convert_numeric_columns(df)
    assert df["hhs_care"].iloc[0] == 2000
    assert df["hhs_care"].iloc[1] == 1995
    assert pd.api.types.is_numeric_dtype(df["hhs_care"])
    assert df["hhs_care"].isna().sum() == 0


def test_numeric_conversion_all_columns(raw_df):
    df = rename_columns(raw_df)
    df = drop_fully_blank_rows(df)
    df = parse_dates(df)
    df = convert_numeric_columns(df)
    for col in ["apprehensions", "cbp_custody", "transfers", "hhs_care", "discharges"]:
        assert pd.api.types.is_numeric_dtype(df[col])


def test_validate_numeric_ranges_detects_negatives():
    df = pd.DataFrame({
        "apprehensions": [-1, 5],
        "cbp_custody": [10, 20],
        "transfers": [5, 5],
        "hhs_care": [100, 200],
        "discharges": [1, 2],
    })
    issues = validate_numeric_ranges(df)
    assert issues["apprehensions_negative_count"] == 1
    assert issues["cbp_custody_negative_count"] == 0


def test_check_duplicate_dates_none(raw_df):
    df = rename_columns(raw_df)
    df = drop_fully_blank_rows(df)
    df = parse_dates(df)
    dupes = check_duplicate_dates(df)
    assert len(dupes) == 0


def test_check_duplicate_dates_detected():
    df = pd.DataFrame({
        "date": pd.to_datetime(["2024-01-01", "2024-01-01", "2024-01-02"]),
        "apprehensions": [1, 2, 3],
    })
    dupes = check_duplicate_dates(df)
    assert len(dupes) == 2


def test_sort_and_deduplicate_removes_exact_duplicates():
    df = pd.DataFrame({
        "date": pd.to_datetime(["2024-01-02", "2024-01-01", "2024-01-01"]),
        "value": [1, 2, 2],
    })
    result = sort_and_deduplicate(df)
    assert len(result) == 2
    assert result["date"].iloc[0] == pd.Timestamp("2024-01-01")


def test_full_preprocessing_pipeline(raw_df):
    clean_df, report = run_preprocessing_pipeline(raw_df)
    assert clean_df.shape[0] == 5
    assert clean_df.isnull().sum().sum() == 0
    assert report["shape_after_blank_row_removal"] == (5, 6)
    assert report["numeric_validation"]["hhs_care_null_count"] == 0
    # chronological order
    assert clean_df["date"].is_monotonic_increasing


def test_preprocessing_handles_zero_values_correctly(raw_df):
    """Zero apprehensions/transfers/discharges on Jan 05 must survive as 0, not NaN."""
    clean_df, _ = run_preprocessing_pipeline(raw_df)
    jan5 = clean_df[clean_df["date"] == pd.Timestamp("2024-01-05")]
    assert jan5["apprehensions"].iloc[0] == 0
    assert jan5["transfers"].iloc[0] == 0
    assert jan5["discharges"].iloc[0] == 0
