# 08 — Limitations

This project analyzes a **public, aggregate, daily** dataset. The following limitations apply
to every KPI, insight, bottleneck period, and anomaly reported anywhere in this repository.

## Data-Level Limitations

- **The data is aggregate, not individual-level.** Every figure is a same-day system-wide
  count. Nothing in this dataset ties a specific outcome to a specific child.
- **Individual processing times cannot be calculated.** There is no way to know, from this
  data, how long any particular child spent in CBP custody or HHS care.
- **Individual child outcomes cannot be inferred.** KPIs like Discharge Effectiveness describe
  the aggregate relationship between two daily counts — never an individual child's
  probability of discharge, placement type, or outcome.
- **Sponsor-level performance cannot be evaluated.** The dataset has no sponsor identifiers or
  sponsor-level breakdowns.
- **Shelter-level performance cannot be evaluated.** The dataset has no facility or
  shelter-level breakdowns.
- **Geographic bottlenecks cannot be determined.** There is no location field in this dataset;
  all figures are national aggregates.
- **The reporting cadence is not a strict daily cadence.** Friday and Saturday are almost
  entirely absent from the reported dates (see `03_EDA_Findings.md`). Any calculation that
  assumes strictly consecutive calendar days (e.g. "7 consecutive days") in this project
  actually means 7 consecutive *reported* days, which may span more than 7 calendar days.

## Methodological Limitations

- **Causal conclusions cannot be drawn from these aggregate observations alone.** Strong
  correlations reported in `03_EDA_Findings.md` (e.g. CBP custody vs. transfers, r = 0.925)
  describe co-movement of same-day aggregate counts, not a verified causal or cohort-tracked
  relationship.
- **No true end-to-end throughput metric is defined**, deliberately — see
  `04_KPI_Definitions.md` for why combining apprehensions with a later stage's same-day flow
  would misrepresent the pipeline as tracking a single cohort.
- **All bottleneck thresholds are project-defined**, not official CBP/HHS operational
  standards. They were calibrated to this dataset's own observed distributions (documented in
  `05_Bottleneck_Analysis.md`) specifically so they would be meaningful for *this* dataset —
  they should be re-evaluated, not assumed, if applied to a different or updated dataset.
- **The Outcome Stability Score is project-defined**, a simple 0–100 normalization of
  coefficient of variation. It is not validated against any external stability standard and
  should not be treated as a certified performance grade.
- **Anomaly detection identifies statistically unusual observations, not confirmed
  failures.** A flagged date may reflect a genuine operational event, a reporting correction,
  a holiday effect, or simple natural variation — this project cannot distinguish between
  these without additional context.
- **Trend classification is a transparent rule, not a forecast.** `classify_trend()`
  describes the historical shape of a window; it does not predict future behavior, and (as
  shown concretely in `07_Results.md`) can disagree with a naive endpoint-based percent
  change on a noisy or non-monotonic window.
- **Rolling averages with `min_periods=1`** mean the very first few rows of any rolling-window
  chart are based on fewer observations than the nominal window size, and are therefore less
  smoothed/reliable than later points in the same series.
- **Weekday comparisons are effectively Sunday-through-Thursday comparisons** in this dataset,
  given how rarely Friday and Saturday are reported (see `03_EDA_Findings.md`).

## Scope Limitations

- This project covers the period 2023-01-12 through 2025-12-21 only, as present in the
  provided CSV. It does not incorporate any data before or after this range.
- This is an internship-level analytics project intended to demonstrate a complete,
  reproducible data-science workflow (validation → cleaning → EDA → feature engineering →
  KPIs → bottleneck/anomaly detection → dashboard → documentation). It is **not** a policy
  evaluation, an audit, or an official assessment of program performance, and should not be
  cited as such.
