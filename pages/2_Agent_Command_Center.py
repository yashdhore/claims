"""
pages/2_Agent_Command_Center.py

Agent Command Center page.

This page now reads agent_events and claims directly from Cosmos DB and shows the
event timeline for a selected claim.
"""

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


def load_agent_events_data() -> pd.DataFrame:
    """
    Load all agent event documents from the Cosmos DB agent_events container.
    """
    try:
        container = cosmos_store.get_container('agent_events')
        items = list(
            container.query_items(
                query="SELECT * FROM c",
                enable_cross_partition_query=True,
            )
        )
        return pd.DataFrame(items)
    except Exception:
        return pd.DataFrame()


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


AGENT_DESCRIPTIONS = {
    "Intake Agent": "The Intake Agent created the claim and normalized the FNOL data.",
    "Policy Verification Agent": "The Policy Verification Agent checked policy status, policy dates, deductible, coverage limit, and whether coverage applies.",
    "Adjuster Agent": "The Adjuster Agent assigned the claim to an adjuster and calculated severity and fraud risk scores.",
    "Processing Agent": "The Processing Agent determined whether the claim should be approved, denied, or escalated for additional review.",
    "Reporting Agent": "The Reporting Agent refreshed dashboard metrics and converted operational activity into management insights."
}


st.set_page_config(
    page_title="Agent Command Center",
    layout="wide"
)

apply_custom_styles()

st.title("Agent Command Center")
st.caption("View the full event timeline for each claim.")

instruction_box("""
<strong>What this tab does:</strong> This page shows the agent-by-agent workflow trail from
Cosmos DB agent_events.
<br><br>
<strong>Before coming here:</strong> Submit at least one FNOL from the FNOL Intake page.
<br><br>
<strong>What to expect next:</strong> Review the sequence of agent decisions, then go to
Claims Dashboard to see operational impact.
""")

try:
    events = load_agent_events_data()
    claims = load_claims_data()
except Exception as e:
    st.error(f"Could not load required Cosmos DB data: {e}")
    st.stop()

if events.empty:
    st.warning("No agent events found yet. Go to FNOL Intake and submit a claim first.")
    st.stop()

claim_ids = events["claim_id"].dropna().astype(str).unique().tolist()
selected_claim_id = st.selectbox("Select Claim ID", sorted(claim_ids, reverse=True))

claim_events = events[events["claim_id"].astype(str) == selected_claim_id].copy()
claim_events = claim_events.sort_values("timestamp")

st.subheader(f"Agent Timeline for {selected_claim_id}")

for _, row in claim_events.iterrows():
    agent_name = row["agent_name"]
    agent_description = AGENT_DESCRIPTIONS.get(
        agent_name,
        "This agent completed one step in the claims workflow."
    )

    st.markdown(
        f"""
        <div class="agent-card">
            <div class="agent-name">{agent_name}</div>
            <div class="agent-description">{agent_description}</div>
            <p><span class="blue-label">Status:</span> {row['status']}</p>
            <p><span class="blue-label">Event Type:</span> {row['event_type']}</p>
            <p><span class="blue-label">Input:</span> {row['input_summary']}</p>
            <p><span class="blue-label">Decision:</span> {row['decision']}</p>
            <p><span class="blue-label">Output:</span> {row['output_summary']}</p>
            <p><span class="blue-label">Next Agent:</span> {row['next_agent']}</p>
            <p><span class="blue-label">Timestamp:</span> {row['timestamp']}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

st.divider()

st.subheader("Raw Agent Events")
st.dataframe(claim_events, use_container_width=True)

st.warning("Next step: Open Claims Dashboard to see how this claim affects operational metrics.")
