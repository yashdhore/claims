"""
pages/3_Claims_Dashboard.py

Operational claims dashboard.
"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from agents.data_access.cosmos_store import cosmos_store

# This dashboard page now reads claims and payments directly from Cosmos DB.



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


def load_claims_data() -> pd.DataFrame:
    """
    Load all claim documents from the Cosmos DB claims container.
    """
    try:
        container = cosmos_store.get_container('claims')
        items = list(
            container.query_items(
                query="SELECT * FROM c",
                enable_cross_partition_query=True,
            )
        )
        return pd.DataFrame(items)
    except Exception:
        return pd.DataFrame()


def load_payments_data() -> pd.DataFrame:
    """
    Load all payment documents from the Cosmos DB payments container.
    """
    try:
        container = cosmos_store.get_container('payments')
        items = list(
            container.query_items(
                query="SELECT * FROM c",
                enable_cross_partition_query=True,
            )
        )
        return pd.DataFrame(items)
    except Exception:
        return pd.DataFrame()


def claims_summary(claims_df: pd.DataFrame, payments_df: pd.DataFrame) -> dict:
    """
    Build summary metrics from claims and payments DataFrames.
    """
    if claims_df.empty:
        return {
            'total_claims': 0,
            'open_claims': 0,
            'high_fraud_claims': 0,
            'high_severity_claims': 0,
            'total_estimated_loss': 0.0,
            'total_paid': 0.0,
        }

    claims_df = claims_df.copy()

    if 'claim_status' in claims_df.columns:
        claims_df['claim_status'] = claims_df['claim_status'].astype(str)
    elif 'status' in claims_df.columns:
        claims_df['claim_status'] = claims_df['status'].astype(str)
    else:
        claims_df['claim_status'] = 'Unknown'

    claims_df['estimated_loss'] = pd.to_numeric(claims_df.get('estimated_loss', 0), errors='coerce').fillna(0)
    claims_df['severity_score'] = pd.to_numeric(claims_df.get('severity_score', 0), errors='coerce').fillna(0)
    claims_df['fraud_risk_score'] = pd.to_numeric(claims_df.get('fraud_risk_score', 0), errors='coerce').fillna(0)

    open_mask = claims_df['claim_status'].str.lower().isin(
        ['open', 'under review', 'pending', 'in progress', 'in review']
    )

    total_paid = 0.0
    if not payments_df.empty and 'payment_amount' in payments_df.columns:
        total_paid = pd.to_numeric(payments_df['payment_amount'], errors='coerce').fillna(0).sum()

    return {
        'total_claims': int(len(claims_df)),
        'open_claims': int(open_mask.sum()),
        'high_fraud_claims': int((claims_df['fraud_risk_score'] > 75).sum()),
        'high_severity_claims': int((claims_df['severity_score'] > 75).sum()),
        'total_estimated_loss': float(claims_df['estimated_loss'].sum()),
        'total_paid': float(total_paid),
    }


def claims_by_country(claims_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a DataFrame grouped by country with claim counts.
    """
    if claims_df.empty or 'country' not in claims_df.columns:
        return pd.DataFrame(columns=['country', 'total_claims'])

    grouped = (
        claims_df
        .assign(country=claims_df['country'].astype(str).fillna('Unknown'))
        .groupby('country')
        .size()
        .reset_index(name='total_claims')
        .sort_values('total_claims', ascending=False)
    )
    return grouped


def claims_by_status(claims_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a DataFrame grouped by claim status with claim counts.
    """
    if claims_df.empty:
        return pd.DataFrame(columns=['claim_status', 'total_claims'])

    if 'claim_status' not in claims_df.columns and 'status' in claims_df.columns:
        claims_df['claim_status'] = claims_df['status'].astype(str)

    if 'claim_status' not in claims_df.columns:
        return pd.DataFrame(columns=['claim_status', 'total_claims'])

    grouped = (
        claims_df
        .assign(claim_status=claims_df['claim_status'].astype(str).fillna('Unknown'))
        .groupby('claim_status')
        .size()
        .reset_index(name='total_claims')
        .sort_values('total_claims', ascending=False)
    )
    return grouped


st.set_page_config(
    page_title="Claims Dashboard",
    layout="wide"
)

apply_custom_styles()

st.title("Claims Dashboard")
st.caption("Operational view of claims, risk, status, geography, and payments.")

instruction_box("""
<strong>What this tab does:</strong> This dashboard shows the operational claims picture.
It reads claims and payments directly from Cosmos DB.
<br><br>
<strong>Before coming here:</strong> Submit an FNOL and review the agent workflow, or use the
historical synthetic claims already loaded in the Cosmos DB account.
<br><br>
<strong>What to expect next:</strong> Use these metrics to understand workload, status,
fraud risk, severity, and multinational claim distribution.
""")

try:
    claims = load_claims_data()
    payments = load_payments_data()
    summary = claims_summary(claims, payments)
except Exception as e:
    st.error(f"Could not load claims dashboard data: {e}")
    st.stop()

blue_card(
    "Operational Summary",
    "The metrics below are recalculated from the latest Cosmos DB data every time the page loads."
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
    status_df = claims_by_status(claims)

    if not status_df.empty:
        st.bar_chart(status_df.set_index("claim_status"))
        st.dataframe(status_df, use_container_width=True)
    else:
        st.warning("No status data available.")

with right:
    st.subheader("Claims by Country")
    country_df = claims_by_country(claims)

    if not country_df.empty:
        st.bar_chart(country_df.set_index("country")["total_claims"])
        st.dataframe(country_df, use_container_width=True)
    else:
        st.warning("Country column not found or no country data available.")

st.divider()

st.subheader("Claims Detail")
st.dataframe(claims, use_container_width=True)

st.warning("Next step: Open Executive Insights to translate operational data into business metrics.")
