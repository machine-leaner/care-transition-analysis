# 01 — Problem Statement

## Background

The U.S. Department of Health and Human Services (HHS) Office of Refugee Resettlement (ORR)
publishes daily aggregate figures describing the flow of unaccompanied alien children (UAC)
through the federal care pipeline:

```
CBP Apprehension / Custody
        ↓
CBP → HHS Transfer
        ↓
HHS Care
        ↓
Discharge / Sponsor Placement
```

Each day, the published report includes five aggregate counts:

1. Children apprehended and placed in CBP custody
2. Children in CBP custody (on that day)
3. Children transferred out of CBP custody
4. Children in HHS Care (on that day)
5. Children discharged from HHS Care

These are **aggregate, system-level counts** — not records tied to individual children — and
they are published on the days the program reports (which, as this project's data-quality
analysis shows, is not every calendar day).

## Problem

Aggregate daily counts, viewed one day at a time, do not answer operational questions such
as:

- Is the CBP-to-HHS transfer process keeping pace with apprehensions, in aggregate?
- Is the HHS discharge process keeping pace with the population in care?
- Is system load (population in custody / in care) growing, shrinking, or holding steady?
- Are there sustained multi-day periods where the aggregate flow appears strained?
- Are there unusual daily observations that warrant closer inspection?
- Is the overall trend improving, declining, or stable?

## Objective

This project builds a reproducible, statistically grounded analytics system — a data
pipeline, a set of project-defined KPIs, statistical and temporal analysis, a transparent
rule-based bottleneck detector, a two-method anomaly detector, and an interactive dashboard —
to help an analyst answer:

- **Where** is operational pressure occurring (which stage of the pipeline)?
- **When** does it occur (which periods, which days of the week, which months)?
- **Is the situation improving or deteriorating**, based on transparent trend rules?
- **Which metrics should be investigated further** by someone with access to more granular,
  non-public data?

## Explicit Non-Goals

This project does **not** attempt to:

- Determine or predict any individual child's outcome, placement, or processing time.
- Evaluate the performance of any specific shelter, facility, or sponsor.
- Establish geographic bottlenecks (the public dataset contains no location fields).
- Draw causal conclusions from aggregate correlational patterns.
- Represent any of its thresholds, scores, or classifications as official government
  benchmarks. All such items are explicitly labeled **project-defined** throughout the
  codebase and documentation.

See `08_Limitations.md` for the full discussion of what this analysis can and cannot support.
