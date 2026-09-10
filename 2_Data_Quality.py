"""Page 2 — Data Quality."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st

from dashboard_common import configure_page, load_and_process_data, render_global_filters
from src.data_loader import load_raw_data, inspect_raw_data
from src.preprocessing import validate_numeric_ranges

configure_page("Data Quality")

clean_df, features_df, report = load_and_process_data()
filters = render_global_filters(features_df)

st.title("Data Quality")
st.caption("Findings from the initial inspection and validation stages of the pipeline (raw -> validated -> cleaned).")

raw_df = load_raw_data()
raw_summary = inspect_raw_data(raw_df)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Raw rows (incl. blanks)", f"{raw_summary['shape'][0]:,}")
col2.metric("Fully-blank rows dropped", f"{raw_summary['fully_blank_rows']:,}")
col3.metric("Clean rows", f"{len(clean_df):,}")
col4.metric("Columns", f"{raw_summary['shape'][1]}")

st.divider()
c1, c2 = st.columns(2)

with c1:
    st.subheader("Missing Values (raw file)")
    missing_df = pd.DataFrame(list(raw_summary["missing_values"].items()), columns=["Column", "Missing (raw)"])
    st.dataframe(missing_df, use_container_width=True, hide_index=True)
    st.caption(
        f"All {raw_summary['fully_blank_rows']} missing values per column come from the same "
        f"{raw_summary['fully_blank_rows']} fully-blank trailing rows in the CSV export -- a "
        f"formatting artifact, not scattered missing observations."
    )

with c2:
    st.subheader("Numeric Range Validation (after cleaning)")
    numeric_issues = validate_numeric_ranges(clean_df)
    issues_df = pd.DataFrame(list(numeric_issues.items()), columns=["Check", "Count"])
    st.dataframe(issues_df, use_container_width=True, hide_index=True)
    if all(v == 0 for k, v in numeric_issues.items() if "negative" in k or "null" in k):
        st.success("No negative values and no missing values in any numeric column after cleaning.")

st.divider()
st.subheader("Date Coverage & Continuity")
continuity = report["date_continuity"]
c1, c2, c3 = st.columns(3)
c1.metric("Date range", f"{continuity['date_min'].date()} → {continuity['date_max'].date()}")
c2.metric("Reported days", f"{continuity['n_reported_days']:,}")
c3.metric("Missing calendar days", f"{continuity['n_missing_days']:,}")

wc1, wc2 = st.columns(2)
with wc1:
    st.markdown("**Reported-day weekday counts**")
    st.dataframe(
        pd.DataFrame(list(continuity["weekday_counts_reported"].items()), columns=["Weekday", "Count"]),
        use_container_width=True, hide_index=True,
    )
with wc2:
    st.markdown("**Missing-day weekday counts**")
    st.dataframe(
        pd.DataFrame(list(continuity["weekday_counts_missing"].items()), columns=["Weekday", "Count"]),
        use_container_width=True, hide_index=True,
    )

st.info(
    "The program's own reporting cadence skips Friday and Saturday almost entirely. This is "
    "treated as a structural characteristic of the source data (documented in "
    "docs/03_EDA_Findings.md), not corrected via interpolation or forward-filling."
)

st.divider()
st.subheader("Duplicate Records")
st.metric("Duplicate rows found (post-cleaning)", report.get("duplicate_date_rows", 0))

st.subheader("Data Types (post-cleaning)")
dtype_df = pd.DataFrame({"Column": clean_df.dtypes.index.astype(str), "Type": clean_df.dtypes.values.astype(str)})
st.dataframe(dtype_df, use_container_width=True, hide_index=True)
