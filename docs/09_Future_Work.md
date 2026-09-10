# 09 — Future Work

The current system is intentionally scoped to what public, aggregate, daily data can support
(see `08_Limitations.md`). The following directions would meaningfully extend the analysis,
given the right additional data or resources.

## 1. Individual-Level Case Data

If individual (de-identified) case-level records became available — apprehension timestamp,
transfer timestamp, HHS intake timestamp, discharge timestamp per child — this project's
aggregate "efficiency" and "effectiveness" indicators could be replaced with true cohort-based
processing-time metrics.

## 2. Processing-Time Analysis

With individual timestamps, actual time-in-custody and time-in-care distributions could be
computed directly (median, percentiles, tail behavior) instead of being inferred indirectly
from aggregate ratios.

## 3. Survival Analysis

Time-to-discharge could be modeled with survival analysis techniques (Kaplan-Meier curves,
Cox proportional hazards) to characterize discharge timing distributions and identify
covariates associated with longer stays, rather than the current aggregate-ratio approach.

## 4. Geographic Analysis

With facility or regional location data, this project's national-aggregate bottleneck and
anomaly detection could be repeated at a regional or facility level to identify localized
pressure points invisible in the national aggregate.

## 5. Shelter-Level Analysis

Facility-level data would allow the current discharge-effectiveness and stability metrics to
be computed per shelter, enabling comparison of relative consistency and throughput across
facilities.

## 6. Forecasting

Building on the current trend classification and rolling-average features, a proper
time-series forecasting model (e.g. SARIMA, Prophet, or a gradient-boosted model with
calendar features) could project near-term apprehension, custody, and care volumes, with
appropriate uncertainty intervals — something explicitly out of scope for this project's
descriptive/diagnostic analysis.

## 7. Resource Optimization

Combined with staffing, shelter-capacity, and sponsor-availability data (none of which is
present in the current dataset), this analysis could inform queueing or optimization models
for resource allocation across the pipeline stages.

## 8. Causal Inference with Appropriate Data

The correlational findings in this project (e.g. CBP custody vs. transfers) could be
investigated causally with quasi-experimental designs (e.g. difference-in-differences around
known policy changes, instrumental variables) if suitable exogenous variation and
individual/facility-level data were available.

## 9. Real-Time Monitoring

The current dashboard analyzes a static CSV snapshot. A production version could connect to a
live data feed, re-run the pipeline on a schedule, and add alerting when new bottleneck or
anomaly conditions are detected under the configured thresholds.

## 10. More Advanced Time-Series Models

Beyond the current OLS-slope trend classification and rolling averages, techniques such as
STL decomposition (trend/seasonal/residual), change-point detection (e.g. PELT, Bayesian
online change-point detection), or state-space models could provide a more rigorous
characterization of structural shifts in the series than the current transparent-but-simple
rule-based approach.
