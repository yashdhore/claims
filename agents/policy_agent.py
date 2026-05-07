import pandas as pd

from utils.data_store import (
    get_claim,
    get_policy,
    update_claim,
    log_agent_event,
)


def run_policy_agent(claim_id: str) -> bool:
    """
    Policy Verification Agent.

    Checks whether the selected policy is valid for the submitted claim.

    Rules:
    1. Policy must exist.
    2. Policy status must be Active.
    3. Claim date must be on or after policy start date.
    4. Claim date must be on or before policy end date.
    """

    claim = get_claim(claim_id)

    if not claim:
        raise ValueError(f"Claim not found: {claim_id}")

    policy = get_policy(claim["policy_id"])

    if not policy:
        raise ValueError(f"Policy not found: {claim['policy_id']}")

    claim_date = pd.to_datetime(claim["claim_date"]).date()
    start_date = pd.to_datetime(policy["policy_start_date"]).date()
    end_date = pd.to_datetime(policy["policy_end_date"]).date()

    policy_active = policy["policy_status"] == "Active"
    claim_after_start = claim_date >= start_date
    claim_before_end = claim_date <= end_date

    coverage_valid = policy_active and claim_after_start and claim_before_end

    failed_reasons = []

    if not policy_active:
        failed_reasons.append(
            f"Policy status is {policy['policy_status']}, not Active"
        )

    if not claim_after_start:
        failed_reasons.append(
            f"Claim date {claim_date} is before policy start date {start_date}"
        )

    if not claim_before_end:
        failed_reasons.append(
            f"Claim date {claim_date} is after policy end date {end_date}"
        )

    if coverage_valid:
        decision = "Coverage Valid"
        output_summary = (
            f"Coverage approved. Policy is active and claim date {claim_date} "
            f"is within policy period {start_date} to {end_date}."
        )
    else:
        decision = "Coverage Invalid"
        output_summary = "Coverage failed because: " + "; ".join(failed_reasons)

    update_claim(
        claim_id,
        {
            "coverage_valid": coverage_valid,
            "coverage_limit": policy["coverage_limit"],
            "deductible": policy["deductible"],
        },
    )

    log_agent_event(
        claim_id=claim_id,
        agent_name="Policy Verification Agent",
        event_type="Coverage Check",
        input_summary=(
            f"Policy ID={policy['policy_id']}; "
            f"Policy Status={policy['policy_status']}; "
            f"Policy Start={start_date}; "
            f"Policy End={end_date}; "
            f"Claim Date={claim_date}; "
            f"Deductible=${float(policy['deductible']):,.2f}; "
            f"Coverage Limit=${float(policy['coverage_limit']):,.2f}"
        ),
        decision=decision,
        output_summary=output_summary,
        next_agent="Adjuster Agent",
        status="Completed",
    )

    return coverage_valid