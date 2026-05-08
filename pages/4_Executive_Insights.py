"""
pages/4_Executive_Insights.py

Executive and financial insights page.
"""

# This page now reads claims and payments directly from Cosmos DB via cosmos_store.

import sys
from pathlib import Path

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from agents.data_access.cosmos_store import cosmos_store



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


def to_numeric_series(series, default=0.0) -> pd.Series:
    """
    Convert a series to numeric values and replace invalid entries with a default.
    """
    return pd.to_numeric(series, errors='coerce').fillna(default)


def normalize_claims_dataframe(claims_df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize Cosmos DB claim data for executive metrics.
    """
    if claims_df.empty:
        return pd.DataFrame(columns=[
            'claim_status', 'estimated_loss', 'fraud_risk_score', 'severity_score'
        ])

    claims_df = claims_df.copy()
    if 'claim_status' in claims_df.columns:
        claims_df['claim_status'] = claims_df['claim_status'].astype(str)
    elif 'status' in claims_df.columns:
        claims_df['claim_status'] = claims_df['status'].astype(str)
    else:
        claims_df['claim_status'] = 'Unknown'

    claims_df['estimated_loss'] = to_numeric_series(claims_df.get('estimated_loss', pd.Series(0, index=claims_df.index)))
    claims_df['fraud_risk_score'] = to_numeric_series(claims_df.get('fraud_risk_score', pd.Series(0, index=claims_df.index)))
    claims_df['severity_score'] = to_numeric_series(claims_df.get('severity_score', pd.Series(0, index=claims_df.index)))

    return claims_df


st.set_page_config(
    page_title="Executive Insights",
    layout="wide"
)

apply_custom_styles()

st.title("Executive Insights")
st.caption("Business and financial view for leadership.")

instruction_box("""
<strong>What this tab does:</strong> This page converts operational claims data into
executive-level financial and risk insights using Cosmos DB.
<br><br>
<strong>Before coming here:</strong> Confirm that the claims and payments Cosmos DB
containers are populated. For the best demo, submit a new FNOL and review the Agent
Command Center first.
<br><br>
<strong>What to expect next:</strong> Use this page to discuss exposure, payments,
outstanding exposure, risk concentration, and the future Copilot Studio roadmap.
""")

try:
    claims = normalize_claims_dataframe(load_claims_data())
    payments = load_payments_data()
except Exception as e:
    st.error(f"Could not load executive insight data: {e}")
    st.stop()

if claims.empty:
    total_claims = 0
    open_claims = 0
    approved_claims = 0
    denied_claims = 0
    estimated_exposure = 0.0
    high_fraud = pd.DataFrame()
    high_severity = pd.DataFrame()
else:
    total_claims = len(claims)
    open_claims = int(claims['claim_status'].str.lower().isin(["new", "under review"]).sum())
    approved_claims = int(claims['claim_status'].str.lower().isin(["approved", "paid", "closed"]).sum())
    denied_claims = int((claims['claim_status'].str.lower() == "denied").sum())
    estimated_exposure = float(claims['estimated_loss'].sum())
    high_fraud = claims[claims['fraud_risk_score'] >= 75]
    high_severity = claims[claims['severity_score'] >= 75]

if payments.empty or 'payment_amount' not in payments:
    total_paid = 0.0
else:
    total_paid = float(to_numeric_series(payments['payment_amount']).sum())

outstanding_exposure = estimated_exposure - total_paid

blue_card(
    "Executive Summary",
    "This view is designed for leadership. It focuses on claim volume, financial exposure, payments, outstanding exposure, and high-risk claims."
)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Claims", total_claims)
col2.metric("Open Claims", open_claims)
col3.metric("Approved, Paid, or Closed", approved_claims)
col4.metric("Denied Claims", denied_claims)

col5, col6, col7 = st.columns(3)
col5.metric("Estimated Exposure", f"${estimated_exposure:,.2f}")
col6.metric("Total Paid", f"${total_paid:,.2f}")
col7.metric("Outstanding Exposure", f"${outstanding_exposure:,.2f}")

st.divider()

st.subheader("Executive Narrative")

st.markdown(f"""
Based on the current claims data:

- The claims operation is managing **{total_claims} total claims**.
- **{open_claims} claims** are still open and may require adjuster action.
- **{len(high_fraud)} claims** have high fraud risk and may need investigation.
- **{len(high_severity)} claims** have high severity and may require priority handling.
- Estimated claim exposure is **${estimated_exposure:,.2f}**.
- Total payment issued or pending is **${total_paid:,.2f}**.
- Outstanding exposure is **${outstanding_exposure:,.2f}**.

This gives leaders a quick view of operational workload, financial exposure,
and risk concentration.
""")

st.divider()

st.subheader("Country-Level Insight")
country_df = claims_by_country(claims)

if not country_df.empty:
    st.dataframe(country_df, use_container_width=True)
else:
    st.warning("Country-level data is not available.")

st.subheader("High Fraud Risk Claims")
if not high_fraud.empty:
    st.dataframe(high_fraud, use_container_width=True)
else:
    st.success("No high fraud risk claims found.")

st.subheader("High Severity Claims")
if not high_severity.empty:
    st.dataframe(high_severity, use_container_width=True)
else:
    st.success("No high severity claims found.")

blue_card(
    "Demo Message",
    """
    This prototype shows how an agentic claims workflow creates operational transparency,
    auditability, and executive-level insight using Cosmos DB-backed data access.
    """
)
