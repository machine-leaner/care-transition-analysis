"""Page 8 — Anomaly Analysis."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from dashboard_common import configure_page, load_and_process_data, render_global_filters, apply_date_filter
from src.anomaly_detection import rolling_zscore_anomalies, isolation_forest_anomalies
from src.visualizations import anomaly_scatter

configure_page("Anomaly Analysis")

clean_df, features_df, report = load_and_process_data()
filters = render_global_filters(features_df)
df = apply_date_filter(features_df, filters)

st.title("Anomaly Analysis")
st.caption(
    "Two independent methods for methodological comparison: a simple rolling z-score and an "
    "Isolation Forest (machine learning). Both flag statistically UNUSUAL observations -- "
    "neither confirms an operational failure or data error."
)

if df.empty:
    st.warning("No data in the selected date range.")
    st.stop()

if not filters["anomaly_enabled"]:
    st.info("Anomaly detection is disabled. Enable it in the sidebar to view results.")
    st.stop()

zscore_df = rolling_zscore_anomalies(df)
iso_df = isolation_forest_anomalies(df)

col1, col2 = st.columns(2)
col1.metric("Rolling Z-Score anomalies (dates)", zscore_df["date"].nunique() if not zscore_df.empty else 0)
col2.metric("Isolation Forest anomalies (dates)", len(iso_df))

st.divider()
st.subheader("Statistical Method — Rolling Z-Score")
if zscore_df.empty:
    st.success("No anomalies flagged by the rolling z-score method under current settings.")
else:
    st.dataframe(zscore_df.sort_values("date"), use_container_width=True, hide_index=True)
    metric_for_plot = st.selectbox("Visualize metric", sorted(zscore_df["column"].unique()), key="zscore_metric")
    dates_for_metric = zscore_df.loc[zscore_df["column"] == metric_for_plot, "date"]
    st.plotly_chart(
        anomaly_scatter(df, metric_for_plot, dates_for_metric, f"{metric_for_plot} with Flagged Anomalies (Z-Score)"),
        use_container_width=True,
    )

st.divider()
st.subheader("Machine Learning Method — Isolation Forest")
if iso_df.empty:
    st.success("No anomalies flagged by Isolation Forest under current settings.")
else:
    st.dataframe(iso_df, use_container_width=True, hide_index=True)
    st.plotly_chart(
        anomaly_scatter(df, "discharge_effectiveness", iso_df["date"],
                         "Discharge Effectiveness with Isolation Forest Anomalies"),
        use_container_width=True,
    )

st.divider()
with st.expander("Methodological comparison notes"):
    st.markdown("""
- **Rolling Z-Score** flags a single metric on a single day when it deviates sharply from its
  own recent trailing average. It is easy to interpret but only looks at one metric at a time.
- **Isolation Forest** looks across several metrics simultaneously and can catch multivariate
  outliers (e.g. a day that is unusual in *combination* of features even if no single feature
  looks extreme on its own).
- Overlap between the two methods increases confidence that a date is genuinely unusual;
  disagreement is expected and does not mean either method is "wrong."
""")
