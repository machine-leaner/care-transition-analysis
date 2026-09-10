# 03 — EDA Findings

Full working notebook: `notebooks/01_EDA.ipynb`. This document summarizes the findings in
prose for the internship report.

## Data Quality Summary

| Check | Result |
|---|---|
| Raw file shape | 1,170 rows × 6 columns |
| Fully-blank trailing rows | 450 (dropped as a CSV export artifact) |
| Clean dataset shape | 720 rows × 6 columns |
| Duplicate rows (post-cleaning) | 0 |
| Duplicate dates (post-cleaning) | 0 |
| Negative values in any numeric column | 0 |
| Missing values in any numeric column (post-cleaning) | 0 |
| Date range | 2023-01-12 to 2025-12-21 |

## Reporting Cadence (Date Continuity)

The full calendar span (2023-01-12 to 2025-12-21) covers 1,075 calendar days. Only 720 of
those days (67%) have a reported record. Breaking down the **720 reported days** by weekday:

| Weekday | Reported days |
|---|---|
| Tuesday | 149 |
| Thursday | 147 |
| Wednesday | 147 |
| Monday | 145 |
| Sunday | 130 |
| **Friday** | **2** |
| **Saturday** | **0** |

And the **355 missing calendar days**, by weekday:

| Weekday | Missing days |
|---|---|
| Saturday | 154 |
| Friday | 152 |
| Sunday | 24 |
| Monday | 8 |
| Thursday | 7 |
| Wednesday | 6 |
| Tuesday | 4 |

**Finding:** The program's own reporting cadence excludes Friday and Saturday almost
completely — together they account for 306 of the 355 missing days (86%). The remaining 49
missing days spread across Sunday–Thursday most plausibly correspond to federal holidays or
occasional reporting pauses. This is treated throughout the project as a **structural
characteristic of the source data**, not a defect to be corrected: no forward-filling or
interpolation is applied to manufacture values for non-reporting days.

## Distributional Findings

| Column | Mean | Std Dev | Min | Max | Coefficient of Variation |
|---|---|---|---|---|---|
| Apprehensions | 93.5 | — | 0 | 333 | 0.78 |
| CBP Custody | 171.5 | — | — | 531 | 0.74 |
| Transfers | 128.7 | — | 0 | 440 | 0.76 |
| HHS Care | 6,061.3 | — | — | 11,516 | 0.47 |
| Discharges | 173.4 | — | 0 | 505 | 0.72 |

**Finding:** `hhs_care` operates on a fundamentally different scale from the other four
columns — it is a **population stock** (children currently in care on a given day, in the
thousands) rather than a **daily flow** (apprehensions/transfers/discharges, typically in the
tens to low hundreds). This has a direct and important consequence for KPI design: Discharge
Effectiveness (discharges ÷ HHS care × 100) is structurally a small percentage (see
`04_KPI_Definitions.md`), and project-defined bottleneck thresholds for that KPI had to be
calibrated to this dataset's actual scale rather than borrowed from a generic percentage
range (the default was set relative to this dataset's own distribution, not to 20% as an
arbitrary round number would suggest).

`hhs_care` also has the lowest relative variability (CV = 0.47) of the five columns, meaning
the population-in-care figure is comparatively more stable day-to-day than the daily flow
counts, which is expected for a large stock relative to smaller daily flows in and out of it.

## Relationships Between Variables

Pearson correlation matrix (all five flow columns):

|  | apprehensions | cbp_custody | transfers | hhs_care | discharges |
|---|---|---|---|---|---|
| apprehensions | 1.00 | 0.95 | 0.89 | 0.69 | 0.63 |
| cbp_custody | 0.95 | 1.00 | 0.93 | 0.66 | 0.60 |
| transfers | 0.89 | 0.93 | 1.00 | 0.71 | 0.66 |
| hhs_care | 0.69 | 0.66 | 0.71 | 1.00 | 0.92 |
| discharges | 0.63 | 0.60 | 0.66 | 0.92 | 1.00 |

Requested pairwise relationships specifically:

- **CBP custody vs. Transfers:** Pearson r = 0.925 (p < 0.001), Spearman ρ = 0.886 (p < 0.001), n = 720.
  Strong positive relationship — days with more children in CBP custody tend to also have more
  transfers out of CBP custody that same day.
- **HHS care vs. Discharges:** Pearson r = 0.921 (p < 0.001), Spearman ρ = 0.895 (p < 0.001), n = 720.
  Strong positive relationship — a larger population in HHS care is associated with a larger
  daily discharge count, consistent with discharges scaling with the size of the population
  being served.
- **Apprehensions vs. Transfers:** Pearson r = 0.888 (p < 0.001), Spearman ρ = 0.865 (p < 0.001), n = 720.
  Strong positive relationship between same-day apprehensions and transfers.

**Important caveat:** These are same-day aggregate correlations, not matched-cohort or
lagged-cohort relationships. A strong positive correlation between, e.g., apprehensions and
transfers on the *same day* does not mean the children apprehended that day are the same
children transferred that day (transfers on a given day plausibly include children
apprehended on previous days). Correlation here describes co-movement of aggregate daily
volumes, not a tracked causal chain — see `08_Limitations.md`.

## Weekday Patterns

Because Friday/Saturday reporting is nearly absent, weekday comparisons in this project
functionally compare Sunday through Thursday. See `notebooks/01_EDA.ipynb` §7 and the
dashboard's Temporal Analysis page for the full weekday breakdown of Transfer Efficiency and
Discharge Effectiveness.

## Summary of Key EDA Takeaways

1. The raw file's 450 blank rows are a formatting artifact; the true dataset is 720 clean
   daily records spanning just under 3 years.
2. The program does not report on a strict daily cadence — Friday and Saturday are almost
   entirely absent — and this shapes how "missing data" should be interpreted throughout the
   rest of the analysis.
3. No negative values, impossible percentages, or duplicate records were found.
4. `hhs_care` is a population stock roughly 35–60× larger than the daily flow columns, which
   materially affects the scale (and therefore the sensible threshold range) of any KPI that
   divides a flow by `hhs_care`.
5. The pipeline stages show strong, statistically significant positive correlations with each
   other in aggregate, consistent with (but not proof of) a connected multi-stage operational
   process.
