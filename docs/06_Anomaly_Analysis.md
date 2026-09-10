# 06 — Anomaly Analysis

## Methodology

Two methodologically independent anomaly-detection approaches are implemented in
`src/anomaly_detection.py`, so results can be cross-checked rather than relying on a single
technique:

### 1. Rolling Z-Score (statistical)

For each chosen column, a trailing 14-day rolling mean and standard deviation are computed
(`min_periods=5`), and any day where the value deviates more than 3 standard deviations from
its own trailing rolling mean is flagged. This method looks at **one metric at a time**,
relative to its own recent history.

### 2. Isolation Forest (machine learning)

A scikit-learn `IsolationForest` (`contamination=0.03`, 200 trees, `random_state=42`) is fit
across eight features simultaneously: the five flow columns plus `transfer_efficiency`,
`discharge_effectiveness`, and `net_flow_pressure`. This method can catch **multivariate**
outliers — a day that looks unremarkable on any single metric but unusual in *combination*.
For interpretability, each flagged day is annotated with its two most extreme features (by
whole-sample z-score) and their direction (unusually high/low).

Isolation Forest requires a reasonable sample size to fit meaningfully; if a dashboard filter
narrows the date range to fewer than 10 valid rows, the function returns an empty result
rather than fitting on too little data or raising an error.

**Neither method proves an operational failure, data-entry error, or confirmed anomaly in the
underlying program — both only identify observations that are statistically unusual relative
to the rest of the dataset (or, for Isolation Forest, relative to the rest of the selected
feature space).**

## Results on the Full Dataset

### Rolling Z-Score — 2 distinct dates flagged (3 metric-level flags)

| Date | Column | Value | 14-day Rolling Mean | Z-Score |
|---|---|---|---|---|
| 2023-02-08 | apprehensions | 93 | 30.2 | +3.06 |
| 2023-02-08 | transfers | 169 | 38.7 | +3.33 |
| 2023-05-21 | hhs_care | 7,826 | 8,545.6 | −3.16 |

**Observation:** 2023-02-08 shows a simultaneous spike in both apprehensions and transfers,
flagged independently by the single-metric method on both columns — itself a hint that a
multivariate method might also flag this day (see below).

### Isolation Forest — 22 dates flagged (contamination = 3% of 720 days)

The five most extreme (lowest anomaly score = most unusual) dates:

| Date | Anomaly Score | Explanation |
|---|---|---|
| 2024-01-11 | −0.099 | net_flow_pressure unusually low (z=3.7); discharges unusually high (z=2.4) |
| 2023-01-12 | −0.067 | net_flow_pressure unusually low (z=3.3); discharge_effectiveness unusually high (z=3.2) |
| 2023-10-01 | −0.044 | net_flow_pressure unusually low (z=3.4); discharges unusually high (z=2.5) |
| 2023-08-31 | −0.038 | net_flow_pressure unusually low (z=3.2); discharges unusually high (z=2.6) |
| 2025-02-02 | −0.037 | transfer_efficiency unusually high (z=3.8); discharge_effectiveness unusually high (z=1.8) |

The full ranked list of 22 flagged dates is available in the dashboard's Anomaly Analysis
page and reproducible via `src.anomaly_detection.isolation_forest_anomalies()`.

## Methodological Comparison

- 2023-02-08, flagged by the z-score method for apprehensions/transfers, does **not** appear
  in the Isolation Forest top-5 shown above (though it may appear further down the full
  22-date list) — a reminder that the two methods weight "unusualness" differently: z-score
  reacts to a single metric's deviation from its own recent trend, while Isolation Forest
  reacts to the overall unusualness of the day's full feature combination relative to the
  whole 3-year sample, not just a 14-day local window.
- Several Isolation Forest hits (2023-01-12, 2023-08-31, 2023-10-01, 2024-01-11) share a
  common pattern: unusually low net flow pressure paired with unusually high discharges —
  i.e., days where discharge activity spiked well above its typical level relative to that
  day's apprehensions.
- Agreement between the two methods on a given date increases confidence that the date is
  genuinely unusual; disagreement is expected given their different mechanics and does not
  mean either method is "wrong."

See the dashboard's Anomaly Analysis page (Page 8) for interactive exploration, including the
option to toggle anomaly detection on/off and inspect any flagged date against the underlying
time series.
