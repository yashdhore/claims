"""
pages/0_README.py

User guide for the Claims Agent Prototype.
"""

import streamlit as st



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
    page_title="README",
    layout="wide"
)

apply_custom_styles()

st.title("README: How to Use This Claims Agent Prototype")

instruction_box("""
<strong>Purpose:</strong> This page explains what the app does, what each tab is for,
what the user should do before visiting each tab, and what to expect next.
""")

blue_card(
    "What This Prototype Demonstrates",
    """
    This app demonstrates an agent-style insurance claims workflow using Streamlit,
    Python functions, CSV files, and synthetic insurance data.
    """
)

st.header("Build Order")

blue_card(
    "1. FNOL Intake Screen",
    """
    Enter policy, claim type, loss cause, and estimated loss. Then run the orchestrator.
    """
)

blue_card(
    "2. Agent Command Center",
    """
    Read agent_events.csv and show the agent timeline.
    """
)

blue_card(
    "3. Claims Dashboard",
    """
    Show claims by status, country, fraud risk, severity, and paid amount.
    """
)

blue_card(
    "4. Executive Insights",
    """
    Show business insights like open claims, high-risk claims, estimated exposure,
    outstanding exposure, and paid amount.
    """
)

st.header("End-to-End Workflow")

st.code(
"""
User enters FNOL
      |
      v
Intake Agent creates claim
      |
      v
Policy Verification Agent checks policy and coverage
      |
      v
Adjuster Agent assigns adjuster and calculates risk scores
      |
      v
Processing Agent approves, denies, or escalates the claim
      |
      v
Reporting Agent refreshes operational and executive insights
      |
      v
Agent Command Center shows the full event trail
""",
language="text"
)

st.header("What Each Tab Does")

blue_card(
    "FNOL Intake",
    """
    <p><span class="blue-label">Purpose:</span> Submit a new First Notice of Loss.</p>
    <p><span class="blue-label">Before coming here:</span> Make sure the data folder contains policies.csv,
    claims.csv, adjusters.csv, payments.csv, claim_notes.csv, tasks.csv, documents.csv, and agent_events.csv.</p>
    <p><span class="blue-label">What the user does:</span> Selects a policy, enters claim details,
    and submits the FNOL.</p>
    <p><span class="blue-label">What to expect next:</span> The app runs the agent workflow and creates
    a new claim. Then go to Agent Command Center.</p>
    """
)

blue_card(
    "Agent Command Center",
    """
    <p><span class="blue-label">Purpose:</span> Show the step-by-step agent event trail.</p>
    <p><span class="blue-label">Before coming here:</span> Submit at least one FNOL.</p>
    <p><span class="blue-label">What the user does:</span> Selects a claim ID and reviews each agent decision.</p>
    <p><span class="blue-label">What to expect next:</span> Go to Claims Dashboard to see operational impact.</p>
    """
)

blue_card(
    "Claims Dashboard",
    """
    <p><span class="blue-label">Purpose:</span> Show the operational claims picture.</p>
    <p><span class="blue-label">Before coming here:</span> Make sure claims.csv has data.</p>
    <p><span class="blue-label">What the user does:</span> Reviews claim counts, status, geography,
    fraud, severity, exposure, and payments.</p>
    <p><span class="blue-label">What to expect next:</span> Go to Executive Insights for business impact.</p>
    """
)

blue_card(
    "Executive Insights",
    """
    <p><span class="blue-label">Purpose:</span> Summarize financial and risk impact for leadership.</p>
    <p><span class="blue-label">Before coming here:</span> Make sure claims.csv and payments.csv have data.</p>
    <p><span class="blue-label">What the user does:</span> Reviews exposure, paid amount,
    outstanding exposure, high-risk claims, and country-level metrics.</p>
    <p><span class="blue-label">What to expect next:</span> Use this page to tell the executive story.</p>
    """
)

st.header("Demo Talk Track")

blue_card(
    "Suggested Message",
    """
    This prototype uses Python, Streamlit, and CSV files to simulate an enterprise claims workflow.
    Each workflow step is represented as an agent. The Intake Agent captures the FNOL, the Policy
    Verification Agent validates coverage, the Adjuster Agent scores risk and assigns work, the
    Processing Agent determines the claim outcome, and the Reporting Agent updates management insights.
    """
)
