"""
feature_engineering.py
=======================
Adds calendar features and rolling-window smoothed metrics to the cleaned
UAC dataframe. Assumes input has already passed through preprocessing.py
(typed numeric columns, parsed dates, sorted chronologically).
"""

from __future__ import annotations

import pandas as pd

from src.config import (
    DATE_COL,
    TRANSFERS_COL,
    DISCHARGES_COL,
    ROLLING_WINDOWS,
)
from src.metrics import compute_all_kpis


def add_calendar_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add Year, Month, Month_Name, Week, Weekday, Day_of_Week columns."""
    df = df.copy()
    df["Year"] = df[DATE_COL].dt.year
    df["Month"] = df[DATE_COL].dt.month
    df["Month_Name"] = df[DATE_COL].dt.strftime("%B")
    df["Week"] = df[DATE_COL].dt.isocalendar().week.astype(int)
    df["Weekday"] = df[DATE_COL].dt.weekday  # 0=Monday
    df["Day_of_Week"] = df[DATE_COL].dt.strftime("%A")
    df["Quarter"] = df[DATE_COL].dt.quarter
    return df


def add_core_kpis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Attach all seven daily (non-rolling) KPI columns -- Transfer Efficiency,
    Discharge Effectiveness, CBP Transfer Rate, Net Flow Pressure,
    Cumulative Net Flow Pressure, CBP Transfer Gap, HHS Discharge Gap --
    via metrics.compute_all_kpis, so rolling averages and downstream
    analysis/dashboard pages have every KPI available.
    """
    return compute_all_kpis(df)


def add_rolling_features(df: pd.DataFrame, windows: list = None) -> pd.DataFrame:
    """
    Add rolling averages (7/14/30-day by default) for Transfers, Discharges,
    Transfer Efficiency, Discharge Effectiveness, and Net Accumulation.

    Rolling windows operate on chronological order (data must already be
    sorted by date) and use `min_periods=1` so early rows produce a partial
    average rather than NaN, which is documented in the KPI methodology.
    """
    if windows is None:
        windows = ROLLING_WINDOWS

    df = df.sort_values(DATE_COL).reset_index(drop=True).copy()

    base_cols = {
        "transfers": TRANSFERS_COL,
        "discharges": DISCHARGES_COL,
        "transfer_efficiency": "transfer_efficiency",
        "discharge_effectiveness": "discharge_effectiveness",
        "net_flow_pressure": "net_flow_pressure",
    }

    for window in windows:
        for label, col in base_cols.items():
            new_col = f"{label}_roll{window}"
            df[new_col] = df[col].rolling(window=window, min_periods=1).mean()

    return df


def run_feature_engineering(df: pd.DataFrame, windows: list = None) -> pd.DataFrame:
    """
    Full feature-engineering pipeline: sort chronologically, then add
    calendar features + all 7 KPIs (including Cumulative Net Flow Pressure,
    which depends on chronological order) + rolling averages.
    """
    df = df.sort_values(DATE_COL).reset_index(drop=True)
    df = add_calendar_features(df)
    df = add_core_kpis(df)
    df = add_rolling_features(df, windows=windows)
    return df
