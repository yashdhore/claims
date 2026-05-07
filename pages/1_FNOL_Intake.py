"""
pages/1_FNOL_Intake.py

FNOL Intake page.

This page allows a user to:
1. Select an existing policy from policies.csv
2. Enter new claim information
3. Submit the FNOL
4. Trigger the full agent workflow
"""

import sys
from pathlib import Path
from datetime import date

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from utils.data_store import get_policies
from agents.orchestrator import run_claim_workflow



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
    page_title="FNOL Intake",
    layout="wide"
)

apply_custom_styles()

st.title("FNOL Intake")
st.caption("Submit a First Notice of Loss and run the claim through all agents.")

instruction_box("""
<strong>What this tab does:</strong> This is the starting point for the demo. Select a policy,
enter claim details, and submit the FNOL. The orchestrator will run all agents automatically.
<br><br>
<strong>Before coming here:</strong> Confirm that policies.csv, claims.csv, adjusters.csv,
payments.csv, tasks.csv, documents.csv, and agent_events.csv exist in the data folder.
<br><br>
<strong>What to expect next:</strong> After submission, go to Agent Command Center and select
the new claim ID to view the agent timeline.
""")

try:
    policies = get_policies()
except Exception as e:
    st.error(f"Could not load policies.csv: {e}")
    st.stop()

st.subheader("Step 1: Select Policy")

policy_ids = policies["policy_id"].astype(str).tolist()
selected_policy_id = st.selectbox("Policy ID", policy_ids)

policy = policies[policies["policy_id"].astype(str) == selected_policy_id].iloc[0]

col1, col2, col3 = st.columns(3)
col1.metric("Customer", policy["customer_name"])
col2.metric("Country", policy["country"])
col3.metric("Policy Status", policy["policy_status"])

st.write("Selected policy details")
st.dataframe(pd.DataFrame([policy]), use_container_width=True)

st.subheader("Step 2: Enter FNOL Details")

with st.form("fnol_form"):
    col1, col2 = st.columns(2)

    with col1:
        claim_date = st.date_input("Claim Date", value=date.today())

        claim_type = st.selectbox(
            "Claim Type",
            ["Collision", "Comprehensive", "Bodily Injury", "Property Damage"]
        )

        loss_cause = st.selectbox(
            "Loss Cause",
            [
                "Rear-end accident",
                "Hail damage",
                "Theft",
                "Vandalism",
                "Side collision",
                "Parking lot damage"
            ]
        )

    with col2:
        estimated_loss = st.number_input(
            "Estimated Loss",
            min_value=0.0,
            value=8500.0,
            step=500.0
        )

        st.selectbox(
            "Initial Status",
            ["New"],
            disabled=True
        )

    submitted = st.form_submit_button("Submit FNOL and Run Agents")

if submitted:
    fnol_data = {
        "policy_id": policy["policy_id"],
        "customer_id": policy["customer_id"],
        "country": policy["country"],
        "state": policy["state"],
        "claim_date": claim_date.isoformat(),
        "claim_type": claim_type,
        "loss_cause": loss_cause,
        "claim_status": "New",
        "estimated_loss": estimated_loss,
        "deductible": policy["deductible"],
        "coverage_limit": policy["coverage_limit"],
        "coverage_valid": False,
        "severity_score": 0,
        "fraud_risk_score": 0,
        "adjuster_id": ""
    }

    with st.spinner("Running agents..."):
        result = run_claim_workflow(fnol_data)

    st.success(f"Claim submitted and processed successfully: {result['claim_id']}")
    st.write("Workflow result")
    st.json(result)

    st.warning("Next step: Open Agent Command Center and select this claim to view the agent timeline.")
