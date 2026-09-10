"""Page 3 — Pipeline Analysis."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from dashboard_common import configure_page, load_and_process_data, render_global_filters, apply_date_filter
from src.analysis import monthly_aggregation
from src.visualizations import pipeline_flow_chart, pipeline_sankey, line_chart, bar_chart

configure_page("Pipeline Analysis")

clean_df, features_df, report = load_and_process_data()
filters = render_global_filters(features_df)
df = apply_date_filter(features_df, filters)

st.title("Pipeline Analysis")
st.caption("The full CBP apprehension → CBP custody → transfer → HHS care → discharge flow over the selected period.")

if df.empty:
    st.warning("No data in the selected date range.")
    st.stop()

st.plotly_chart(pipeline_flow_chart(df), use_container_width=True)

st.divider()
c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(
        line_chart(df, ["apprehensions", "transfers"], "Apprehensions vs Transfers", "Children (count)"),
        use_container_width=True,
    )
with c2:
    st.plotly_chart(
        line_chart(df, ["hhs_care"], "Children in HHS Care (population)", "Children (count)"),
        use_container_width=True,
    )

st.divider()
st.subheader("Aggregate Period Flow (Sankey)")
st.caption(
    "Represents SUM totals across the selected period, not a tracked cohort of individual "
    "children moving stage to stage."
)
st.plotly_chart(pipeline_sankey(df), use_container_width=True)

st.divider()
st.subheader("Monthly Comparison")
monthly = monthly_aggregation(df, columns=["apprehensions", "cbp_custody", "transfers", "hhs_care", "discharges"], agg="mean")
st.plotly_chart(
    bar_chart(monthly, "year_month", "apprehensions", "Average Daily Apprehensions by Month", "Children (count)"),
    use_container_width=True,
)
st.dataframe(monthly.round(1), use_container_width=True, hide_index=True)
