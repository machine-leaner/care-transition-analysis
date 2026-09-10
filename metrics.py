"""
metrics.py
==========
KPI formulas for the Care Transition Efficiency & Placement Outcome
Analytics project. Every KPI here is an AGGREGATE, PROJECT-DEFINED
indicator computed from daily aggregate counts. None of these metrics
measure individual processing time, individual outcome probability, or
true end-to-end pipeline throughput -- see docs/04_KPI_Definitions.md and
docs/08_Limitations.md for full discussion.

All ratio-based KPIs handle zero denominators explicitly by returning NaN
(not 0, not inf) so that downstream rolling/statistical calculations do
not silently misrepresent an undefined ratio as a real value.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.config import (
    APPREHENSIONS_COL,
    CBP_CUSTODY_COL,
    TRANSFERS_COL,
    HHS_CARE_COL,
    DISCHARGES_COL,
)


def _safe_ratio(numerator: pd.Series, denominator: pd.Series, multiplier: float = 1.0) -> pd.Series:
    """
    Compute numerator / denominator * multiplier, returning NaN wherever
    the denominator is zero or missing rather than raising or returning
    inf. This avoids fabricating a 0% or infinite value for an undefined
    ratio.
    """
    denominator = denominator.replace(0, np.nan)
    return (numerator / denominator) * multiplier


def transfer_efficiency(df: pd.DataFrame) -> pd.Series:
    """
    KPI 1 -- Transfer Efficiency = Transfers / CBP Custody * 100

    Interpretation: an aggregate indicator of transfers out of CBP custody
    relative to the CBP custody population on that day. This is NOT a
    direct measurement of individual processing speed.
    """
    return _safe_ratio(df[TRANSFERS_COL], df[CBP_CUSTODY_COL], 100.0)


def discharge_effectiveness(df: pd.DataFrame) -> pd.Series:
    """
    KPI 2 -- Discharge Effectiveness = Discharges / HHS Care * 100

    Interpretation: an aggregate indicator of discharge volume relative to
    the HHS care population on that day. This is NOT an individual
    probability of discharge.
    """
    return _safe_ratio(df[DISCHARGES_COL], df[HHS_CARE_COL], 100.0)


def cbp_transfer_rate(df: pd.DataFrame) -> pd.Series:
    """
    KPI 3 -- CBP Transfer Rate = Transfers / Apprehensions * 100

    A flow-based complementary metric relating same-day transfers to
    same-day apprehensions. Because these are same-day aggregate counts
    (not matched-cohort figures), this should be read as a flow-balance
    indicator, not a completion rate for a specific cohort of children.
    """
    return _safe_ratio(df[TRANSFERS_COL], df[APPREHENSIONS_COL], 100.0)


def net_flow_pressure(df: pd.DataFrame) -> pd.Series:
    """
    KPI 4 -- Net Flow Pressure = Apprehensions - Discharges

    An aggregate inflow/outflow pressure indicator. Positive values
    indicate more children entering the system (via apprehension) than
    exiting it (via discharge) on that day; negative values indicate the
    reverse.
    """
    return df[APPREHENSIONS_COL] - df[DISCHARGES_COL]


def cumulative_net_flow_pressure(df: pd.DataFrame) -> pd.Series:
    """
    KPI 5 -- Cumulative Net Flow Pressure = running cumulative sum of
    daily Net Flow Pressure. Used to identify sustained accumulation
    periods rather than single-day noise.
    """
    return net_flow_pressure(df).cumsum()


def cbp_transfer_gap(df: pd.DataFrame) -> pd.Series:
    """KPI 6 -- CBP Transfer Gap = CBP Custody - Transfers."""
    return df[CBP_CUSTODY_COL] - df[TRANSFERS_COL]


def hhs_discharge_gap(df: pd.DataFrame) -> pd.Series:
    """KPI 7 -- HHS Discharge Gap = HHS Care - Discharges."""
    return df[HHS_CARE_COL] - df[DISCHARGES_COL]


def compute_all_kpis(df: pd.DataFrame) -> pd.DataFrame:
    """Attach all seven KPI columns to a copy of the input dataframe."""
    out = df.copy()
    out["transfer_efficiency"] = transfer_efficiency(df)
    out["discharge_effectiveness"] = discharge_effectiveness(df)
    out["cbp_transfer_rate"] = cbp_transfer_rate(df)
    out["net_flow_pressure"] = net_flow_pressure(df)
    out["cumulative_net_flow_pressure"] = cumulative_net_flow_pressure(df)
    out["cbp_transfer_gap"] = cbp_transfer_gap(df)
    out["hhs_discharge_gap"] = hhs_discharge_gap(df)
    return out
