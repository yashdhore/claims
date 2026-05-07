from agents.intake_agent import run_intake_agent
from agents.policy_agent import run_policy_agent
from agents.adjuster_agent import run_adjuster_agent
from agents.processing_agent import run_processing_agent
from agents.reporting_agent import run_reporting_agent


def run_claim_workflow(fnol_data: dict):

    claim_id = run_intake_agent(fnol_data)

    run_policy_agent(claim_id)

    run_adjuster_agent(claim_id)

    final_status = run_processing_agent(claim_id)

    reporting_output = run_reporting_agent(claim_id)

    return {
        "claim_id": claim_id,
        "final_status": final_status,
        "reporting_output": reporting_output
    }


if __name__ == "__main__":

    sample_fnol = {
        "policy_id": "POL00001",
        "customer_id": "CUST00001",
        "country": "USA",
        "state": "TX",
        "claim_date": "2026-05-06",
        "claim_type": "Collision",
        "loss_cause": "Rear-end accident",
        "claim_status": "New",
        "estimated_loss": 8500,
        "deductible": 500,
        "coverage_limit": 50000,
        "coverage_valid": True,
        "severity_score": 0,
        "fraud_risk_score": 0,
        "adjuster_id": ""
    }

    result = run_claim_workflow(sample_fnol)

    print(result)
