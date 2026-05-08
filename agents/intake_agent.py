"""
agents/intake_agent.py

Cosmos DB write-path version of the Intake Agent.

This agent creates a new FNOL claim in Azure Cosmos DB and logs the
Intake Agent event into the agent_events container.
"""

from datetime import datetime
from typing import Any, Dict, List

from agents.data_access.cosmos_store import cosmos_store


def run_intake_agent(fnol_data: dict) -> str:
    """
    Creates a new FNOL claim and writes it directly to Cosmos DB.
    """

    existing_claims = cosmos_store.get_all_claims()
    claim_id = _next_id_from_cosmos(existing_claims, "claim_id", "CLM", 5)

    cosmos_claim = _build_cosmos_claim(fnol_data, claim_id)
    cosmos_store.insert_claim(cosmos_claim)

    try:
        existing_events = list(
            cosmos_store.get_container("agent_events").query_items(
                query="SELECT * FROM c",
                enable_cross_partition_query=True,
            )
        )
    except Exception:
        existing_events = []

    event_id = _next_id_from_cosmos(existing_events, "event_id", "EVT", 5)

    cosmos_event = _build_cosmos_event(claim_id, event_id)
    cosmos_store.insert_agent_event(cosmos_event)

    return claim_id


def _next_id_from_cosmos(
    existing_items: List[Dict[str, Any]],
    id_field: str,
    prefix: str,
    width: int = 5,
) -> str:
    """
    Generate the next business ID from existing Cosmos documents.
    """

    max_number = 0

    for item in existing_items:
        value = str(item.get(id_field, ""))

        if value.startswith(prefix):
            numeric_part = value.replace(prefix, "", 1)

            if numeric_part.isdigit():
                max_number = max(max_number, int(numeric_part))

    return f"{prefix}{max_number + 1:0{width}d}"


def _build_cosmos_claim(fnol_data: Dict[str, Any], claim_id: str) -> Dict[str, Any]:
    """
    Build the claim document to insert into the Cosmos claims container.

    Cosmos DB requires JSON-serializable values.
    Streamlit and Pandas values may contain numpy, pandas, datetime, or date
    objects, so this function converts all values into JSON-safe Python types.
    """

    claim_doc = {}

    for key, value in fnol_data.items():
        claim_doc[key] = _make_json_safe(value)

    claim_doc["id"] = claim_id
    claim_doc["claim_id"] = claim_id

    return claim_doc


def _build_cosmos_event(claim_id: str, event_id: str) -> Dict[str, Any]:
    """
    Build the Intake Agent event document to insert into the Cosmos
    agent_events container.
    """

    return {
        "id": event_id,
        "event_id": event_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "claim_id": claim_id,
        "agent_name": "Intake Agent",
        "event_type": "FNOL Intake",
        "input_summary": "Customer submitted FNOL",
        "decision": "Claim created successfully",
        "output_summary": f"Claim {claim_id} created in Cosmos DB",
        "next_agent": "Policy Verification Agent",
        "status": "Completed",
    }


def _make_json_safe(value: Any) -> Any:
    """
    Convert common Pandas, NumPy, datetime, and date values into JSON-safe values.
    """

    if value is None:
        return None

    if hasattr(value, "item"):
        return value.item()

    if hasattr(value, "isoformat"):
        return value.isoformat()

    return value