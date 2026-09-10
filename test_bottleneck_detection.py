"""Tests for src.bottleneck_detection."""
import pandas as pd

from src.bottleneck_detection import (
    detect_transfer_bottlenecks,
    detect_discharge_bottlenecks,
    detect_sustained_accumulation,
    _severity,
)


def _make_df(transfer_eff_values, discharge_eff_values=None, net_flow_values=None):
    n = len(transfer_eff_values)
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    df = pd.DataFrame({
        "date": dates,
        "transfer_efficiency": transfer_eff_values,
        "discharge_effectiveness": discharge_eff_values or [50] * n,
        "net_flow_pressure": net_flow_values or [0] * n,
    })
    return df


def test_detects_sustained_low_transfer_efficiency():
    # 10 days below threshold (60), min_days=7 -> should detect one period
    values = [50] * 10
    df = _make_df(values)
    result = detect_transfer_bottlenecks(df, threshold=60, min_days=7)
    assert len(result) == 1
    assert result.iloc[0]["duration_days"] == 10


def test_does_not_detect_short_dips_below_min_days():
    # only 3 consecutive low days, min_days=7 -> should NOT detect
    values = [80, 80, 50, 50, 50, 80, 80]
    df = _make_df(values)
    result = detect_transfer_bottlenecks(df, threshold=60, min_days=7)
    assert len(result) == 0


def test_detects_multiple_separate_periods():
    values = [50] * 8 + [80] * 3 + [40] * 9
    df = _make_df(values)
    result = detect_transfer_bottlenecks(df, threshold=60, min_days=7)
    assert len(result) == 2


def test_run_extending_to_end_of_data_detected():
    values = [80, 80, 80] + [30] * 8  # bottleneck runs to the very last row
    df = _make_df(values)
    result = detect_transfer_bottlenecks(df, threshold=60, min_days=7)
    assert len(result) == 1
    assert result.iloc[0]["end_date"] == df["date"].iloc[-1]


def test_discharge_bottleneck_detection():
    values = [50] * 10  # transfer_efficiency irrelevant here
    df = _make_df(values, discharge_eff_values=[5] * 10)
    result = detect_discharge_bottlenecks(df, threshold=20, min_days=7)
    assert len(result) == 1


def test_sustained_accumulation_detection():
    values = [50] * 10
    net_flow = [10] * 10  # always positive -> accumulation
    df = _make_df(values, net_flow_values=net_flow)
    result = detect_sustained_accumulation(df, min_days=7)
    assert len(result) == 1
    assert result.iloc[0]["type"] == "Sustained accumulation (net inflow > net outflow)"


def test_severity_buckets():
    assert _severity(avg_value=10, threshold=60) == "High"     # 83% shortfall
    assert _severity(avg_value=45, threshold=60) == "Medium"   # 25% shortfall
    assert _severity(avg_value=55, threshold=60) == "Low"      # 8% shortfall


def test_bottleneck_result_includes_required_fields():
    values = [50] * 10
    df = _make_df(values)
    result = detect_transfer_bottlenecks(df, threshold=60, min_days=7)
    for col in ["start_date", "end_date", "duration_days", "metric", "average_value", "threshold", "severity"]:
        assert col in result.columns
