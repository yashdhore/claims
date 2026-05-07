from utils.data_store import create_claim, log_agent_event

def run_intake_agent(fnol_data: dict) -> str:
    """
    Creates a claim from FNOL input.
    """

    claim_id = create_claim(fnol_data)

    log_agent_event(
        claim_id=claim_id,
        agent_name="Intake Agent",
        event_type="FNOL Intake",
        input_summary="Customer submitted FNOL",
        decision="Claim created successfully",
        output_summary=f"Claim {claim_id} created",
        next_agent="Policy Verification Agent",
        status="Completed"
    )

    return claim_id

