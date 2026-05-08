"""
NOTE:
The current severity and fraud-risk scoring logic is intentionally implemented
as a lightweight rule-based simulation model for rapid prototyping purposes.

The goal of this prototype is to demonstrate:

- Agent orchestration
- Workflow automation
- Explainable decisioning
- Operational routing
- Auditability
- Executive visibility

rather than production-grade predictive analytics.

Current Severity Logic:
- Primarily based on estimated claim loss amount
- Includes minor randomized variation for simulation realism
- Produces a normalized score between 0 and 100

Current Fraud Logic:
- Uses simulated fraud-risk scoring with threshold-based adjustments
- Higher estimated claim amounts increase fraud-risk likelihood
- Produces a normalized score between 0 and 100

Future Enterprise Evolution:
The scoring framework can later be replaced with enterprise-grade
machine learning or predictive analytics models using:

- Historical claims data
- Fraud detection models
- Behavioral analytics
- Geospatial analysis
- Network analysis
- Claim pattern recognition
- Real-time external data sources

without changing the overall workflow orchestration architecture.
"""

import random

from utils.data_store import (
    get_claim,
    get_adjusters,
    update_claim,
    add_task,
    log_agent_event
)

def run_adjuster_agent(claim_id: str):

    claim = get_claim(claim_id)

    if not claim:
        raise ValueError(f"Claim not found: {claim_id}")

    adjusters = get_adjusters()

    regional_adjusters = adjusters[
        (adjusters["country"] == claim["country"]) &
        (adjusters["state"] == claim["state"])
    ]

    if len(regional_adjusters) > 0:
        assigned_adjuster = regional_adjusters.sample(1).iloc[0]
    else:
        assigned_adjuster = adjusters.sample(1).iloc[0]

    estimated_loss = float(claim["estimated_loss"])

    severity_score = min(
        100,
        int((estimated_loss / 30000) * 100) + random.randint(0, 10)
    )

    fraud_risk_score = random.randint(10, 90)

    if estimated_loss > 20000:
        fraud_risk_score += 10

    fraud_risk_score = min(100, fraud_risk_score)

    update_claim(
        claim_id,
        {
            "adjuster_id": assigned_adjuster["adjuster_id"],
            "severity_score": severity_score,
            "fraud_risk_score": fraud_risk_score,
            "claim_status": "Under Review"
        }
    )

    add_task(
        claim_id=claim_id,
        assigned_to=assigned_adjuster["adjuster_id"],
        task_type="Review claim and estimate damages",
        task_status="Open"
    )

    log_agent_event(
        claim_id=claim_id,
        agent_name="Adjuster Agent",
        event_type="Triage and Assignment",
        input_summary="Calculated severity and fraud risk",
        decision=f"Assigned to {assigned_adjuster['adjuster_id']}",
        output_summary=f"Severity={severity_score}, Fraud={fraud_risk_score}",
        next_agent="Processing Agent",
        status="Completed"
    )

    return {
        "adjuster_id": assigned_adjuster["adjuster_id"],
        "severity_score": severity_score,
        "fraud_risk_score": fraud_risk_score
    }

