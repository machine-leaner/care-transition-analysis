"""Page 6 — Bottleneck Analysis."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from dashboard_common import configure_page, load_and_process_data, render_global_filters, apply_date_filter
from src.bottleneck_detection import run_bottleneck_analysis
from src.visualizations import bottleneck_gantt, cumulative_pressure_chart

configure_page("Bottleneck Analysis")

clean_df, features_df, report = load_and_process_data()
filters = render_global_filters(features_df)
df = apply_date_filter(features_df, filters)

st.title("Bottleneck Analysis")
st.caption(
    "Rule-based, transparent detection of sustained periods below the configured thresholds "
    "(set in the sidebar). These are project-defined analytical thresholds -- NOT official "
    "government thresholds -- and do not, by themselves, prove the cause of any detected period."
)

if df.empty:
    st.warning("No data in the selected date range.")
    st.stop()

bn = run_bottleneck_analysis(
    df, filters["transfer_threshold"], filters["discharge_threshold"], filters["sustained_days"],
)

col1, col2, col3 = st.columns(3)
col1.metric("Transfer bottleneck periods", len(bn["transfer_bottlenecks"]))
col2.metric("Discharge bottleneck periods", len(bn["discharge_bottlenecks"]))
col3.metric("Sustained accumulation periods", len(bn["sustained_accumulation"]))

st.divider()

for key, title in [
    ("transfer_bottlenecks", "Potential CBP → HHS Transfer Bottlenecks"),
    ("discharge_bottlenecks", "Potential HHS Discharge Bottlenecks"),
    ("sustained_accumulation", "Sustained Accumulation Periods (Net Flow Pressure > 0)"),
]:
    st.subheader(title)
    result = bn[key]
    if result.empty:
        st.success("No periods detected under the current thresholds.")
    else:
        fig = bottleneck_gantt(result, title)
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)
        display_cols = [c for c in ["start_date", "end_date", "duration_days", "average_value",
                                     "threshold", "severity", "type"] if c in result.columns]
        st.dataframe(result[display_cols], use_container_width=True, hide_index=True)
    st.divider()

st.subheader("Net Accumulation")
st.plotly_chart(cumulative_pressure_chart(df), use_container_width=True)
