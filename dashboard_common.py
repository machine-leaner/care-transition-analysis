"""
dashboard_common.py
====================
Shared utilities for the Streamlit dashboard: cached data loading (running
the same pipeline used by run_pipeline.py so the dashboard never depends
on stale processed CSVs), a common sidebar with global filters whose
values persist across pages via st.session_state, and small formatting
helpers reused by every page.

This module intentionally contains NO analytical logic of its own -- it
only wires the src/ pipeline modules into Streamlit's caching and widget
layer, per the project requirement that app.py (and its pages) stay a
thin visualization/exploration layer over src/.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.data_loader import load_raw_data
from src.preprocessing import run_preprocessing_pipeline
from src.feature_engineering import run_feature_engineering
from src.config import (
    DATE_COL,
    DEFAULT_TRANSFER_EFFICIENCY_THRESHOLD,
    DEFAULT_DISCHARGE_EFFECTIVENESS_THRESHOLD,
    DEFAULT_SUSTAINED_DAYS,
    ROLLING_WINDOWS,
)

PAGE_ICON = "🧭"
BRAND_NAME = "Care Transition Efficiency & Placement Outcome Analytics"


@st.cache_data(show_spinner="Running data pipeline (load → validate → clean → engineer features)...")
def load_and_process_data() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """
    Run the full pipeline (raw load -> preprocessing -> feature engineering)
    once per Streamlit session/cache key and return:
      (clean_df, features_df, preprocessing_report)
    """
    raw_df = load_raw_data()
    clean_df, report = run_preprocessing_pipeline(raw_df)
    features_df = run_feature_engineering(clean_df)
    return clean_df, features_df, report


def configure_page(page_title: str):
    st.set_page_config(
        page_title=f"{page_title} | UAC Analytics",
        page_icon=PAGE_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )


def render_global_filters(features_df: pd.DataFrame) -> dict:
    """
    Render the shared sidebar controls (date range, rolling-window selector,
    bottleneck threshold controls, anomaly-detection toggle). Values are
    bound to st.session_state keys so they persist as the user navigates
    between pages.

    Returns a dict of the current filter values.
    """
    st.sidebar.markdown(f"### {BRAND_NAME}")
    st.sidebar.caption("Aggregate operational analytics for the UAC care pipeline. Not an individual-level or official system.")
    st.sidebar.divider()

    min_date = features_df[DATE_COL].min().date()
    max_date = features_df[DATE_COL].max().date()

    st.sidebar.markdown("**Date range**")
    date_range = st.sidebar.date_input(
        "Filter reported dates",
        value=st.session_state.get("date_range", (min_date, max_date)),
        min_value=min_date,
        max_value=max_date,
        key="date_range",
        label_visibility="collapsed",
    )
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = min_date, max_date

    st.sidebar.markdown("**Rolling window**")
    rolling_window = st.sidebar.select_slider(
        "Rolling average window (days)",
        options=ROLLING_WINDOWS,
        value=st.session_state.get("rolling_window", 7),
        key="rolling_window",
        label_visibility="collapsed",
    )

    with st.sidebar.expander("Bottleneck thresholds (project-defined)", expanded=False):
        transfer_threshold = st.slider(
            "Transfer Efficiency threshold (%)", min_value=0.0, max_value=150.0,
            value=st.session_state.get("transfer_threshold", DEFAULT_TRANSFER_EFFICIENCY_THRESHOLD),
            step=1.0, key="transfer_threshold",
        )
        discharge_threshold = st.slider(
            "Discharge Effectiveness threshold (%)", min_value=0.0, max_value=10.0,
            value=st.session_state.get("discharge_threshold", DEFAULT_DISCHARGE_EFFECTIVENESS_THRESHOLD),
            step=0.1, key="discharge_threshold",
        )
        sustained_days = st.slider(
            "Minimum sustained days", min_value=2, max_value=30,
            value=st.session_state.get("sustained_days", DEFAULT_SUSTAINED_DAYS),
            step=1, key="sustained_days",
        )
        st.caption("These are project-defined analytical thresholds, not official government benchmarks.")

    st.sidebar.markdown("**Anomaly detection**")
    anomaly_enabled = st.sidebar.toggle(
        "Enable anomaly detection", value=st.session_state.get("anomaly_enabled", True), key="anomaly_enabled",
    )

    st.sidebar.divider()
    st.sidebar.caption(
        "Data source: HHS Unaccompanied Alien Children Program public daily report. "
        "This dashboard analyzes aggregate flow only -- it cannot determine individual "
        "child outcomes, processing times, or sponsor/shelter-level performance."
    )

    return {
        "start_date": pd.Timestamp(start_date),
        "end_date": pd.Timestamp(end_date),
        "rolling_window": rolling_window,
        "transfer_threshold": transfer_threshold,
        "discharge_threshold": discharge_threshold,
        "sustained_days": sustained_days,
        "anomaly_enabled": anomaly_enabled,
    }


def apply_date_filter(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    mask = (df[DATE_COL] >= filters["start_date"]) & (df[DATE_COL] <= filters["end_date"])
    return df.loc[mask].reset_index(drop=True)


def metric_delta_color(value: float) -> str:
    if value is None or pd.isna(value):
        return "off"
    return "normal"


def fmt_pct(value: float, decimals: int = 1) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value:.{decimals}f}%"


def fmt_num(value: float, decimals: int = 0) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value:,.{decimals}f}"
