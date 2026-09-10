"""Tests for src.anomaly_detection."""
import numpy as np
import pandas as pd

from src.anomaly_detection import rolling_zscore_anomalies, isolation_forest_anomalies
from src.feature_engineering import run_feature_engineering


def _df_with_spike():
    dates = pd.date_range("2024-01-01", periods=40, freq="D")
    rng = np.random.default_rng(0)
    apprehensions = rng.integers(20, 30, size=40).astype(float)
    apprehensions[30] = 500.0  # obvious spike
    df = pd.DataFrame({
        "date": dates,
        "apprehensions": apprehensions,
        "cbp_custody": rng.integers(50, 100, size=40),
        "transfers": rng.integers(10, 40, size=40),
        "hhs_care": rng.integers(1500, 2000, size=40),
        "discharges": rng.integers(5, 30, size=40),
    })
    return run_feature_engineering(df)


def test_rolling_zscore_flags_obvious_spike():
    df = _df_with_spike()
    result = rolling_zscore_anomalies(df, columns=["apprehensions"])
    flagged_dates = set(result["date"])
    assert df["date"].iloc[30] in flagged_dates


def test_rolling_zscore_returns_expected_columns():
    df = _df_with_spike()
    result = rolling_zscore_anomalies(df, columns=["apprehensions"])
    for col in ["date", "column", "value", "rolling_mean", "z_score", "method", "explanation"]:
        assert col in result.columns


def test_rolling_zscore_no_anomalies_on_flat_series():
    dates = pd.date_range("2024-01-01", periods=30, freq="D")
    df = pd.DataFrame({"date": dates, "apprehensions": [10] * 30})
    result = rolling_zscore_anomalies(df, columns=["apprehensions"])
    assert len(result) == 0


def test_isolation_forest_returns_expected_columns():
    df = _df_with_spike()
    result = isolation_forest_anomalies(df)
    for col in ["date", "anomaly_score", "method", "explanation"]:
        assert col in result.columns


def test_isolation_forest_flags_some_fraction_of_data():
    df = _df_with_spike()
    result = isolation_forest_anomalies(df, contamination=0.1)
    assert 0 < len(result) < len(df)


def test_isolation_forest_handles_missing_values_gracefully():
    df = _df_with_spike()
    df.loc[5, "apprehensions"] = np.nan
    # should not raise, and should simply exclude the row with NaN from fitting
    result = isolation_forest_anomalies(df)
    assert isinstance(result, pd.DataFrame)
