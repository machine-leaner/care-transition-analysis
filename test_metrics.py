"""Tests for src.metrics -- KPI formulas and zero-denominator handling."""
import numpy as np
import pandas as pd

from src.metrics import (
    transfer_efficiency,
    discharge_effectiveness,
    cbp_transfer_rate,
    net_flow_pressure,
    cumulative_net_flow_pressure,
    cbp_transfer_gap,
    hhs_discharge_gap,
    compute_all_kpis,
)


def _df():
    return pd.DataFrame({
        "apprehensions": [10, 20, 0, 15],
        "cbp_custody": [50, 0, 30, 40],
        "transfers": [25, 10, 0, 20],
        "hhs_care": [2000, 1000, 0, 1500],
        "discharges": [100, 50, 0, 75],
    })


def test_transfer_efficiency_basic():
    result = transfer_efficiency(_df())
    assert result.iloc[0] == 50.0  # 25/50*100


def test_transfer_efficiency_zero_denominator_is_nan():
    result = transfer_efficiency(_df())
    assert np.isnan(result.iloc[1])  # cbp_custody = 0


def test_discharge_effectiveness_basic():
    result = discharge_effectiveness(_df())
    assert result.iloc[0] == 5.0  # 100/2000*100


def test_discharge_effectiveness_zero_denominator_is_nan():
    result = discharge_effectiveness(_df())
    assert np.isnan(result.iloc[2])  # hhs_care = 0


def test_cbp_transfer_rate_basic():
    result = cbp_transfer_rate(_df())
    assert result.iloc[0] == 250.0  # 25/10*100


def test_cbp_transfer_rate_zero_denominator_is_nan():
    result = cbp_transfer_rate(_df())
    assert np.isnan(result.iloc[2])  # apprehensions = 0


def test_net_flow_pressure():
    result = net_flow_pressure(_df())
    assert result.iloc[0] == 10 - 100
    assert result.iloc[3] == 15 - 75


def test_cumulative_net_flow_pressure_is_running_sum():
    result = cumulative_net_flow_pressure(_df())
    expected = net_flow_pressure(_df()).cumsum()
    pd.testing.assert_series_equal(result, expected)


def test_cbp_transfer_gap():
    result = cbp_transfer_gap(_df())
    assert result.iloc[0] == 50 - 25


def test_hhs_discharge_gap():
    result = hhs_discharge_gap(_df())
    assert result.iloc[0] == 2000 - 100


def test_compute_all_kpis_adds_all_columns():
    result = compute_all_kpis(_df())
    expected_cols = {
        "transfer_efficiency", "discharge_effectiveness", "cbp_transfer_rate",
        "net_flow_pressure", "cumulative_net_flow_pressure", "cbp_transfer_gap",
        "hhs_discharge_gap",
    }
    assert expected_cols.issubset(set(result.columns))
    # original columns preserved
    assert "apprehensions" in result.columns


def test_zero_denominator_never_produces_inf():
    """No ratio KPI should ever emit +/-inf for a zero denominator."""
    result = compute_all_kpis(_df())
    for col in ["transfer_efficiency", "discharge_effectiveness", "cbp_transfer_rate"]:
        assert not np.isinf(result[col]).any()
