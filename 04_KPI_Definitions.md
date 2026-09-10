# 04 — KPI Definitions

All formulas are implemented in `src/metrics.py`. Every ratio-based KPI returns `NaN` (never
`0` or `±inf`) when its denominator is zero, via a shared `_safe_ratio()` helper.

None of the KPIs below are official HHS/CBP performance metrics. They are project-defined
analytical indicators computed from the public aggregate daily counts, designed to surface
patterns for further investigation — not to certify program performance.

---

### KPI 1 — Transfer Efficiency

```
Transfer Efficiency = Transfers / CBP Custody × 100
```

**Interpretation:** An aggregate indicator of same-day transfers out of CBP custody relative
to the CBP custody population on that day.

**What it is NOT:** A direct measurement of individual processing speed. It says nothing
about how long any specific child spent in CBP custody.

---

### KPI 2 — Discharge Effectiveness

```
Discharge Effectiveness = Discharges / HHS Care × 100
```

**Interpretation:** An aggregate indicator of same-day discharge volume relative to the HHS
care population on that day.

**What it is NOT:** An individual child's probability of being discharged. Because `HHS Care`
is a population stock roughly 35–60× larger than daily `Discharges` (see
`03_EDA_Findings.md`), this KPI is structurally a small percentage (observed median ≈ 2.6% in
this dataset) — a value of "3%" here does not mean 3% of children are being discharged in
some cohort sense; it means that day's discharges were about 3% the size of that day's total
population in care.

---

### KPI 3 — CBP Transfer Rate

```
CBP Transfer Rate = Transfers / Apprehensions × 100
```

**Interpretation:** A flow-based complementary metric relating same-day transfers to same-day
apprehensions.

**Caveat:** Because these are same-day aggregate counts rather than matched-cohort figures,
values can exceed 100% (more transfers on a day than apprehensions that same day, since
transfers can include children apprehended on earlier days). Read this as a flow-balance
indicator, not a completion rate for a specific cohort.

---

### KPI 4 — Net Flow Pressure

```
Net Flow Pressure = Apprehensions − Discharges
```

**Interpretation:** An aggregate inflow/outflow pressure indicator. Positive values indicate
more children entering the system (via apprehension) than exiting it (via discharge) on that
day; negative values indicate the reverse.

---

### KPI 5 — Cumulative Net Flow Pressure

```
Cumulative Net Flow Pressure = running cumulative sum of daily Net Flow Pressure
```

**Interpretation:** Used to identify sustained accumulation or drawdown trends across the
full observed period, rather than reacting to single-day noise.

---

### KPI 6 — CBP Transfer Gap

```
CBP Transfer Gap = CBP Custody − Transfers
```

---

### KPI 7 — HHS Discharge Gap

```
HHS Discharge Gap = HHS Care − Discharges
```

---

## Deliberately NOT Defined: A Single "End-to-End Throughput" Metric

This project does **not** define `(Transfers + Discharges) / Apprehensions` (or any similar
combination) as a true end-to-end pipeline throughput metric. The dataset contains different
stages of the process measured as independent daily aggregate counts, not a tracked cohort of
individual children followed from apprehension through discharge. A metric combining
apprehensions with a later stage's flow on the same calendar day would conflate children from
different entry cohorts and imply a precision the data does not support. Instead, this project
reports the three flow-based ratios above (Transfer Efficiency, CBP Transfer Rate, Discharge
Effectiveness) and Net Flow Pressure, each scoped to a single stage transition, and documents
this limitation explicitly rather than presenting a misleading composite.

---

## Outcome Stability Score (project-defined, 0–100)

```
cv = std(discharge_effectiveness) / mean(discharge_effectiveness)  [over the selected period]
cv_clipped = clip(cv, 0, 1.0)
Outcome Stability Score = 100 × (1 − cv_clipped)
```

A score of 100 means discharge effectiveness was perfectly consistent (zero variation) over
the selected period; a score of 0 means its standard deviation was as large as, or larger
than, its mean (highly inconsistent). This is a project-defined normalization for this
project only — it is **not** an official government KPI, star rating, or grade.

## Bottleneck Thresholds (project-defined, configurable)

See `05_Bottleneck_Analysis.md`. Default values live in `src/config.py` and are adjustable in
the dashboard sidebar. They are calibrated to this dataset's observed distributions (see
`03_EDA_Findings.md`), not to an external or official standard.
