"""
bottleneck_detection.py
========================
Transparent, rule-based, configurable bottleneck detector.

Detects sustained periods where Transfer Efficiency or Discharge
Effectiveness stays below a configurable threshold for a configurable
minimum number of consecutive reported days. Also detects sustained
positive Net Flow Pressure ("accumulation periods").

All thresholds are PROJECT-DEFINED ANALYTICAL THRESHOLDS, not official
government thresholds -- see docs/05_Bottleneck_Analysis.md. This module
does not claim to prove the cause of any detected period; it only reports
where the configured condition was continuously true.
"""

from __future__ import annotations

from typing import List, Dict

import pandas as pd

from src.config import (
    DATE_COL,
    DEFAULT_TRANSFER_EFFICIENCY_THRESHOLD,
    DEFAULT_DISCHARGE_EFFECTIVENESS_THRESHOLD,
    DEFAULT_SUSTAINED_DAYS,
)


def _find_sustained_periods(
    df: pd.DataFrame,
    condition: pd.Series,
    metric_col: str,
    min_days: int,
) -> List[Dict[str, object]]:
    """
    Given a boolean condition series aligned to df (already sorted by
    date), find contiguous runs of True values with length >= min_days
    and summarize each as a bottleneck period.
    """
    df = df.reset_index(drop=True)
    condition = condition.reset_index(drop=True)

    periods = []
    run_start = None

    for i in range(len(df)):
        if condition.iloc[i]:
            if run_start is None:
                run_start = i
        else:
            if run_start is not None:
                run_len = i - run_start
                if run_len >= min_days:
                    periods.append(_summarize_run(df, metric_col, run_start, i - 1))
                run_start = None
    # handle run extending to the end of the data
    if run_start is not None:
        run_len = len(df) - run_start
        if run_len >= min_days:
            periods.append(_summarize_run(df, metric_col, run_start, len(df) - 1))

    return periods


def _summarize_run(df: pd.DataFrame, metric_col: str, start_idx: int, end_idx: int) -> Dict[str, object]:
    segment = df.iloc[start_idx:end_idx + 1]
    return {
        "metric": metric_col,
        "start_date": segment[DATE_COL].iloc[0],
        "end_date": segment[DATE_COL].iloc[-1],
        "duration_days": len(segment),
        "average_value": round(segment[metric_col].mean(), 2),
    }


def detect_transfer_bottlenecks(
    df: pd.DataFrame,
    threshold: float = DEFAULT_TRANSFER_EFFICIENCY_THRESHOLD,
    min_days: int = DEFAULT_SUSTAINED_DAYS,
) -> pd.DataFrame:
    """Detect sustained periods of Transfer Efficiency below `threshold`."""
    df = df.sort_values(DATE_COL).reset_index(drop=True)
    condition = df["transfer_efficiency"] < threshold
    periods = _find_sustained_periods(df, condition, "transfer_efficiency", min_days)
    result = pd.DataFrame(periods)
    if not result.empty:
        result["threshold"] = threshold
        result["type"] = "Potential CBP -> HHS transfer bottleneck"
        result["severity"] = result["average_value"].apply(lambda v: _severity(v, threshold))
    return result


def detect_discharge_bottlenecks(
    df: pd.DataFrame,
    threshold: float = DEFAULT_DISCHARGE_EFFECTIVENESS_THRESHOLD,
    min_days: int = DEFAULT_SUSTAINED_DAYS,
) -> pd.DataFrame:
    """Detect sustained periods of Discharge Effectiveness below `threshold`."""
    df = df.sort_values(DATE_COL).reset_index(drop=True)
    condition = df["discharge_effectiveness"] < threshold
    periods = _find_sustained_periods(df, condition, "discharge_effectiveness", min_days)
    result = pd.DataFrame(periods)
    if not result.empty:
        result["threshold"] = threshold
        result["type"] = "Potential HHS discharge bottleneck"
        result["severity"] = result["average_value"].apply(lambda v: _severity(v, threshold))
    return result


def detect_sustained_accumulation(
    df: pd.DataFrame,
    min_days: int = DEFAULT_SUSTAINED_DAYS,
) -> pd.DataFrame:
    """Detect sustained periods of positive Net Flow Pressure (accumulation)."""
    df = df.sort_values(DATE_COL).reset_index(drop=True)
    condition = df["net_flow_pressure"] > 0
    periods = _find_sustained_periods(df, condition, "net_flow_pressure", min_days)
    result = pd.DataFrame(periods)
    if not result.empty:
        result["type"] = "Sustained accumulation (net inflow > net outflow)"
        result["severity"] = "Informational"
    return result


def _severity(avg_value: float, threshold: float) -> str:
    """
    Simple, transparent severity bucketing based on how far below
    threshold the average value fell (project-defined, not a statistical
    test): >50% of threshold below = High, >20% = Medium, else Low.
    """
    if threshold == 0:
        return "Unknown"
    shortfall_pct = (threshold - avg_value) / threshold * 100
    if shortfall_pct >= 50:
        return "High"
    elif shortfall_pct >= 20:
        return "Medium"
    return "Low"


def run_bottleneck_analysis(
    df: pd.DataFrame,
    transfer_threshold: float = DEFAULT_TRANSFER_EFFICIENCY_THRESHOLD,
    discharge_threshold: float = DEFAULT_DISCHARGE_EFFECTIVENESS_THRESHOLD,
    min_days: int = DEFAULT_SUSTAINED_DAYS,
) -> Dict[str, pd.DataFrame]:
    """Run all three bottleneck/accumulation detectors and return results."""
    return {
        "transfer_bottlenecks": detect_transfer_bottlenecks(df, transfer_threshold, min_days),
        "discharge_bottlenecks": detect_discharge_bottlenecks(df, discharge_threshold, min_days),
        "sustained_accumulation": detect_sustained_accumulation(df, min_days),
    }
