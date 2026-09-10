"""
app.py
======
Entry point for the Care Transition Efficiency & Placement Outcome
Analytics Streamlit dashboard. This file renders Page 1 — Executive
Summary. Pages 2-9 live in pages/ and are auto-discovered by Streamlit's
multipage navigation.

Run with: streamlit run app.py
"""
import pandas as pd
import streamlit as st

from dashboard_common import (
    configure_page, load_and_process_data, render_global_filters, apply_date_filter,
    fmt_pct, fmt_num,
)
from src.bottleneck_detection import run_bottleneck_analysis
from src.anomaly_detection import run_anomaly_detection
from src.analysis import trend_summary, outcome_stability_score
from src.insights import generate_all_insights
from src.visualizations import line_chart, dual_axis_chart

configure_page("Executive Summary")

clean_df, features_df, report = load_and_process_data()
filters = render_global_filters(features_df)
df = apply_date_filter(features_df, filters)

st.title("Executive Summary")
st.caption(
    "Aggregate operational snapshot of the CBP → HHS → Discharge pipeline for the selected "
    "date range. All figures are aggregate, project-defined indicators -- see the Data "
    "Quality and Limitations documentation before drawing conclusions."
)

if df.empty:
    st.warning("No data in the selected date range. Adjust the filters in the sidebar.")
    st.stop()

latest = df.sort_values("date").iloc[-1]

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Transfer Efficiency (latest)", fmt_pct(latest["transfer_efficiency"]))
col2.metric("Discharge Effectiveness (latest)", fmt_pct(latest["discharge_effectiveness"], 2))
col3.metric("CBP Transfer Rate (latest)", fmt_pct(latest["cbp_transfer_rate"]))
col4.metric("Net Flow Pressure (latest)", fmt_num(latest["net_flow_pressure"]))
stability = outcome_stability_score(df)
col5.metric("Outcome Stability Score", f"{stability:.1f} / 100" if pd.notna(stability) else "N/A")

st.divider()

left, right = st.columns([2, 1])

with left:
    st.subheader("Key KPI Trends")
    fig = line_chart(
        df, ["transfer_efficiency", "discharge_effectiveness"],
        "Transfer Efficiency vs Discharge Effectiveness (daily)", "Percent (%)",
    )
    st.plotly_chart(fig, use_container_width=True)

    fig2 = dual_axis_chart(df, "net_flow_pressure", "cumulative_net_flow_pressure",
                            "Net Flow Pressure (daily) vs Cumulative Net Flow Pressure")
    st.plotly_chart(fig2, use_container_width=True)

with right:
    st.subheader("Recent Trend (last 30 reported days)")
    for col, label in [("transfer_efficiency", "Transfer Efficiency"),
                        ("discharge_effectiveness", "Discharge Effectiveness"),
                        ("cbp_transfer_rate", "CBP Transfer Rate")]:
        summary = trend_summary(df, col, window_days=30)
        direction = summary["direction"]
        icon = {"Increasing": "📈", "Decreasing": "📉", "Stable": "➡️"}.get(direction, "❔")
        st.markdown(f"**{label}:** {icon} {direction}")

    st.divider()
    st.subheader("Current Status")
    bn = run_bottleneck_analysis(
        df, filters["transfer_threshold"], filters["discharge_threshold"], filters["sustained_days"],
    )
    n_active_bottlenecks = sum(
        1 for res in bn.values() if not res.empty and (res["end_date"] == df["date"].max()).any()
    )
    if n_active_bottlenecks > 0:
        st.error(f"{n_active_bottlenecks} bottleneck condition(s) active as of the latest reported date.")
    else:
        st.success("No bottleneck condition is currently active based on the selected thresholds.")

st.divider()
st.subheader("Key Findings")

an = run_anomaly_detection(df) if filters["anomaly_enabled"] else None
insights = generate_all_insights(df, bottleneck_results=bn, anomaly_results=an)
for insight in insights:
    st.markdown(f"- {insight}")

with st.expander("What these KPIs do and do NOT measure"):
    st.markdown("""
- **Transfer Efficiency** and **Discharge Effectiveness** are aggregate, same-day ratios of
  flow to population -- they are *indicators*, not direct measurements of individual
  processing speed or individual discharge probability.
- **Net Flow Pressure** reflects aggregate inflow vs outflow imbalance, not a forecast.
- The **Outcome Stability Score** is a project-defined 0-100 normalization of discharge
  effectiveness variability, not an official government KPI.
- See the `docs/` folder (04_KPI_Definitions.md, 08_Limitations.md) for full methodology.
""")
