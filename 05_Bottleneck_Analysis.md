# 05 — Bottleneck Analysis

## Methodology

`src/bottleneck_detection.py` implements a transparent, rule-based detector. For a chosen
metric and threshold, it walks the chronologically sorted daily records and finds contiguous
runs of days where the metric stays below (or, for accumulation, above zero) the threshold.
A run is only reported as a "bottleneck period" if its length is at least `min_days`
(default 7, configurable in the dashboard sidebar).

For each detected period, the following is reported:

- **Start date / End date**
- **Duration** (days)
- **Metric** and its **average value** during the period
- **Threshold** used
- **Severity** — a project-defined bucket based on how far below threshold the period's
  average fell: `High` if the average is ≥50% below threshold, `Medium` if ≥20% below,
  `Low` otherwise.

Three detectors are run:

1. **Transfer bottleneck** — sustained `transfer_efficiency < transfer_threshold`
   (default 60%, project-defined).
2. **Discharge bottleneck** — sustained `discharge_effectiveness < discharge_threshold`
   (default 1.0%, calibrated to this dataset's own distribution — see `04_KPI_Definitions.md`
   for why a generic 20% would be meaningless here).
3. **Sustained accumulation** — sustained `net_flow_pressure > 0` (more apprehensions than
   discharges for `min_days` or more consecutive reported days).

**All thresholds are PROJECT-DEFINED ANALYTICAL THRESHOLDS. They are NOT official CBP or HHS
operational thresholds**, and crossing one does not, by itself, prove an operational failure
or its cause — it flags a period worth further investigation by someone with access to more
granular (non-public) data.

## Results on the Full Dataset (default thresholds)

Using the default thresholds (Transfer Efficiency < 60%, Discharge Effectiveness < 1.0%,
minimum 7 sustained days):

### Transfer Bottlenecks — 9 periods detected

| Start | End | Duration (days) | Avg. Transfer Efficiency | Severity |
|---|---|---|---|---|
| 2025-04-27 | 2025-05-07 | 9 | 40.7% | Medium |
| 2025-06-10 | 2025-06-25 | 7 | 31.0% | Medium |
| 2025-06-29 | 2025-07-14 | 11 | 30.8% | Medium |
| 2025-07-16 | 2025-07-30 | 10 | 25.1% | High |
| 2025-08-03 | 2025-08-25 | 17 | 27.1% | High |
| 2025-08-27 | 2025-09-10 | 10 | 31.6% | Medium |
| 2025-09-17 | 2025-10-22 | 25 | 33.5% | Medium |
| 2025-11-02 | 2025-11-12 | 8 | 27.3% | High |
| 2025-11-16 | 2025-12-18 | 24 | 24.5% | High |

**Observation:** Every detected transfer-bottleneck period falls within 2025, and the periods
become both longer and more frequent from mid-2025 onward, with the two longest (25 and 24
days) both occurring in the final quarter of the observed data (Sep–Dec 2025).

### Discharge Bottlenecks — 3 periods detected

| Start | End | Duration (days) | Avg. Discharge Effectiveness | Severity |
|---|---|---|---|---|
| 2025-03-11 | 2025-06-25 | 70 | 0.43% | High |
| 2025-07-27 | 2025-08-20 | 19 | 0.59% | Medium |
| 2025-08-24 | 2025-12-21 | 82 | 0.47% | High |

**Observation:** The final detected discharge-bottleneck period (82 days, Aug 24 – Dec 21,
2025) runs to the very last reported date in the dataset, meaning discharge effectiveness was
still below the project-defined threshold as of the most recent available data.

### Sustained Accumulation — 0 periods detected

No period of 7+ consecutive days with positive Net Flow Pressure was found at default
settings — the longest such streak observed was 5 consecutive reported days (see
`07_Results.md`).

## Interpreting These Results

These periods indicate that, under the project's chosen definitions, aggregate transfer and
discharge indicators were below the chosen thresholds for extended stretches, concentrated in
2025. They do **not** indicate why — that would require operational data (staffing, shelter
capacity, sponsor availability, legal/case processing status) that is not present in this
public aggregate dataset. See `08_Limitations.md`.
