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

from datetime import datetime
from typing import Any, Dict, List, Optional
import random

from agents.data_access.cosmos_store import cosmos_store


def run_adjuster_agent(claim_id: str) -> Dict[str, Any]:
    """
    Adjuster Agent - Cosmos DB version.

    Reads:
    - claim from Cosmos DB claims container
    - adjusters from Cosmos DB adjusters container

    Updates:
    - assigned adjuster
    - severity score
    - fraud risk score
    - claim status

    Writes:
    - task document into tasks container
    - Adjuster Agent event into agent_events container
    """

    claim = cosmos_store.get_claim(claim_id)

    if not claim:
        raise ValueError(f"Claim not found: {claim_id}")

    adjusters = _get_all_adjusters_from_cosmos()

    if not adjusters:
        raise ValueError("No adjusters found in Cosmos DB adjusters container")

    assigned_adjuster = _select_adjuster_for_claim(claim, adjusters)

    estimated_loss = float(claim.get("estimated_loss", 0))

    severity_score = min(
        100,
        int((estimated_loss / 30000) * 100) + random.randint(0, 10),
    )

    fraud_risk_score = random.randint(10, 90)

    if estimated_loss > 20000:
        fraud_risk_score += 10

    fraud_risk_score = min(100, fraud_risk_score)

    claim_update = dict(claim)
    claim_update["id"] = claim_id
    claim_update["claim_id"] = claim_id
    claim_update["adjuster_id"] = assigned_adjuster["adjuster_id"]
    claim_update["severity_score"] = severity_score
    claim_update["fraud_risk_score"] = fraud_risk_score
    claim_update["claim_status"] = "Under Review"

    cosmos_store.update_claim(_make_json_safe_document(claim_update))

    task_id = _generate_next_task_id()

    task_doc = {
        "id": task_id,
        "task_id": task_id,
        "claim_id": claim_id,
        "assigned_to": assigned_adjuster["adjuster_id"],
        "task_type": "Review claim and estimate damages",
        "task_status": "Open",
        "due_date": datetime.now().date().isoformat(),
    }

    cosmos_store.get_container("tasks").upsert_item(_make_json_safe_document(task_doc))

    event_id = _generate_next_event_id()

    agent_event = {
        "id": event_id,
        "event_id": event_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "claim_id": claim_id,
        "agent_name": "Adjuster Agent",
        "event_type": "Triage and Assignment",
        "input_summary": "Calculated severity and fraud risk",
        "decision": f"Assigned to {assigned_adjuster['adjuster_id']}",
        "output_summary": f"Severity={severity_score}, Fraud={fraud_risk_score}",
        "next_agent": "Processing Agent",
        "status": "Completed",
    }

    cosmos_store.insert_agent_event(_make_json_safe_document(agent_event))

    return {
        "adjuster_id": assigned_adjuster["adjuster_id"],
        "severity_score": severity_score,
        "fraud_risk_score": fraud_risk_score,
    }


def _get_all_adjusters_from_cosmos() -> List[Dict[str, Any]]:
    """
    Retrieve all adjusters from the adjusters container.
    """

    container = cosmos_store.get_container("adjusters")

    items = list(
        container.query_items(
            query="SELECT * FROM c",
            enable_cross_partition_query=True,
        )
    )

    return items


def _select_adjuster_for_claim(
    claim: Dict[str, Any],
    adjusters: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Select a regional adjuster when possible.

    Matching logic:
    - Same country
    - Same state

    If no regional adjuster exists, select any adjuster.
    """

    claim_country = str(claim.get("country", ""))
    claim_state = str(claim.get("state", ""))

    regional_adjusters = [
        adjuster
        for adjuster in adjusters
        if str(adjuster.get("country", "")) == claim_country
        and str(adjuster.get("state", "")) == claim_state
    ]

    if regional_adjusters:
        return random.choice(regional_adjusters)

    return random.choice(adjusters)


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


def _generate_next_task_id() -> str:
    """
    Generate next task ID from existing Cosmos DB tasks documents.
    """

    try:
        existing_tasks = list(
            cosmos_store.get_container("tasks").query_items(
                query="SELECT * FROM c",
                enable_cross_partition_query=True,
            )
        )
    except Exception:
        existing_tasks = []

    return _next_id_from_cosmos(existing_tasks, "task_id", "TASK", 5)


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
        TASK00213 -> 213
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