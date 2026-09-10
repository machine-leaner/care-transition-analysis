# 02 — Methodology

## Pipeline Architecture

```
Raw CSV (data/raw/, preserved unmodified)
   ↓
src/data_loader.py        — read raw CSV as-is; lightweight inspection helper
   ↓
src/preprocessing.py      — validate, clean, transform
   ↓
src/feature_engineering.py — calendar features, KPIs, rolling averages
   ↓
data/processed/ (generated, never hand-edited)
   ↓
src/analysis.py            — descriptive stats, correlation, temporal, trend, stability
src/bottleneck_detection.py — rule-based sustained-period detection
src/anomaly_detection.py    — rolling z-score + Isolation Forest
   ↓
src/visualizations.py       — shared Plotly chart builders
src/insights.py              — dynamically generated, evidence-based text findings
   ↓
notebooks/01_EDA.ipynb  (exploratory)      app.py + pages/ (Streamlit dashboard)
```

Each `src/` module has a single responsibility, is independently unit-tested (`tests/`), and
contains no hard-coded results — every number produced anywhere in the system is computed from
the dataset at run time.

## Data Cleaning Decisions

| Issue | Decision | Rationale |
|---|---|---|
| 450 fully-blank trailing rows in raw CSV | Dropped entirely | Confirmed to be a CSV export artifact (every column null), not real missing observations |
| `Children in HHS Care` comma-formatted strings (e.g. `"2,484"`) | Stripped and converted to numeric | Necessary for any numeric analysis; done unconditionally on the string form to be robust to dtype differences across pandas versions |
| Dates as `"Month DD, YYYY"` strings | Parsed to `datetime64` | Required for time-series operations |
| Reporting cadence skips Friday/Saturday almost entirely | Left as-is (no interpolation or forward-fill) | This is a structural characteristic of how the program reports, not a defect; fabricating values for non-reporting days would misrepresent the data |
| Negative values / impossible percentages | Checked for, none found in this dataset | Reported via `validate_numeric_ranges()`, not silently removed — the function only counts and flags, so a future dataset revision with negatives would be caught, not masked |

## KPI Methodology

See `04_KPI_Definitions.md` for full formulas. All ratio KPIs use a shared `_safe_ratio()`
helper (`src/metrics.py`) that returns `NaN` — never `0` or `inf` — when the denominator is
zero, so a single day with zero CBP custody, zero apprehensions, or zero HHS care never
silently corrupts a rolling average or trend calculation.

## Rolling Averages

7/14/30-day rolling averages use `min_periods=1`, so early rows in the series produce a
partial-window average rather than `NaN`. This is a deliberate choice to keep the full date
range usable in charts and KPI cards, at the cost of the first few days' rolling values being
based on fewer observations than the nominal window — this trade-off is documented here and
should be kept in mind when interpreting the very start of any rolling-average chart.

## Trend Classification

`src/analysis.classify_trend()` fits an ordinary-least-squares regression line to a metric
over a specified window, converts the projected total change over that window to a percentage
of the window's mean value, and classifies the result as:

- **Stable** — |percent change| < 2% (default `flat_threshold_pct`)
- **Increasing** — percent change ≥ +2%
- **Decreasing** — percent change ≤ −2%

This is a transparent, reproducible rule rather than a subjective judgment call, and the
2% flat-band threshold is explicitly a project-defined default (adjustable via the function
argument). The function reports raw direction only — callers (e.g. the dashboard) apply their
own interpretation of whether an increase is desirable for a given metric.

**Important methodological note:** `classify_trend()`'s OLS-slope-based direction and the
simple start-vs-end percent change shown in generated insights (`src/insights.py`) are
deliberately different calculations and can disagree, particularly over longer or noisier
windows. The regression slope reflects the overall shape of the whole window (more robust to
which specific two days happen to sit at the endpoints); the endpoint percent change is more
intuitive but sensitive to noise on exactly the first/last reported day. Both are reported
because both are useful, but they answer subtly different questions ("what was the general
direction across the window" vs. "how did the last reported day compare to the first"), and
an analyst should not be surprised if they occasionally point in different directions on a
volatile metric — see `07_Results.md` for a concrete example from this dataset.

## Bottleneck Detection Methodology

See `05_Bottleneck_Analysis.md` for full detail. In summary: a boolean condition (e.g.
`transfer_efficiency < threshold`) is evaluated for every reported day in chronological order;
contiguous runs of `True` values lasting at least `min_days` are reported as a bottleneck
period, with start date, end date, duration, average value during the period, and a
project-defined severity bucket based on how far below threshold the period's average fell.

## Anomaly Detection Methodology

See `06_Anomaly_Analysis.md`. Two independent, methodologically distinct approaches are used
so results can be cross-checked against each other:

1. **Rolling Z-Score** (statistical): per-metric, compares each day's value to its own
   trailing rolling mean and standard deviation.
2. **Isolation Forest** (machine learning, scikit-learn): fits across multiple KPI and flow
   features simultaneously to catch multivariate outliers that no single-metric method would
   flag.

## Outcome Stability Score

A project-defined, 0–100 normalization of the coefficient of variation (CV) of Discharge
Effectiveness over the selected period:

```
cv = std(discharge_effectiveness) / mean(discharge_effectiveness)
cv_clipped = clip(cv, 0, 1.0)
score = 100 * (1 - cv_clipped)
```

A CV of 0 (perfectly consistent discharge effectiveness) maps to a score of 100; a CV at or
above 1.0 (standard deviation as large as or larger than the mean) maps to a score of 0. This
is explicitly **not** an official government KPI — see `04_KPI_Definitions.md`.

## Reproducibility

- `run_pipeline.py` runs the full Raw → Processed pipeline end-to-end from the command line.
- The Streamlit dashboard runs the identical pipeline functions (via `dashboard_common.py`,
  cached with `st.cache_data`) rather than reading a separately-maintained processed file, so
  the dashboard can never drift from the pipeline logic in `src/`.
- All thresholds, window sizes, and constants live in `src/config.py`, not scattered as magic
  numbers, so the full set of project-defined choices is auditable in one file.
