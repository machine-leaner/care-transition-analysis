"""
analysis.py
===========
Statistical, temporal, and stability analysis functions operating on the
feature-engineered dataframe (output of feature_engineering.run_feature_engineering).

Covers: descriptive statistics, correlation analysis, month-over-month
change, weekday comparison, trend classification, and the project-defined
Outcome Stability Score.
"""

from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

from src.config import (
    DATE_COL,
    APPREHENSIONS_COL,
    CBP_CUSTODY_COL,
    TRANSFERS_COL,
    HHS_CARE_COL,
    DISCHARGES_COL,
    STABILITY_SCORE_MAX_CV,
)


# ---------------------------------------------------------------------------
# Descriptive statistics
# ---------------------------------------------------------------------------

def descriptive_statistics(df: pd.DataFrame, columns: List[str] = None) -> pd.DataFrame:
    """Mean, median, min, max, std, and quartiles for the given columns."""
    if columns is None:
        columns = [APPREHENSIONS_COL, CBP_CUSTODY_COL, TRANSFERS_COL, HHS_CARE_COL, DISCHARGES_COL]
    desc = df[columns].describe(percentiles=[0.25, 0.5, 0.75]).T
    desc["coefficient_of_variation"] = desc["std"] / desc["mean"]
    return desc


# ---------------------------------------------------------------------------
# Correlation analysis
# ---------------------------------------------------------------------------

def correlation_analysis(df: pd.DataFrame, columns: List[str] = None) -> Dict[str, pd.DataFrame]:
    """
    Pearson and Spearman correlation matrices for the given (or default
    flow) columns. Correlation does not imply causation -- interpret
    alongside docs/08_Limitations.md.
    """
    if columns is None:
        columns = [APPREHENSIONS_COL, CBP_CUSTODY_COL, TRANSFERS_COL, HHS_CARE_COL, DISCHARGES_COL]
    return {
        "pearson": df[columns].corr(method="pearson"),
        "spearman": df[columns].corr(method="spearman"),
    }


def pairwise_correlation(df: pd.DataFrame, col_a: str, col_b: str) -> Dict[str, float]:
    """Pearson and Spearman correlation (with p-values) between two columns."""
    sub = df[[col_a, col_b]].dropna()
    pearson_r, pearson_p = scipy_stats.pearsonr(sub[col_a], sub[col_b])
    spearman_r, spearman_p = scipy_stats.spearmanr(sub[col_a], sub[col_b])
    return {
        "pearson_r": pearson_r,
        "pearson_p": pearson_p,
        "spearman_r": spearman_r,
        "spearman_p": spearman_p,
        "n": len(sub),
    }


# ---------------------------------------------------------------------------
# Temporal analysis
# ---------------------------------------------------------------------------

def monthly_aggregation(df: pd.DataFrame, columns: List[str] = None, agg: str = "mean") -> pd.DataFrame:
    """Aggregate metrics by calendar month (Year-Month)."""
    if columns is None:
        columns = [APPREHENSIONS_COL, CBP_CUSTODY_COL, TRANSFERS_COL, HHS_CARE_COL, DISCHARGES_COL,
                   "transfer_efficiency", "discharge_effectiveness", "net_flow_pressure"]
    columns = [c for c in columns if c in df.columns]
    tmp = df.copy()
    tmp["year_month"] = tmp[DATE_COL].dt.to_period("M").astype(str)
    return tmp.groupby("year_month")[columns].agg(agg).reset_index()


def month_over_month_change(monthly_df: pd.DataFrame, value_col: str) -> pd.DataFrame:
    """Percentage change of `value_col` from the previous month."""
    out = monthly_df.copy()
    out[f"{value_col}_mom_pct_change"] = out[value_col].pct_change() * 100
    return out


def weekday_comparison(df: pd.DataFrame, columns: List[str] = None) -> pd.DataFrame:
    """Mean and median of key metrics grouped by day of week."""
    if columns is None:
        columns = [APPREHENSIONS_COL, TRANSFERS_COL, DISCHARGES_COL, "transfer_efficiency", "discharge_effectiveness"]
    columns = [c for c in columns if c in df.columns]
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    grouped = df.groupby("Day_of_Week")[columns].agg(["mean", "median", "count"])
    grouped = grouped.reindex([d for d in weekday_order if d in grouped.index])
    return grouped


def quarterly_aggregation(df: pd.DataFrame, columns: List[str] = None, agg: str = "mean") -> pd.DataFrame:
    """Aggregate metrics by year-quarter, if the date range supports it."""
    if columns is None:
        columns = [APPREHENSIONS_COL, TRANSFERS_COL, DISCHARGES_COL, "transfer_efficiency", "discharge_effectiveness"]
    columns = [c for c in columns if c in df.columns]
    tmp = df.copy()
    tmp["year_quarter"] = tmp[DATE_COL].dt.to_period("Q").astype(str)
    return tmp.groupby("year_quarter")[columns].agg(agg).reset_index()


# ---------------------------------------------------------------------------
# Trend classification (transparent, rule-based)
# ---------------------------------------------------------------------------

def classify_trend(series: pd.Series, flat_threshold_pct: float = 2.0) -> str:
    """
    Classify a metric's trend as 'Improving', 'Declining', or 'Stable'
    using an ordinary-least-squares regression slope over the series
    index, normalized as a percent change over the series' mean.

    Methodology (documented in docs/02_Methodology.md):
      1. Fit y = a*x + b via least squares over the series (x = 0..n-1).
      2. Compute total_projected_change = a * (n-1).
      3. Express as a percentage of the series mean.
      4. If |pct| < flat_threshold_pct -> 'Stable'.
         Else sign determines 'Improving' (for metrics where higher = better)
         or 'Declining'.

    NOTE: This function returns the raw direction ('Increasing'/'Decreasing'/
    'Stable') based purely on slope sign -- callers decide whether an
    increase is "good" or "bad" for a given metric (e.g. rising Net Flow
    Pressure is not an "improvement").
    """
    s = series.dropna()
    if len(s) < 3:
        return "Insufficient data"
    x = np.arange(len(s))
    slope, intercept, r_value, p_value, std_err = scipy_stats.linregress(x, s.values)
    mean_val = s.mean()
    if mean_val == 0 or np.isnan(mean_val):
        return "Insufficient data"
    total_change = slope * (len(s) - 1)
    pct_change = (total_change / abs(mean_val)) * 100
    if abs(pct_change) < flat_threshold_pct:
        return "Stable"
    return "Increasing" if pct_change > 0 else "Decreasing"


def trend_summary(df: pd.DataFrame, column: str, window_days: int = 30) -> Dict[str, object]:
    """Trend classification for a column over the most recent `window_days`."""
    recent = df.sort_values(DATE_COL).tail(window_days)
    direction = classify_trend(recent[column])
    pct_change = np.nan
    s = recent[column].dropna()
    if len(s) >= 2 and s.iloc[0] != 0:
        pct_change = ((s.iloc[-1] - s.iloc[0]) / abs(s.iloc[0])) * 100
    return {
        "column": column,
        "window_days": window_days,
        "direction": direction,
        "start_value": s.iloc[0] if len(s) else np.nan,
        "end_value": s.iloc[-1] if len(s) else np.nan,
        "pct_change_over_window": pct_change,
    }


# ---------------------------------------------------------------------------
# Outcome stability (discharge effectiveness stability)
# ---------------------------------------------------------------------------

def outcome_stability_metrics(df: pd.DataFrame) -> Dict[str, float]:
    """
    Mean, standard deviation, coefficient of variation, and rolling std of
    Discharge Effectiveness.
    """
    series = df["discharge_effectiveness"].dropna()
    mean_val = series.mean()
    std_val = series.std()
    cv = std_val / mean_val if mean_val else np.nan
    rolling_std = df["discharge_effectiveness"].rolling(window=14, min_periods=3).std()
    return {
        "mean_discharge_effectiveness": mean_val,
        "std_discharge_effectiveness": std_val,
        "coefficient_of_variation": cv,
        "mean_rolling_std_14d": rolling_std.mean(),
    }


def outcome_stability_score(df: pd.DataFrame) -> float:
    """
    PROJECT-DEFINED Outcome Stability Score (0-100, NOT an official
    government KPI). Higher = more stable/consistent discharge
    effectiveness over the period.

    Formula (documented in docs/04_KPI_Definitions.md):
        cv = std(discharge_effectiveness) / mean(discharge_effectiveness)
        cv_clipped = clip(cv, 0, STABILITY_SCORE_MAX_CV)
        score = 100 * (1 - cv_clipped / STABILITY_SCORE_MAX_CV)

    A coefficient of variation of 0 (perfectly consistent) maps to a score
    of 100; a CV at or above STABILITY_SCORE_MAX_CV (default 1.0, i.e.
    std >= mean) maps to a score of 0.
    """
    metrics = outcome_stability_metrics(df)
    cv = metrics["coefficient_of_variation"]
    if cv is None or np.isnan(cv):
        return np.nan
    cv_clipped = float(np.clip(cv, 0, STABILITY_SCORE_MAX_CV))
    score = 100 * (1 - cv_clipped / STABILITY_SCORE_MAX_CV)
    return round(score, 2)
