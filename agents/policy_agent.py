import pandas as pd
from datetime import datetime
from typing import Any, Dict, List, Optional

from agents.data_access.cosmos_store import cosmos_store


def run_policy_agent(claim_id: str) -> bool:
    """
    Policy Verification Agent - Cosmos DB version.

    Reads:
    - claim from Cosmos DB claims container
    - policy from Cosmos DB policies container

    Updates:
    - coverage_valid
    - deductible
    - coverage_limit

    Writes:
    - Policy Verification Agent event into agent_events container
    """

    claim = cosmos_store.get_claim(claim_id)

    if not claim:
        raise ValueError(f"Claim not found: {claim_id}")

    policy = _get_policy_from_cosmos(claim["policy_id"])

    if not policy:
        raise ValueError(f"Policy not found: {claim['policy_id']}")

    claim_date = pd.to_datetime(claim["claim_date"]).date()
    start_date = pd.to_datetime(policy["policy_start_date"]).date()
    end_date = pd.to_datetime(policy["policy_end_date"]).date()

    policy_active = str(policy["policy_status"]) == "Active"
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

    claim_update = dict(claim)
    claim_update["id"] = claim_id
    claim_update["claim_id"] = claim_id
    claim_update["coverage_valid"] = coverage_valid
    claim_update["coverage_limit"] = _make_json_safe(policy["coverage_limit"])
    claim_update["deductible"] = _make_json_safe(policy["deductible"])

    cosmos_store.update_claim(claim_update)

    event_id = _generate_next_event_id()

    agent_event = {
        "id": event_id,
        "event_id": event_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "claim_id": claim_id,
        "agent_name": "Policy Verification Agent",
        "event_type": "Coverage Check",
        "input_summary": (
            f"Policy ID={policy['policy_id']}; "
            f"Policy Status={policy['policy_status']}; "
            f"Policy Start={start_date}; "
            f"Policy End={end_date}; "
            f"Claim Date={claim_date}; "
            f"Deductible=${float(policy['deductible']):,.2f}; "
            f"Coverage Limit=${float(policy['coverage_limit']):,.2f}"
        ),
        "decision": decision,
        "output_summary": output_summary,
        "next_agent": "Adjuster Agent",
        "status": "Completed",
    }

    cosmos_store.insert_agent_event(agent_event)

    return coverage_valid


def _get_policy_from_cosmos(policy_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve one policy from the policies container.
    """

    container = cosmos_store.get_container("policies")

    query = "SELECT * FROM c WHERE c.policy_id = @policy_id"
    parameters = [{"name": "@policy_id", "value": policy_id}]

    items = list(
        container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True,
        )
    )

    return items[0] if items else None


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