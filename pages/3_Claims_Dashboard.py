"""
pages/3_Claims_Dashboard.py

Operational claims dashboard.
"""

import sys
from pathlib import Path

import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from utils.data_store import (
    get_claims,
    get_payments,
    claims_summary,
    claims_by_country,
    claims_by_status
)



def apply_custom_styles():
    """
    Apply custom styling across the Streamlit app.

    Design choices:
    - Buttons are cyan with white font.
    - Important bordered sections use dark blue borders.
    - Agent names and key headings use dark blue.
    """

    st.markdown(
        """
        <style>
        /* Main button styling */
        div.stButton > button {
            background-color: #00AEEF;
            color: white;
            border: 1px solid #00AEEF;
            border-radius: 6px;
            padding: 0.55rem 1rem;
            font-weight: 600;
        }

        div.stButton > button:hover {
            background-color: #008FC4;
            color: white;
            border: 1px solid #008FC4;
        }

        div.stButton > button:focus {
            background-color: #008FC4;
            color: white;
            border: 1px solid #008FC4;
            box-shadow: none;
        }

        /* Dark blue reusable card */
        .blue-card {
            border: 2px solid #003B70;
            border-radius: 10px;
            padding: 18px;
            margin-bottom: 16px;
            background-color: #F8FBFF;
        }

        /* Dark blue section title */
        .blue-title {
            color: #003B70;
            font-weight: 700;
            margin-bottom: 8px;
        }

        /* Dark blue smaller label */
        .blue-label {
            color: #003B70;
            font-weight: 600;
        }

        /* Soft instruction box */
        .instruction-box {
            border-left: 6px solid #003B70;
            background-color: #F3F8FC;
            padding: 14px 18px;
            border-radius: 6px;
            margin-bottom: 18px;
        }

        /* Agent card */
        .agent-card {
            border: 2px solid #003B70;
            border-radius: 10px;
            padding: 18px;
            margin-bottom: 16px;
            background-color: #FFFFFF;
        }

        .agent-name {
            color: #003B70;
            font-size: 1.25rem;
            font-weight: 800;
            margin-bottom: 6px;
        }

        .agent-description {
            color: #1F2937;
            font-size: 1rem;
            margin-bottom: 14px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


def blue_card(title, body):
    """
    Render a reusable dark-blue bordered card.
    """
    st.markdown(
        f"""
        <div class="blue-card">
            <div class="blue-title">{title}</div>
            <div>{body}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def instruction_box(body):
    """
    Render a reusable instruction box.
    """
    st.markdown(
        f"""
        <div class="instruction-box">
            {body}
        </div>
        """,
        unsafe_allow_html=True
    )



st.set_page_config(
    page_title="Claims Dashboard",
    layout="wide"
)

apply_custom_styles()

st.title("Claims Dashboard")
st.caption("Operational view of claims, risk, status, geography, and payments.")

instruction_box("""
<strong>What this tab does:</strong> This dashboard shows the operational claims picture.
It reads claims.csv and payments.csv.
<br><br>
<strong>Before coming here:</strong> Submit an FNOL and review the agent workflow, or use the
historical synthetic claims already loaded in the CSV files.
<br><br>
<strong>What to expect next:</strong> Use these metrics to understand workload, status,
fraud risk, severity, and multinational claim distribution.
""")

try:
    claims = get_claims()
    payments = get_payments()
    summary = claims_summary()
except Exception as e:
    st.error(f"Could not load claims dashboard data: {e}")
    st.stop()

blue_card(
    "Operational Summary",
    "The metrics below are recalculated from the latest CSV data every time the page loads."
)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Claims", summary["total_claims"])
col2.metric("Open Claims", summary["open_claims"])
col3.metric("High Fraud Claims", summary["high_fraud_claims"])
col4.metric("High Severity Claims", summary["high_severity_claims"])

col5, col6 = st.columns(2)
col5.metric("Total Estimated Loss", f"${summary['total_estimated_loss']:,.2f}")
col6.metric("Total Paid", f"${summary['total_paid']:,.2f}")

st.divider()

left, right = st.columns(2)

with left:
    st.subheader("Claims by Status")
    status_df = claims_by_status()

    if not status_df.empty:
        st.bar_chart(status_df.set_index("claim_status"))
        st.dataframe(status_df, use_container_width=True)
    else:
        st.warning("No status data available.")

with right:
    st.subheader("Claims by Country")
    country_df = claims_by_country()

    if not country_df.empty:
        st.bar_chart(country_df.set_index("country")["total_claims"])
        st.dataframe(country_df, use_container_width=True)
    else:
        st.warning("Country column not found or no country data available.")

st.divider()

st.subheader("Claims Detail")
st.dataframe(claims, use_container_width=True)

st.warning("Next step: Open Executive Insights to translate operational data into business metrics.")
