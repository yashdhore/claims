from utils.data_store import (
    get_claim,
    update_claim,
    add_payment,
    log_agent_event,
)


def run_processing_agent(claim_id: str):
    """
    Processing Agent.

    Makes the final claim decision.

    Rules:
    1. If coverage is invalid, deny the claim.
    2. If fraud score is 85 or higher, escalate to Under Review.
    3. Otherwise, approve the claim and create a payment.
    """

    claim = get_claim(claim_id)

    if not claim:
        raise ValueError(f"Claim not found: {claim_id}")

    coverage_valid = str(claim["coverage_valid"]).lower() == "true"
    fraud_score = int(claim["fraud_risk_score"])
    severity_score = int(claim["severity_score"])
    estimated_loss = float(claim["estimated_loss"])
    deductible = float(claim["deductible"])
    coverage_limit = float(claim["coverage_limit"])

    decision_reason = ""
    rule_triggered = ""
    recommended_action = ""
    payment_amount = 0

    if not coverage_valid:
        final_status = "Denied"
        decision = "Claim denied"
        rule_triggered = "Coverage validation failed"
        decision_reason = (
            "The claim was denied because the policy coverage was not valid "
            "for the submitted claim date or the policy was not active."
        )
        recommended_action = (
            "Review the policy status, policy start date, policy end date, "
            "and submitted claim date."
        )

    elif fraud_score >= 85:
        final_status = "Under Review"
        decision = "Claim escalated"
        rule_triggered = "Fraud risk threshold exceeded"
        decision_reason = (
            f"The claim was escalated because the fraud risk score was {fraud_score}, "
            "which is at or above the threshold of 85."
        )
        recommended_action = (
            "Send the claim to a fraud investigator before payment is issued."
        )

    else:
        final_status = "Approved"
        decision = "Claim approved"
        rule_triggered = "Coverage valid and fraud risk below threshold"

        payment_amount = max(
            0,
            min(estimated_loss, coverage_limit) - deductible,
        )

        decision_reason = (
            "The claim was approved because coverage was valid and fraud risk "
            "was below the escalation threshold."
        )
        recommended_action = (
            f"Issue payment of ${payment_amount:,.2f}, subject to final adjuster review."
        )

        add_payment(
            claim_id=claim_id,
            country=claim["country"],
            state=claim["state"],
            payment_amount=payment_amount,
            payment_status="Pending",
            payment_method="ACH",
        )

    update_claim(
        claim_id,
        {
            "claim_status": final_status,
        },
    )

    output_summary = (
        f"Final Status={final_status}; "
        f"Rule Triggered={rule_triggered}; "
        f"Reason={decision_reason}; "
        f"Recommended Action={recommended_action}"
    )

    log_agent_event(
        claim_id=claim_id,
        agent_name="Processing Agent",
        event_type="Claim Decision",
        input_summary=(
            f"Coverage Valid={coverage_valid}; "
            f"Estimated Loss=${estimated_loss:,.2f}; "
            f"Deductible=${deductible:,.2f}; "
            f"Coverage Limit=${coverage_limit:,.2f}; "
            f"Fraud Score={fraud_score}; "
            f"Severity Score={severity_score}"
        ),
        decision=decision,
        output_summary=output_summary,
        next_agent="Reporting Agent",
        status="Completed",
    )

    return final_status