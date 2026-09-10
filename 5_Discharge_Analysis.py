"""Page 5 — Discharge Analysis."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from dashboard_common import configure_page, load_and_process_data, render_global_filters, apply_date_filter, fmt_pct
from src.analysis import trend_summary, descriptive_statistics, outcome_stability_metrics, outcome_stability_score
from src.visualizations import rolling_comparison_chart, line_chart

configure_page("Discharge Analysis")

clean_df, features_df, report = load_and_process_data()
filters = render_global_filters(features_df)
df = apply_date_filter(features_df, filters)

st.title("Discharge Analysis")
st.caption("HHS discharge performance and variability: Discharge Effectiveness and Outcome Stability.")

if df.empty:
    st.warning("No data in the selected date range.")
    st.stop()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Mean Discharge Effectiveness", fmt_pct(df["discharge_effectiveness"].mean(), 2))
col2.metric("Std Dev", f"{df['discharge_effectiveness'].std():.2f}")
stability = outcome_stability_score(df)
col3.metric("Outcome Stability Score", f"{stability:.1f}/100" if stability == stability else "N/A")
trend = trend_summary(df, "discharge_effectiveness", window_days=min(30, len(df)))
col4.metric("30-day trend", trend["direction"])

st.caption(
    "Discharge Effectiveness compares a daily flow (discharges) to a much larger population "
    "stock (children currently in HHS care), so it is structurally a small percentage -- this "
    "is expected, not a data error."
)

st.divider()
st.plotly_chart(
    rolling_comparison_chart(df, "discharge_effectiveness", "Discharge Effectiveness: Daily vs Rolling Averages", "Percent (%)"),
    use_container_width=True,
)

roll_col = f"discharge_effectiveness_roll{filters['rolling_window']}"
if roll_col in df.columns:
    st.plotly_chart(
        line_chart(df, [roll_col], f"Discharge Effectiveness -- {filters['rolling_window']}-day rolling average", "Percent (%)"),
        use_container_width=True,
    )

st.divider()
c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(
        line_chart(df, ["discharges"], "Daily Discharges", "Children (count)"),
        use_container_width=True,
    )
with c2:
    st.plotly_chart(
        line_chart(df, ["hhs_care"], "Children in HHS Care (population)", "Children (count)"),
        use_container_width=True,
    )

st.divider()
st.subheader("Variability")
metrics = outcome_stability_metrics(df)
m1, m2, m3 = st.columns(3)
m1.metric("Mean", f"{metrics['mean_discharge_effectiveness']:.2f}%")
m2.metric("Coefficient of Variation", f"{metrics['coefficient_of_variation']:.2f}")
m3.metric("Mean 14-day Rolling Std", f"{metrics['mean_rolling_std_14d']:.2f}")

st.divider()
st.subheader("Descriptive Statistics")
st.dataframe(
    descriptive_statistics(df, columns=["discharges", "hhs_care", "discharge_effectiveness"]).round(2),
    use_container_width=True,
)
