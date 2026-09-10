"""Page 9 — Data Explorer."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from dashboard_common import configure_page, load_and_process_data, render_global_filters, apply_date_filter

configure_page("Data Explorer")

clean_df, features_df, report = load_and_process_data()
filters = render_global_filters(features_df)
df = apply_date_filter(features_df, filters)

st.title("Data Explorer")
st.caption("Browse, filter, and download the processed, feature-engineered dataset directly.")

st.subheader("Column Filter")
all_columns = list(df.columns)
default_cols = ["date", "apprehensions", "cbp_custody", "transfers", "hhs_care", "discharges",
                 "transfer_efficiency", "discharge_effectiveness", "net_flow_pressure"]
default_cols = [c for c in default_cols if c in all_columns]
selected_columns = st.multiselect("Columns to display", all_columns, default=default_cols)

st.subheader("Dataset Preview")
st.caption(f"{len(df):,} rows in current date-range selection (see sidebar).")
display_df = df[selected_columns] if selected_columns else df
st.dataframe(display_df, use_container_width=True, hide_index=True)

st.divider()
st.subheader("Download")
csv_bytes = display_df.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download filtered data as CSV",
    data=csv_bytes,
    file_name="uac_filtered_export.csv",
    mime="text/csv",
)

with st.expander("Column reference"):
    st.markdown("""
| Column | Meaning |
|---|---|
| `date` | Reported date |
| `apprehensions` | Children apprehended and placed in CBP custody that day |
| `cbp_custody` | Children in CBP custody on that day |
| `transfers` | Children transferred out of CBP custody that day |
| `hhs_care` | Children in HHS Care on that day (population stock) |
| `discharges` | Children discharged from HHS Care that day |
| `transfer_efficiency` | Transfers / CBP Custody × 100 |
| `discharge_effectiveness` | Discharges / HHS Care × 100 |
| `cbp_transfer_rate` | Transfers / Apprehensions × 100 |
| `net_flow_pressure` | Apprehensions − Discharges |
| `cumulative_net_flow_pressure` | Running cumulative sum of Net Flow Pressure |
| `cbp_transfer_gap` | CBP Custody − Transfers |
| `hhs_discharge_gap` | HHS Care − Discharges |
| `*_roll7 / *_roll14 / *_roll30` | 7/14/30-day rolling averages |

See `docs/04_KPI_Definitions.md` for full formulas and interpretation notes.
""")
