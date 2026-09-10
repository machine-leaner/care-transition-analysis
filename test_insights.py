"""Tests for src.insights -- ensures insights are dynamically derived, not hard-coded."""
import numpy as np
import pandas as pd

from src.feature_engineering import run_feature_engineering
from src.bottleneck_detection import run_bottleneck_analysis
from src.anomaly_detection import run_anomaly_detection
from src.insights import generate_all_insights, generate_trend_insights, generate_pressure_insights


def _synthetic_df(n=60, seed=3):
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


def test_generate_all_insights_returns_list_of_strings():
    df = _synthetic_df()
    bn = run_bottleneck_analysis(df)
    an = run_anomaly_detection(df)
    insights = generate_all_insights(df, bottleneck_results=bn, anomaly_results=an)
    assert isinstance(insights, list)
    assert all(isinstance(s, str) for s in insights)
    assert len(insights) > 0


def test_insights_reflect_actual_data_values():
    """Changing the underlying data should change the generated insight text --
    proving insights are computed dynamically, not hard-coded."""
    df_a = _synthetic_df(seed=1)
    df_b = _synthetic_df(seed=99)
    insights_a = generate_trend_insights(df_a)
    insights_b = generate_trend_insights(df_b)
    assert insights_a != insights_b


def test_pressure_insights_mention_cumulative_value():
    df = _synthetic_df()
    insights = generate_pressure_insights(df)
    cumulative_val = df["cumulative_net_flow_pressure"].iloc[-1]
    combined = " ".join(insights)
    assert f"{cumulative_val:.0f}" in combined


def test_generate_all_insights_handles_no_bottlenecks_gracefully():
    dates = pd.date_range("2024-01-01", periods=10, freq="D")
    df = pd.DataFrame({
        "date": dates,
        "apprehensions": [10] * 10,
        "cbp_custody": [50] * 10,
        "transfers": [40] * 10,  # high efficiency, no bottleneck
        "hhs_care": [1000] * 10,
        "discharges": [50] * 10,
    })
    df = run_feature_engineering(df)
    bn = run_bottleneck_analysis(df)
    insights = generate_all_insights(df, bottleneck_results=bn)
    assert isinstance(insights, list)  # should not raise even with empty bottleneck frames
