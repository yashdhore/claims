"""
app.py

Main landing page for the Claims Agent Prototype.

Run the app with:
    streamlit run app.py
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
    page_title="Claims Agent Prototype",
    layout="wide"
)

apply_custom_styles()

st.title("Claims Agent Prototype")
st.subheader("Python, CSV, Streamlit, and agent-style workflow")

instruction_box("""
<strong>Start here:</strong> This app demonstrates an end-to-end insurance claims workflow.
The app uses Python agents, CSV files, and Streamlit screens to simulate how a First Notice
of Loss moves through intake, policy verification, adjuster review, processing, and reporting.
""")

blue_card(
    "Recommended Demo Flow",
    """
    <ol>
        <li>Open the README page to understand the flow.</li>
        <li>Submit a new claim from FNOL Intake.</li>
        <li>Review the agent timeline in Agent Command Center.</li>
        <li>Review operational metrics in Claims Dashboard.</li>
        <li>Review business metrics in Executive Insights.</li>
    </ol>
    """
)

blue_card(
    "Agent Workflow",
    """
    User submits FNOL &rarr; Intake Agent &rarr; Policy Verification Agent &rarr;
    Adjuster Agent &rarr; Processing Agent &rarr; Reporting Agent.
    """
)

blue_card(
    "Enterprise Migration Story",
    """
    This prototype can later be moved into Microsoft Copilot Studio. Python agents can become
    Copilot topics, actions, or Power Automate flows. CSV files can be replaced by Dataverse,
    SQL, SharePoint, Fabric, or another enterprise data source.
    """
)
