"""
insights.py
============
Generates evidence-based, plain-language insight strings directly from
computed data. Every numeric value in every insight is pulled dynamically
from the dataframe / analysis results passed in -- nothing here is
hard-coded. If the underlying data changes, the insights change with it.
"""

from __future__ import annotations

from typing import List, Dict

import numpy as np
import pandas as pd

from src.config import DATE_COL
from src.analysis import trend_summary, outcome_stability_score


def _fmt(value: float, decimals: int = 1) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "N/A"
    return f"{value:.{decimals}f}"


def generate_trend_insights(df: pd.DataFrame, window_days: int = 30) -> List[str]:
    """Insights about recent directional movement in core KPIs."""
    insights = []
    metric_labels = {
        "transfer_efficiency": "Transfer efficiency",
        "discharge_effectiveness": "Discharge effectiveness",
        "cbp_transfer_rate": "CBP transfer rate",
    }
    for col, label in metric_labels.items():
        if col not in df.columns:
            continue
        summary = trend_summary(df, col, window_days=window_days)
        if summary["direction"] == "Insufficient data":
            continue
        pct = summary["pct_change_over_window"]
        if np.isnan(pct):
            continue
        direction_word = "increased" if pct > 0 else "decreased"
        insights.append(
            f"{label} {direction_word} by {_fmt(abs(pct))}% over the most recent "
            f"{window_days} reported days (from {_fmt(summary['start_value'])}% to "
            f"{_fmt(summary['end_value'])}%)."
        )
    return insights


def generate_pressure_insights(df: pd.DataFrame) -> List[str]:
    """Insights about net flow pressure and accumulation."""
    insights = []
    df_sorted = df.sort_values(DATE_COL)
    positive_streak = 0
    max_streak = 0
    for val in df_sorted["net_flow_pressure"]:
        if val > 0:
            positive_streak += 1
            max_streak = max(max_streak, positive_streak)
        else:
            positive_streak = 0
    if max_streak >= 3:
        insights.append(
            f"Positive net flow pressure (more apprehensions than discharges) persisted for "
            f"{max_streak} consecutive reported days at its longest stretch in the dataset."
        )

    cumulative_end = df_sorted["cumulative_net_flow_pressure"].iloc[-1] if len(df_sorted) else np.nan
    if not np.isnan(cumulative_end):
        direction = "net accumulation" if cumulative_end > 0 else "net drawdown"
        insights.append(
            f"Cumulative net flow pressure across the full observed period is {_fmt(cumulative_end, 0)}, "
            f"indicating overall {direction} relative to the start of the dataset."
        )
    return insights


def generate_bottleneck_insights(bottleneck_results: Dict[str, pd.DataFrame]) -> List[str]:
    """Insights summarizing detected bottleneck periods."""
    insights = []
    labels = {
        "transfer_bottlenecks": "potential CBP-to-HHS transfer bottleneck period(s)",
        "discharge_bottlenecks": "potential HHS discharge bottleneck period(s)",
        "sustained_accumulation": "sustained accumulation period(s)",
    }
    for key, label in labels.items():
        result = bottleneck_results.get(key)
        if result is not None and not result.empty:
            n = len(result)
            longest = result.loc[result["duration_days"].idxmax()]
            insights.append(
                f"{n} {label} identified using project-defined thresholds; the longest ran "
                f"{int(longest['duration_days'])} days ({longest['start_date'].date()} to "
                f"{longest['end_date'].date()})."
            )
    return insights


def generate_variability_insights(df: pd.DataFrame) -> List[str]:
    """Insights about discharge stability, comparing first half vs second half of the data."""
    insights = []
    df_sorted = df.sort_values(DATE_COL).reset_index(drop=True)
    midpoint = len(df_sorted) // 2
    first_half = df_sorted.iloc[:midpoint]
    second_half = df_sorted.iloc[midpoint:]

    std_first = first_half["discharge_effectiveness"].std()
    std_second = second_half["discharge_effectiveness"].std()

    if not (np.isnan(std_first) or np.isnan(std_second)):
        if std_first > std_second:
            insights.append(
                f"Discharge effectiveness variability was higher in the first half of the observed "
                f"period (std = {_fmt(std_first)}) than the second half (std = {_fmt(std_second)})."
            )
        else:
            insights.append(
                f"Discharge effectiveness variability was higher in the second half of the observed "
                f"period (std = {_fmt(std_second)}) than the first half (std = {_fmt(std_first)})."
            )

    score = outcome_stability_score(df)
    if not np.isnan(score):
        insights.append(f"The project-defined Outcome Stability Score for discharge effectiveness is {_fmt(score, 1)} out of 100.")

    return insights


def generate_anomaly_insights(anomaly_results: Dict[str, pd.DataFrame]) -> List[str]:
    """Insights summarizing anomaly-detection results."""
    insights = []
    zscore_df = anomaly_results.get("rolling_zscore")
    iso_df = anomaly_results.get("isolation_forest")

    if zscore_df is not None and not zscore_df.empty:
        insights.append(
            f"The rolling z-score method flagged {zscore_df['date'].nunique()} distinct date(s) "
            f"with at least one metric deviating sharply from its recent trailing average."
        )
    if iso_df is not None and not iso_df.empty:
        insights.append(
            f"Isolation Forest flagged {len(iso_df)} date(s) as multivariate outliers across the "
            f"combined set of flow and KPI features."
        )
    return insights


def generate_all_insights(
    df: pd.DataFrame,
    bottleneck_results: Dict[str, pd.DataFrame] = None,
    anomaly_results: Dict[str, pd.DataFrame] = None,
    window_days: int = 30,
) -> List[str]:
    """Aggregate all insight categories into a single evidence-based list."""
    insights: List[str] = []
    insights += generate_trend_insights(df, window_days=window_days)
    insights += generate_pressure_insights(df)
    if bottleneck_results is not None:
        insights += generate_bottleneck_insights(bottleneck_results)
    insights += generate_variability_insights(df)
    if anomaly_results is not None:
        insights += generate_anomaly_insights(anomaly_results)
    return insights
