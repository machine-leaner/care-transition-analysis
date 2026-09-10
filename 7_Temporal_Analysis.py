"""Page 7 — Temporal Analysis."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st

from dashboard_common import configure_page, load_and_process_data, render_global_filters, apply_date_filter
from src.analysis import weekday_comparison, monthly_aggregation, month_over_month_change, quarterly_aggregation
from src.visualizations import weekday_box_plot, bar_chart, line_chart

configure_page("Temporal Analysis")

clean_df, features_df, report = load_and_process_data()
filters = render_global_filters(features_df)
df = apply_date_filter(features_df, filters)

st.title("Temporal Analysis")
st.caption("Weekday patterns, monthly trends, and month-over-month change.")

if df.empty:
    st.warning("No data in the selected date range.")
    st.stop()

st.subheader("Weekday Patterns")
st.plotly_chart(weekday_box_plot(df, "transfer_efficiency", "Transfer Efficiency by Day of Week"), use_container_width=True)
st.plotly_chart(weekday_box_plot(df, "discharge_effectiveness", "Discharge Effectiveness by Day of Week"), use_container_width=True)

weekday_stats = weekday_comparison(df)
st.dataframe(weekday_stats.round(2), use_container_width=True)

st.divider()
st.subheader("Monthly Analysis")
monthly = monthly_aggregation(df)
metric_choice = st.selectbox(
    "Metric", ["transfer_efficiency", "discharge_effectiveness", "net_flow_pressure",
               "apprehensions", "transfers", "discharges"],
    index=0,
)
st.plotly_chart(bar_chart(monthly, "year_month", metric_choice, f"Monthly Average: {metric_choice}"), use_container_width=True)

mom = month_over_month_change(monthly, metric_choice)
mom_plot_df = mom.rename(columns={"year_month": "date"}).assign(date=lambda d: pd.to_datetime(d["date"]))
st.plotly_chart(
    line_chart(mom_plot_df, [f"{metric_choice}_mom_pct_change"], f"Month-over-Month % Change: {metric_choice}", "% change"),
    use_container_width=True,
)

st.divider()
st.subheader("Quarterly View")
quarterly = quarterly_aggregation(df)
if len(quarterly) > 1:
    st.dataframe(quarterly.round(2), use_container_width=True, hide_index=True)
else:
    st.info("Insufficient date range in current filter to produce a meaningful quarterly comparison.")
