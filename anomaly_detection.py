"""
anomaly_detection.py
=====================
Two independent anomaly-detection approaches for methodological comparison:

  1. Rolling z-score (simple statistical method) -- flags a day as unusual
     when a metric deviates more than ROLLING_ZSCORE_THRESHOLD standard
     deviations from its own trailing rolling mean.
  2. Isolation Forest (machine-learning method, scikit-learn) -- flags
     multivariate outliers across several numeric features simultaneously.

Both methods identify statistically UNUSUAL observations. Neither method
confirms an operational failure, data-entry error, or true anomaly in the
underlying program -- see docs/06_Anomaly_Analysis.md.
"""

from __future__ import annotations

from typing import List

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from src.config import (
    DATE_COL,
    APPREHENSIONS_COL,
    CBP_CUSTODY_COL,
    TRANSFERS_COL,
    HHS_CARE_COL,
    DISCHARGES_COL,
    ISOLATION_FOREST_CONTAMINATION,
    ROLLING_ZSCORE_WINDOW,
    ROLLING_ZSCORE_THRESHOLD,
)

DEFAULT_ISO_FEATURES = [
    APPREHENSIONS_COL,
    CBP_CUSTODY_COL,
    TRANSFERS_COL,
    HHS_CARE_COL,
    DISCHARGES_COL,
    "transfer_efficiency",
    "discharge_effectiveness",
    "net_flow_pressure",
]


def rolling_zscore_anomalies(
    df: pd.DataFrame,
    columns: List[str] = None,
    window: int = ROLLING_ZSCORE_WINDOW,
    threshold: float = ROLLING_ZSCORE_THRESHOLD,
) -> pd.DataFrame:
    """
    For each specified column, compute a rolling z-score
    (value - rolling_mean) / rolling_std using a trailing window, and flag
    rows where |z| > threshold.

    Returns a long-format dataframe: one row per (date, column) anomaly,
    with the z-score and a plain-language explanation.
    """
    if columns is None:
        columns = [APPREHENSIONS_COL, TRANSFERS_COL, HHS_CARE_COL, DISCHARGES_COL,
                   "transfer_efficiency", "discharge_effectiveness"]
    columns = [c for c in columns if c in df.columns]

    df = df.sort_values(DATE_COL).reset_index(drop=True)
    records = []
    for col in columns:
        roll_mean = df[col].rolling(window=window, min_periods=5).mean()
        roll_std = df[col].rolling(window=window, min_periods=5).std()
        z = (df[col] - roll_mean) / roll_std.replace(0, np.nan)
        flagged = z.abs() > threshold
        for idx in df.index[flagged.fillna(False)]:
            records.append({
                "date": df.loc[idx, DATE_COL],
                "column": col,
                "value": df.loc[idx, col],
                "rolling_mean": round(roll_mean.loc[idx], 2),
                "z_score": round(z.loc[idx], 2),
                "method": "Rolling Z-Score",
                "explanation": (
                    f"{col} = {df.loc[idx, col]:.1f} deviates {z.loc[idx]:.1f} standard "
                    f"deviations from its trailing {window}-day rolling mean of "
                    f"{roll_mean.loc[idx]:.1f}."
                ),
            })
    return pd.DataFrame(records)


def isolation_forest_anomalies(
    df: pd.DataFrame,
    features: List[str] = None,
    contamination: float = ISOLATION_FOREST_CONTAMINATION,
    random_state: int = 42,
) -> pd.DataFrame:
    """
    Fit an Isolation Forest across the given numeric features and flag the
    most multivariate-unusual observations. Returns a dataframe with one
    row per flagged date, the anomaly score, and which features were most
    extreme (by z-score against the full-sample mean) as a simple
    explanation aid.
    """
    if features is None:
        features = DEFAULT_ISO_FEATURES
    features = [f for f in features if f in df.columns]

    work = df.sort_values(DATE_COL).reset_index(drop=True)
    X = work[features].copy()
    X = X.replace([np.inf, -np.inf], np.nan)
    valid_mask = X.notna().all(axis=1)
    X_valid = X[valid_mask]

    # Isolation Forest needs a reasonable number of samples to fit meaningfully;
    # guard against tiny date-range selections (e.g. a single day) where fitting
    # would be meaningless or scikit-learn would raise.
    if len(X_valid) < 10:
        return pd.DataFrame(columns=["date", "anomaly_score", "method", "explanation"])

    model = IsolationForest(contamination=contamination, random_state=random_state, n_estimators=200)
    model.fit(X_valid)
    scores = model.decision_function(X_valid)  # higher = more normal
    predictions = model.predict(X_valid)  # -1 = anomaly, 1 = normal

    result_idx = X_valid.index[predictions == -1]

    # Feature-level z-scores (whole-sample) to give a human-readable "why"
    means = X_valid.mean()
    stds = X_valid.std().replace(0, np.nan)

    records = []
    for idx in result_idx:
        row_z = ((X_valid.loc[idx] - means) / stds).abs().sort_values(ascending=False)
        top_features = row_z.head(2)
        explanation = "; ".join(
            f"{feat} unusually {'high' if (X_valid.loc[idx, feat] - means[feat]) > 0 else 'low'} "
            f"(z={row_z[feat]:.1f})"
            for feat in top_features.index
        )
        records.append({
            "date": work.loc[idx, DATE_COL],
            "anomaly_score": round(scores[X_valid.index.get_loc(idx)], 4),
            "method": "Isolation Forest",
            "explanation": explanation,
        })

    if not records:
        return pd.DataFrame(columns=["date", "anomaly_score", "method", "explanation"])

    result = pd.DataFrame(records).sort_values("anomaly_score")
    return result.reset_index(drop=True)


def run_anomaly_detection(df: pd.DataFrame) -> dict:
    """Run both anomaly-detection methods and return their results."""
    return {
        "rolling_zscore": rolling_zscore_anomalies(df),
        "isolation_forest": isolation_forest_anomalies(df),
    }
