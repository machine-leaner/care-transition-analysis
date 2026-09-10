"""Tests for src.feature_engineering."""
import pandas as pd

from src.feature_engineering import (
    add_calendar_features,
    add_core_kpis,
    add_rolling_features,
    run_feature_engineering,
)


def test_add_calendar_features(clean_df):
    result = add_calendar_features(clean_df)
    for col in ["Year", "Month", "Month_Name", "Week", "Weekday", "Day_of_Week", "Quarter"]:
        assert col in result.columns
    assert result["Year"].iloc[0] == 2024
    assert result["Month_Name"].iloc[0] == "January"


def test_add_core_kpis_attaches_all_kpis(clean_df):
    result = add_core_kpis(clean_df)
    assert "transfer_efficiency" in result.columns
    assert "discharge_effectiveness" in result.columns
    assert "cbp_transfer_rate" in result.columns
    assert "net_flow_pressure" in result.columns


def test_rolling_features_correct_window(clean_df):
    df = add_core_kpis(clean_df)
    result = add_rolling_features(df, windows=[7])
    assert "transfers_roll7" in result.columns
    # first value should equal the raw first value (min_periods=1 window of size 1)
    assert result["transfers_roll7"].iloc[0] == df["transfers"].iloc[0]
    # 7th row (index 6) should equal the mean of the first 7 raw values
    expected = df["transfers"].iloc[0:7].mean()
    assert abs(result["transfers_roll7"].iloc[6] - expected) < 1e-9


def test_rolling_features_no_nan_with_min_periods_1(clean_df):
    df = add_core_kpis(clean_df)
    result = add_rolling_features(df, windows=[7, 14, 30])
    for window in [7, 14, 30]:
        assert result[f"transfers_roll{window}"].isna().sum() == 0


def test_run_feature_engineering_full_pipeline(clean_df):
    result = run_feature_engineering(clean_df)
    # calendar
    assert "Year" in result.columns
    # KPIs
    assert "discharge_effectiveness" in result.columns
    # cumulative
    assert "cumulative_net_flow_pressure" in result.columns
    # rolling
    assert "discharge_effectiveness_roll30" in result.columns
    # chronological order preserved
    assert result["date"].is_monotonic_increasing


def test_cumulative_net_flow_pressure_is_monotonic_running_sum(clean_df):
    result = run_feature_engineering(clean_df)
    manual = result["net_flow_pressure"].cumsum()
    pd.testing.assert_series_equal(
        result["cumulative_net_flow_pressure"].reset_index(drop=True),
        manual.reset_index(drop=True),
        check_names=False,
    )
