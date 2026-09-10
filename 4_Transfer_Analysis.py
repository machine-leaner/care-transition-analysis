"""Page 4 — Transfer Analysis."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from dashboard_common import configure_page, load_and_process_data, render_global_filters, apply_date_filter, fmt_pct
from src.analysis import trend_summary, descriptive_statistics
from src.visualizations import rolling_comparison_chart, line_chart

configure_page("Transfer Analysis")

clean_df, features_df, report = load_and_process_data()
filters = render_global_filters(features_df)
df = apply_date_filter(features_df, filters)

st.title("Transfer Analysis")
st.caption("CBP → HHS transfer performance: Transfer Efficiency and CBP Transfer Rate.")

if df.empty:
    st.warning("No data in the selected date range.")
    st.stop()

col1, col2, col3 = st.columns(3)
col1.metric("Mean Transfer Efficiency", fmt_pct(df["transfer_efficiency"].mean()))
col2.metric("Mean CBP Transfer Rate", fmt_pct(df["cbp_transfer_rate"].mean()))
trend = trend_summary(df, "transfer_efficiency", window_days=min(30, len(df)))
col3.metric("30-day trend", trend["direction"])

st.divider()
st.plotly_chart(
    rolling_comparison_chart(df, "transfer_efficiency", "Transfer Efficiency: Daily vs Rolling Averages", "Percent (%)"),
    use_container_width=True,
)

roll_col = f"transfer_efficiency_roll{filters['rolling_window']}"
if roll_col in df.columns:
    st.plotly_chart(
        line_chart(df, [roll_col], f"Transfer Efficiency -- {filters['rolling_window']}-day rolling average", "Percent (%)"),
        use_container_width=True,
    )

st.divider()
c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(
        line_chart(df, ["transfers", "cbp_custody"], "Transfers vs CBP Custody", "Children (count)"),
        use_container_width=True,
    )
with c2:
    st.plotly_chart(
        line_chart(df, ["cbp_transfer_rate"], "CBP Transfer Rate (Transfers / Apprehensions)", "Percent (%)"),
        use_container_width=True,
    )

st.divider()
st.subheader("Descriptive Statistics")
st.dataframe(
    descriptive_statistics(df, columns=["transfers", "cbp_custody", "transfer_efficiency", "cbp_transfer_rate"]).round(2),
    use_container_width=True,
)
