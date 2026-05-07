# Claims Agent Prototype

## Overview

This project is a rapid prototype of an agentic insurance claims processing system built using:

- Python
- Streamlit
- CSV files
- Synthetic insurance data

The purpose of the prototype is to demonstrate how a First Notice of Loss (FNOL) request can move through multiple specialized agents, from intake to validation, adjuster review, processing, reporting, and executive insights.

The system simulates an enterprise insurance workflow while remaining lightweight enough to build quickly and run locally.

---

# Business Objective

Insurance companies process large volumes of claims across multiple regions and product lines.

This prototype demonstrates how agentic workflows can improve:

- Operational transparency
- Claim processing automation
- Explainability
- Auditability
- Risk visibility
- Executive reporting
- Straight-through processing

The prototype is intentionally designed to later migrate into:

- Microsoft Copilot Studio
- Power Automate
- Dataverse
- Microsoft Fabric
- Power BI
- SQL / SharePoint / Enterprise APIs

---

# Key Features

## FNOL Intake

Users can submit a new claim by entering:

- Policy ID
- Claim date
- Claim type
- Loss cause
- Estimated loss amount

The FNOL request triggers the full multi-agent workflow.

---

## Policy Verification Agent

Validates:

- Policy status
- Policy dates
- Coverage eligibility
- Deductible
- Coverage limit

The system explains exactly why coverage passed or failed.

Example:

```text
Coverage failed because:
Claim date 2026-05-06 is after policy end date 2025-07-19
```

---

## Adjuster Agent

Automatically:

- Assigns adjusters
- Calculates severity score
- Calculates fraud risk score
- Creates review tasks

Example:

```text
Severity = 45
Fraud = 78
```

---

## Processing Agent

Determines:

- Approved
- Denied
- Under Review

Also explains:

- Which rule triggered
- Why the decision happened
- Recommended next action
- Payment calculation

Example:

```text
Claim approved

Rule Triggered:
Coverage valid and fraud risk below threshold

Recommended Action:
Issue payment of $10,500.00
```

---

## Reporting Agent

Refreshes:

- Operational metrics
- Dashboard metrics
- Executive insights
- Exposure calculations

---

## Agent Command Center

Provides:

- Full workflow timeline
- Agent-by-agent decisions
- Audit trail
- Explainability

This is the core "agentic workflow" view.

---

# Architecture

## End-to-End Workflow

```text
User submits FNOL
      |
      v
Intake Agent creates claim
      |
      v
Policy Verification Agent validates coverage
      |
      v
Adjuster Agent assigns adjuster and scores risk
      |
      v
Processing Agent approves, denies, or escalates
      |
      v
Reporting Agent refreshes dashboards
      |
      v
Agent Command Center shows the audit trail
```

---

# Technology Stack

| Component | Technology |
|---|---|
| UI | Streamlit |
| Workflow Logic | Python |
| Backend Storage | CSV Files |
| Reporting | Streamlit Dashboards |
| Data | Synthetic Insurance Data |

---

# Project Structure

```text
_qbe_claims/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── agents/
│   ├── __init__.py
│   ├── intake_agent.py
│   ├── policy_agent.py
│   ├── adjuster_agent.py
│   ├── processing_agent.py
│   ├── reporting_agent.py
│   └── orchestrator.py
│
├── utils/
│   ├── __init__.py
│   └── data_store.py
│
├── pages/
│   ├── 0_README.py
│   ├── 1_FNOL_Intake.py
│   ├── 2_Agent_Command_Center.py
│   ├── 3_Claims_Dashboard.py
│   └── 4_Executive_Insights.py
│
└── data/
    ├── policies.csv
    ├── adjusters.csv
    ├── claims.csv
    ├── payments.csv
    ├── claim_notes.csv
    ├── tasks.csv
    ├── documents.csv
    └── agent_events.csv
```

---

# Installation

## Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Run Streamlit

```bash
streamlit run app.py
```

---

# Recommended Demo Flow

1. Open README
2. Submit a claim in FNOL Intake
3. Review agent decisions in Agent Command Center
4. Review operational metrics in Claims Dashboard
5. Review executive metrics in Executive Insights

---

# Enterprise Migration Roadmap

| Prototype | Enterprise Version |
|---|---|
| Streamlit | Copilot Studio |
| Python Agents | Copilot Topics / Power Automate |
| CSV Files | Dataverse / SQL / SharePoint |
| Streamlit Dashboards | Power BI |
| Local Workflow | Enterprise APIs and Events |

---

# Disclaimer

This project uses synthetic data only.

No real customer or insurance data is included.

This prototype is intended for demonstration and architectural exploration purposes.
