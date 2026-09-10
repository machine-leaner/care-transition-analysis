# Care Transition Efficiency & Placement Outcome Analytics

An internship-level data analytics / data science project analyzing the HHS Unaccompanied
Alien Children (UAC) Program's public daily aggregate data as an operational flow:

```
CBP Apprehension/Custody → CBP → HHS Transfer → HHS Care → Discharge / Sponsor Placement
```

This is a data-quality-first, statistically grounded analytics system — not a hackathon demo.
It prioritizes correct methodology, reproducibility, and honest documentation of what the
data can and cannot support over flashy UI or unnecessary AI features.

---

## 1. Project Overview

The system is a full pipeline: raw CSV → validation → cleaning → feature engineering →
statistical/temporal analysis → KPI development → rule-based bottleneck detection →
two-method anomaly detection → an interactive Streamlit dashboard → an EDA notebook →
automated tests → internship-report-style documentation (this file and `docs/`).

## 2. Problem Statement

See `docs/01_Problem_Statement.md`. In short: aggregate daily counts alone don't answer
operational questions like *where*, *when*, and *whether improving or declining* — this
project builds the analytics to answer those questions, transparently and reproducibly,
without overstating what aggregate public data can support.

## 3. Objectives

1. Understand aggregate transfer efficiency and discharge effectiveness.
2. Track changes in system load (population in custody / in care).
3. Identify potential backlog accumulation.
4. Surface temporal patterns (daily, weekly, monthly).
5. Detect sustained bottleneck periods using transparent, configurable rules.
6. Flag unusual observations using two independent anomaly-detection methods.
7. Assess the stability of discharge performance over time.

## 4. Dataset

`data/raw/HHS_Unaccompanied_Alien_Children_Program.csv` — the HHS UAC Program's public daily
report, covering **2023-01-12 to 2025-12-21** (720 valid daily records after cleaning; see
§14 and `docs/03_EDA_Findings.md` for the full data-quality writeup).

## 5. Data Dictionary

| Raw column | Canonical column (`src/config.py`) | Meaning |
|---|---|---|
| `Date` | `date` | Reported date |
| `Children apprehended and placed in CBP custody*` | `apprehensions` | Children apprehended and placed in CBP custody that day |
| `Children in CBP custody` | `cbp_custody` | Children in CBP custody on that day |
| `Children transferred out of CBP custody` | `transfers` | Children transferred out of CBP custody that day |
| `Children in HHS Care` | `hhs_care` | Children in HHS Care on that day (population stock; comma-formatted in the raw file, e.g. `"2,484"`) |
| `Children discharged from HHS Care` | `discharges` | Children discharged from HHS Care that day |

Feature-engineered columns (added by `src/feature_engineering.py`): `Year`, `Month`,
`Month_Name`, `Week`, `Weekday`, `Day_of_Week`, `Quarter`, the seven KPI columns (§8), and
`*_roll7` / `*_roll14` / `*_roll30` rolling averages. Full reference also in the dashboard's
Data Explorer page.

## 6. Data Preprocessing

See `docs/02_Methodology.md` for the full write-up. Key steps (`src/preprocessing.py`):
rename raw headers to canonical names → drop 450 fully-blank artifact rows → parse dates →
convert numeric columns (handling comma-formatted `hhs_care` values) → validate ranges
(negatives, nulls) → deduplicate → sort chronologically.

## 7. EDA Methodology

`notebooks/01_EDA.ipynb` performs initial inspection, distribution analysis, time-trend
visualization, and correlation analysis, all using the shared `src/` modules (no duplicated
logic). Findings are written up in `docs/03_EDA_Findings.md`.

## 8. KPI Formulas

Full definitions and interpretation notes in `docs/04_KPI_Definitions.md`. Summary:

| KPI | Formula |
|---|---|
| Transfer Efficiency | Transfers / CBP Custody × 100 |
| Discharge Effectiveness | Discharges / HHS Care × 100 |
| CBP Transfer Rate | Transfers / Apprehensions × 100 |
| Net Flow Pressure | Apprehensions − Discharges |
| Cumulative Net Flow Pressure | Running cumulative sum of Net Flow Pressure |
| CBP Transfer Gap | CBP Custody − Transfers |
| HHS Discharge Gap | HHS Care − Discharges |
| Outcome Stability Score (project-defined, 0–100) | `100 × (1 − clip(CV, 0, 1))` on Discharge Effectiveness |

All ratio KPIs return `NaN` (never `0`/`inf`) on a zero denominator.

## 9. Statistical Methodology

Descriptive statistics, Pearson/Spearman correlation, month-over-month change, weekday
comparison, and OLS-slope-based trend classification — see `docs/02_Methodology.md` and
`src/analysis.py`. Correlation is never presented as causation.

## 10. Bottleneck Methodology

Transparent, rule-based, configurable sustained-period detection — see
`docs/05_Bottleneck_Analysis.md` and `src/bottleneck_detection.py`. All thresholds are
project-defined and adjustable in the dashboard sidebar.

## 11. Anomaly Detection Methodology

Rolling Z-Score (statistical) + Isolation Forest (machine learning), run independently for
methodological comparison — see `docs/06_Anomaly_Analysis.md` and `src/anomaly_detection.py`.

## 12. Dashboard Description

A 9-page Streamlit dashboard (`app.py` + `pages/`), sharing global filters (date range,
rolling window, bottleneck thresholds, anomaly toggle) via `dashboard_common.py`:

1. **Executive Summary** — current KPI snapshot, trends, dynamically generated key findings.
2. **Data Quality** — missing values, duplicates, date continuity, validation results.
3. **Pipeline Analysis** — the full flow visualized, including a Sankey of period totals.
4. **Transfer Analysis** — Transfer Efficiency, CBP Transfer Rate, rolling averages, trend.
5. **Discharge Analysis** — Discharge Effectiveness, variability, Outcome Stability Score.
6. **Bottleneck Analysis** — detected periods, thresholds, duration, severity, accumulation.
7. **Temporal Analysis** — weekday patterns, monthly trends, month-over-month change.
8. **Anomaly Analysis** — both detection methods, flagged dates, explanations.
9. **Data Explorer** — column filtering, dataset preview, CSV download.

## 13. Results / Insights

See `docs/07_Results.md` for the full write-up (all figures generated dynamically, never
hard-coded). Headline: transfer efficiency recovered sharply in the most recent 30 reported
days (+124%) while discharge effectiveness softened (−32.8%) over the same window; 9
transfer-bottleneck and 3 discharge-bottleneck periods were identified in 2025 at default
thresholds, with the most recent discharge-bottleneck period still open as of the last
reported date.

## 14. Limitations

See `docs/08_Limitations.md`. In short: this is aggregate, public, daily data. It cannot
support individual-level, sponsor-level, shelter-level, or geographic conclusions, and
correlational findings should never be read as causal.

## 15. Future Work

See `docs/09_Future_Work.md`: individual-level case data, processing-time and survival
analysis, geographic/shelter-level analysis, forecasting, resource optimization, causal
inference, real-time monitoring, and more advanced time-series models.

## 16. Installation

```bash
git clone <this-repo>
cd uac-analytics
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Requires Python 3.10+.

## 17. Running Instructions

**Run the data pipeline** (raw → processed CSVs in `data/processed/`):
```bash
python run_pipeline.py
```

**Run the EDA notebook:**
```bash
jupyter notebook notebooks/01_EDA.ipynb
```

**Run the dashboard:**
```bash
streamlit run app.py
```
Then open the printed local URL (default `http://localhost:8501`) in a browser. All 9 pages
are listed in the sidebar navigation.

## 18. Testing Instructions

```bash
pytest
```

62 tests across `tests/` cover: data loading, comma-removal and numeric conversion, date
parsing, blank-row and duplicate handling, all 7 KPI formulas (including zero-denominator
handling), rolling-window calculations, calendar feature engineering, bottleneck detection
(short dips vs. sustained periods, multiple periods, end-of-data runs), anomaly detection
(both methods, including edge cases with missing values), statistical analysis (trend
classification, stability score, weekday/monthly aggregation), and insight generation
(verifying insights change when the underlying data changes, i.e. are not hard-coded).

Run with coverage:
```bash
pytest --cov=src --cov-report=term-missing
```

---

## Project Structure

```
uac-analytics/
├── app.py                        # Streamlit entry point (Page 1: Executive Summary)
├── dashboard_common.py           # Shared caching, sidebar filters, formatting helpers
├── run_pipeline.py               # CLI: raw -> processed pipeline runner
├── requirements.txt
├── README.md
├── .streamlit/config.toml        # Dashboard theme
├── data/
│   ├── raw/                      # Original CSV, never overwritten
│   └── processed/                # Generated by run_pipeline.py
├── src/
│   ├── config.py                 # Column mappings, thresholds, constants
│   ├── data_loader.py
│   ├── preprocessing.py
│   ├── feature_engineering.py
│   ├── metrics.py                # 7 KPI formulas
│   ├── analysis.py                # Descriptive/correlation/temporal/trend/stability
│   ├── bottleneck_detection.py
│   ├── anomaly_detection.py
│   ├── visualizations.py         # Shared Plotly chart builders
│   └── insights.py                # Dynamic, evidence-based text findings
├── pages/                        # Dashboard pages 2-9 (Streamlit auto-discovery)
├── notebooks/
│   └── 01_EDA.ipynb
├── tests/                        # 62 pytest tests
└── docs/                         # Internship report (01-09)
```

## A Note on Interpretation

Every KPI, threshold, score, and classification in this project is either a straightforward
arithmetic aggregate or an explicitly labeled **project-defined** analytical construct. None
of it is an official CBP/HHS metric, benchmark, or certification. Please read
`docs/08_Limitations.md` before drawing conclusions from any figure in this repository.
