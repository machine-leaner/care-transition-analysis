# 07 — Results / Insights

All figures below are computed live by `src/insights.py` from the full processed dataset
(720 records, 2023-01-12 to 2025-12-21) and are reproduced automatically — not hand-typed —
anywhere they appear in the dashboard's Executive Summary page. This document is a snapshot
of those results at the time of writing.

## Headline Findings

- **Transfer efficiency increased by 124.1%** over the most recent 30 reported days, from
  27.3% to 61.1%.
- **Discharge effectiveness decreased by 32.8%** over the most recent 30 reported days, from
  0.8% to 0.6%.
- **CBP transfer rate increased by 22.2%** over the most recent 30 reported days, from 150.0%
  to 183.3%.
- **Positive net flow pressure persisted for 5 consecutive reported days** at its longest
  stretch across the full ~3-year dataset (below the 7-day threshold used to flag "sustained
  accumulation").
- **Cumulative net flow pressure across the full observed period is −57,516**, indicating an
  overall net drawdown (more cumulative discharges than apprehensions) relative to the start
  of the dataset, despite the 2025 discharge-bottleneck periods noted below.
- **9 potential CBP-to-HHS transfer bottleneck periods** were identified at default
  thresholds; the longest ran **25 days** (2025-09-17 to 2025-10-22).
- **3 potential HHS discharge bottleneck periods** were identified; the longest ran **82
  days** (2025-08-24 to 2025-12-21) — running to the very end of the available data.
- **Discharge effectiveness variability was higher in the second half of the observed period**
  (std = 1.2) than the first half (std = 0.8), indicating discharge performance became less
  consistent over time even as its mean level also shifted.
- The **Outcome Stability Score** for discharge effectiveness over the full period is
  **43.9 / 100** (project-defined; see `04_KPI_Definitions.md`) — indicating meaningfully
  inconsistent, not highly stable, discharge performance over the full ~3 years.
- The rolling z-score method flagged **2 distinct dates**; Isolation Forest flagged **22
  dates** as multivariate outliers (see `06_Anomaly_Analysis.md`).

## A Worked Example of the Trend-Classification Caveat

`docs/02_Methodology.md` notes that the OLS-slope-based `classify_trend()` direction and the
simple endpoint-based percent change can disagree. A concrete example from this dataset:
over the most recent **90** reported days, Transfer Efficiency's simple endpoint comparison
shows a **+158%** increase (23.7% → 61.1%), yet the OLS regression slope across that same
90-day window classifies the overall direction as **"Decreasing."** This is not a
contradiction — it means the 90-day window contains a broader down-trending shape (e.g. a
mid-window peak followed by decline) even though the specific first and last reported days
happen to show an increase. This is exactly why the dashboard surfaces both figures rather
than collapsing them into one summary number: an analyst relying on only the endpoint change
would miss the shape the regression captures, and vice versa.

## Reading These Results Together

The picture across mid-to-late 2025 is one of **sustained pressure on both sides of the
pipeline simultaneously**: multiple, lengthening Transfer Efficiency bottleneck periods
throughout 2025, culminating in a discharge-effectiveness bottleneck period that had not
resolved by the end of the observed data (Dec 21, 2025). At the same time, the most recent
30-day window shows Transfer Efficiency recovering sharply (+124%), suggesting the transfer
side of the pipeline was improving in the final weeks of the dataset even as discharge
effectiveness continued to soften over the same window (−32.8%).

**This project does not attempt to explain why** these patterns occurred — see
`08_Limitations.md` for what additional data would be required to investigate causes such as
shelter capacity, sponsor availability, staffing, or legal/case-processing constraints.
