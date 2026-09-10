"""Tests for src.analysis."""
import numpy as np
import pandas as pd

from src.analysis import (
    descriptive_statistics,
    classify_trend,
    trend_summary,
    outcome_stability_score,
    outcome_stability_metrics,
    weekday_comparison,
    monthly_aggregation,
    month_over_month_change,
)
from src.feature_engineering import run_feature_engineering


def _synthetic_df(n=60, seed=1):
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({
        "date": dates,
        "apprehensions": rng.integers(10, 60, size=n),
        "cbp_custody": rng.integers(50, 200, size=n),
        "transfers": rng.integers(10, 80, size=n),
        "hhs_care": rng.integers(1500, 3000, size=n),
        "discharges": rng.integers(5, 50, size=n),
    })
    return run_feature_engineering(df)


def test_descriptive_statistics_shape():
    df = _synthetic_df()
    result = descriptive_statistics(df, columns=["apprehensions", "transfers"])
    assert "mean" in result.columns
    assert "coefficient_of_variation" in result.columns
    assert len(result) == 2


def test_classify_trend_increasing():
    series = pd.Series(np.arange(30) * 2.0 + 10)
    assert classify_trend(series) == "Increasing"


def test_classify_trend_decreasing():
    series = pd.Series(100 - np.arange(30) * 2.0)
    assert classify_trend(series) == "Decreasing"


def test_classify_trend_stable():
    series = pd.Series(np.full(30, 50.0) + np.random.default_rng(0).normal(0, 0.01, 30))
    assert classify_trend(series) == "Stable"


def test_classify_trend_insufficient_data():
    series = pd.Series([1.0, 2.0])
    assert classify_trend(series) == "Insufficient data"


def test_trend_summary_structure():
    df = _synthetic_df()
    result = trend_summary(df, "transfer_efficiency", window_days=20)
    assert "direction" in result
    assert "pct_change_over_window" in result
    assert result["window_days"] == 20


def test_outcome_stability_score_range():
    df = _synthetic_df()
    score = outcome_stability_score(df)
    assert 0 <= score <= 100


def test_outcome_stability_score_perfectly_stable_is_100():
    dates = pd.date_range("2024-01-01", periods=20, freq="D")
    df = pd.DataFrame({
        "date": dates,
        "apprehensions": [10] * 20,
        "cbp_custody": [50] * 20,
        "transfers": [20] * 20,
        "hhs_care": [1000] * 20,
        "discharges": [50] * 20,  # constant -> discharge_effectiveness constant -> std=0
    })
    df = run_feature_engineering(df)
    score = outcome_stability_score(df)
    assert score == 100.0


def test_outcome_stability_metrics_keys():
    df = _synthetic_df()
    metrics = outcome_stability_metrics(df)
    for key in ["mean_discharge_effectiveness", "std_discharge_effectiveness",
                "coefficient_of_variation", "mean_rolling_std_14d"]:
        assert key in metrics


def test_weekday_comparison_has_all_present_weekdays():
    df = _synthetic_df(n=30)
    result = weekday_comparison(df)
    assert len(result) > 0


def test_monthly_aggregation_and_mom_change():
    df = _synthetic_df(n=90)
    monthly = monthly_aggregation(df, columns=["apprehensions"])
    assert "year_month" in monthly.columns
    mom = month_over_month_change(monthly, "apprehensions")
    assert "apprehensions_mom_pct_change" in mom.columns
    # first month has no prior month to compare to
    assert np.isnan(mom["apprehensions_mom_pct_change"].iloc[0])
