"""
agents/processing_agent.py

Cosmos DB write-path version of the Processing Agent.

This agent:
- reads the claim from Cosmos DB
- applies claim decision rules
- updates claim status in Cosmos DB
- creates a payment in Cosmos DB when approved
- logs a Processing Agent event in Cosmos DB
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from agents.data_access.cosmos_store import cosmos_store


def run_processing_agent(claim_id: str):
    """
    Processing Agent.

    Rules:
    1. If coverage is invalid, deny the claim.
    2. If fraud score is 85 or higher, escalate to Under Review.
    3. Otherwise, approve the claim and create a payment.
    """

    claim = cosmos_store.get_claim(claim_id)

    if not claim:
        raise ValueError(f"Claim not found: {claim_id}")

    coverage_valid = str(claim.get("coverage_valid", "")).lower() == "true"
    fraud_score = int(float(claim.get("fraud_risk_score", 0)))
    severity_score = int(float(claim.get("severity_score", 0)))
    estimated_loss = float(claim.get("estimated_loss", 0))
    deductible = float(claim.get("deductible", 0))
    coverage_limit = float(claim.get("coverage_limit", 0))

    decision_reason = ""
    rule_triggered = ""
    recommended_action = ""
    payment_amount = 0.0

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
        recommended_action = "Send the claim to a fraud investigator before payment is issued."

    else:
        final_status = "Approved"
        decision = "Claim approved"
        rule_triggered = "Coverage valid and fraud risk below threshold"

        payment_amount = max(
            0.0,
            min(estimated_loss, coverage_limit) - deductible,
        )

        decision_reason = (
            "The claim was approved because coverage was valid and fraud risk "
            "was below the escalation threshold."
        )
        recommended_action = (
            f"Issue payment of ${payment_amount:,.2f}, subject to final adjuster review."
        )

        payment_id = _generate_next_payment_id()

        payment_doc = {
            "id": payment_id,
            "payment_id": payment_id,
            "claim_id": claim_id,
            "country": claim.get("country", ""),
            "state": claim.get("state", ""),
            "payment_amount": payment_amount,
            "payment_status": "Pending",
            "payment_method": "ACH",
            "payment_date": datetime.now().date().isoformat(),
        }

        cosmos_store.get_container("payments").upsert_item(
            _make_json_safe_document(payment_doc)
        )

    claim_update = dict(claim)
    claim_update["id"] = claim_id
    claim_update["claim_id"] = claim_id
    claim_update["claim_status"] = final_status

    cosmos_store.update_claim(_make_json_safe_document(claim_update))

    output_summary = (
        f"Final Status={final_status}; "
        f"Rule Triggered={rule_triggered}; "
        f"Reason={decision_reason}; "
        f"Recommended Action={recommended_action}"
    )

    event_id = _generate_next_event_id()

    agent_event = {
        "id": event_id,
        "event_id": event_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "claim_id": claim_id,
        "agent_name": "Processing Agent",
        "event_type": "Claim Decision",
        "input_summary": (
            f"Coverage Valid={coverage_valid}; "
            f"Estimated Loss=${estimated_loss:,.2f}; "
            f"Deductible=${deductible:,.2f}; "
            f"Coverage Limit=${coverage_limit:,.2f}; "
            f"Fraud Score={fraud_score}; "
            f"Severity Score={severity_score}"
        ),
        "decision": decision,
        "output_summary": output_summary,
        "next_agent": "Reporting Agent",
        "status": "Completed",
    }

    cosmos_store.insert_agent_event(_make_json_safe_document(agent_event))

    return final_status


def _generate_next_event_id() -> str:
    """
    Generate next event ID from existing Cosmos DB agent_events documents.
    """

    try:
        existing_events = list(
            cosmos_store.get_container("agent_events").query_items(
                query="SELECT * FROM c",
                enable_cross_partition_query=True,
            )
        )
    except Exception:
        existing_events = []

    return _next_id_from_cosmos(existing_events, "event_id", "EVT", 5)


def _generate_next_payment_id() -> str:
    """
    Generate next payment ID from existing Cosmos DB payments documents.
    """

    try:
        existing_payments = list(
            cosmos_store.get_container("payments").query_items(
                query="SELECT * FROM c",
                enable_cross_partition_query=True,
            )
        )
    except Exception:
        existing_payments = []

    return _next_id_from_cosmos(existing_payments, "payment_id", "PAY", 5)


def _next_id_from_cosmos(
    existing_items: List[Dict[str, Any]],
    id_field: str,
    prefix: str,
    width: int,
) -> str:
    """
    Generate next ID by finding the max existing ID in Cosmos and incrementing it.
    """

    max_index = 0

    for item in existing_items:
        raw_id = item.get(id_field) or item.get("id")
        numeric = _parse_numeric_suffix(raw_id, prefix)

        if numeric is not None and numeric > max_index:
            max_index = numeric

    return f"{prefix}{max_index + 1:0{width}d}"


def _parse_numeric_suffix(value: Optional[str], prefix: str) -> Optional[int]:
    """
    Parse numeric suffix from a prefixed ID string.

    Example:
        PAY00024 -> 24
        EVT00037 -> 37
    """

    if not isinstance(value, str):
        return None

    if not value.startswith(prefix):
        return None

    suffix = value[len(prefix):]

    if suffix.isdigit():
        return int(suffix)

    return None


def _make_json_safe_document(document: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert document values into JSON-safe values before writing to Cosmos DB.
    """

    return {key: _make_json_safe(value) for key, value in document.items()}


def _make_json_safe(value: Any) -> Any:
    """
    Convert Pandas, NumPy, datetime, and date values into JSON-safe values.
    """

    if value is None:
        return None

    if hasattr(value, "item"):
        return value.item()

    if hasattr(value, "isoformat"):
        return value.isoformat()

    return value