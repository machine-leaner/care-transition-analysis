"""
visualizations.py
==================
Reusable Plotly chart-building functions. Shared by both the EDA notebook
and the Streamlit dashboard so chart logic is defined exactly once.

Each function returns a plotly.graph_objects.Figure and takes only plain
data (dataframe + column names), so it has no dependency on Streamlit.
"""

from __future__ import annotations

from typing import List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.config import DATE_COL

TEMPLATE = "plotly_white"


def line_chart(df: pd.DataFrame, y_cols: List[str], title: str, y_title: str = "") -> go.Figure:
    """Simple multi-series time-series line chart against the date column."""
    fig = go.Figure()
    for col in y_cols:
        if col in df.columns:
            fig.add_trace(go.Scatter(x=df[DATE_COL], y=df[col], mode="lines", name=col))
    fig.update_layout(title=title, template=TEMPLATE, xaxis_title="Date", yaxis_title=y_title,
                       legend=dict(orientation="h", yanchor="bottom", y=1.02))
    return fig


def area_chart(df: pd.DataFrame, y_col: str, title: str, y_title: str = "") -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df[DATE_COL], y=df[y_col], mode="lines", fill="tozeroy", name=y_col))
    fig.update_layout(title=title, template=TEMPLATE, xaxis_title="Date", yaxis_title=y_title)
    return fig


def dual_axis_chart(df: pd.DataFrame, y_left: str, y_right: str, title: str) -> go.Figure:
    """Two metrics on independent y-axes (e.g. HHS Care population vs Discharge Effectiveness %)."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=df[DATE_COL], y=df[y_left], name=y_left, mode="lines"), secondary_y=False)
    fig.add_trace(go.Scatter(x=df[DATE_COL], y=df[y_right], name=y_right, mode="lines",
                              line=dict(dash="dot")), secondary_y=True)
    fig.update_layout(title=title, template=TEMPLATE, legend=dict(orientation="h", yanchor="bottom", y=1.02))
    fig.update_yaxes(title_text=y_left, secondary_y=False)
    fig.update_yaxes(title_text=y_right, secondary_y=True)
    return fig


def scatter_with_trendline(df: pd.DataFrame, x_col: str, y_col: str, title: str) -> go.Figure:
    sub = df[[x_col, y_col]].dropna()
    fig = px.scatter(sub, x=x_col, y=y_col, trendline="ols", template=TEMPLATE, title=title)
    return fig


def correlation_heatmap(corr_matrix: pd.DataFrame, title: str) -> go.Figure:
    fig = px.imshow(corr_matrix, text_auto=".2f", color_continuous_scale="RdBu_r",
                     zmin=-1, zmax=1, template=TEMPLATE, title=title, aspect="auto")
    return fig


def bar_chart(df: pd.DataFrame, x_col: str, y_col: str, title: str, y_title: str = "") -> go.Figure:
    fig = px.bar(df, x=x_col, y=y_col, template=TEMPLATE, title=title)
    fig.update_layout(yaxis_title=y_title)
    return fig


def weekday_box_plot(df: pd.DataFrame, y_col: str, title: str) -> go.Figure:
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    fig = px.box(df, x="Day_of_Week", y=y_col, category_orders={"Day_of_Week": weekday_order},
                 template=TEMPLATE, title=title)
    return fig


def pipeline_flow_chart(df: pd.DataFrame, title: str = "UAC Care Pipeline -- Daily Flow") -> go.Figure:
    """Stacked view of the four flow stages over time."""
    fig = go.Figure()
    stages = [
        ("apprehensions", "Apprehensions (into CBP)"),
        ("cbp_custody", "In CBP Custody"),
        ("transfers", "Transferred out of CBP"),
        ("discharges", "Discharged from HHS Care"),
    ]
    for col, label in stages:
        if col in df.columns:
            fig.add_trace(go.Scatter(x=df[DATE_COL], y=df[col], mode="lines", name=label, stackgroup=None))
    fig.update_layout(title=title, template=TEMPLATE, xaxis_title="Date", yaxis_title="Children (count)",
                       legend=dict(orientation="h", yanchor="bottom", y=1.02))
    return fig


def pipeline_sankey(df: pd.DataFrame, title: str = "Aggregate Care Pipeline Flow (period totals)") -> go.Figure:
    """
    Sankey diagram of period-total flow volumes across pipeline stages.
    This represents aggregate totals, not a tracked cohort of individual
    children moving stage to stage.
    """
    totals = {
        "Apprehensions": df["apprehensions"].sum(),
        "CBP Custody (cumulative-days)": df["cbp_custody"].sum(),
        "Transfers": df["transfers"].sum(),
        "HHS Care (cumulative-days)": df["hhs_care"].sum(),
        "Discharges": df["discharges"].sum(),
    }
    labels = ["Apprehensions", "Transfers (out of CBP)", "HHS Care Intake", "Discharges"]
    fig = go.Figure(go.Sankey(
        node=dict(label=labels, pad=20, thickness=20),
        link=dict(
            source=[0, 1, 2],
            target=[1, 2, 3],
            value=[totals["Apprehensions"], totals["Transfers"], totals["Discharges"]],
        )
    ))
    fig.update_layout(title=title, template=TEMPLATE)
    return fig


def rolling_comparison_chart(df: pd.DataFrame, base_col: str, title: str, y_title: str = "") -> go.Figure:
    """Overlay the raw daily metric with its 7/14/30-day rolling averages."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df[DATE_COL], y=df[base_col], mode="lines", name="Daily", opacity=0.35))
    for window, dash in zip([7, 14, 30], ["solid", "dash", "dot"]):
        col = f"{base_col}_roll{window}"
        if col in df.columns:
            fig.add_trace(go.Scatter(x=df[DATE_COL], y=df[col], mode="lines",
                                      name=f"{window}-day avg", line=dict(dash=dash)))
    fig.update_layout(title=title, template=TEMPLATE, xaxis_title="Date", yaxis_title=y_title,
                       legend=dict(orientation="h", yanchor="bottom", y=1.02))
    return fig


def cumulative_pressure_chart(df: pd.DataFrame, title: str = "Cumulative Net Flow Pressure") -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df[DATE_COL], y=df["cumulative_net_flow_pressure"], mode="lines",
                              fill="tozeroy", name="Cumulative Net Flow Pressure"))
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    fig.update_layout(title=title, template=TEMPLATE, xaxis_title="Date",
                       yaxis_title="Cumulative (Apprehensions - Discharges)")
    return fig


def bottleneck_gantt(periods_df: pd.DataFrame, title: str) -> Optional[go.Figure]:
    """Horizontal timeline of detected bottleneck periods, colored by severity."""
    if periods_df is None or periods_df.empty:
        return None
    color_map = {"High": "#d62728", "Medium": "#ff7f0e", "Low": "#2ca02c", "Informational": "#1f77b4",
                 "Unknown": "#7f7f7f"}
    fig = px.timeline(
        periods_df, x_start="start_date", x_end="end_date", y="type",
        color="severity", color_discrete_map=color_map, template=TEMPLATE, title=title,
        hover_data=["duration_days", "average_value"],
    )
    fig.update_yaxes(autorange="reversed")
    return fig


def anomaly_scatter(df: pd.DataFrame, metric_col: str, anomaly_dates: pd.Series, title: str) -> go.Figure:
    """Line chart of a metric with anomaly dates highlighted as markers."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df[DATE_COL], y=df[metric_col], mode="lines", name=metric_col))
    anomalies = df[df[DATE_COL].isin(anomaly_dates)]
    fig.add_trace(go.Scatter(x=anomalies[DATE_COL], y=anomalies[metric_col], mode="markers",
                              name="Flagged anomaly", marker=dict(color="red", size=10, symbol="x")))
    fig.update_layout(title=title, template=TEMPLATE, xaxis_title="Date", yaxis_title=metric_col)
    return fig
