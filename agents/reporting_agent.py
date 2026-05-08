"""
agents/reporting_agent.py

Cosmos DB version of the Reporting Agent.

This agent:
- reads claims from Cosmos DB
- reads payments from Cosmos DB
- calculates operational summary metrics
- calculates country-level metrics
- calculates status-level metrics
- logs a Reporting Agent event into Cosmos DB
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from agents.data_access.cosmos_store import cosmos_store


def run_reporting_agent(claim_id: str):
    """
    Reporting Agent.

    Reads Cosmos DB data and returns dashboard-style metrics.
    """

    claims_df = _load_container_as_dataframe("claims")
    payments_df = _load_container_as_dataframe("payments")

    summary = _claims_summary(claims_df, payments_df)
    country_metrics = _claims_by_country(claims_df)
    status_metrics = _claims_by_status(claims_df)

    event_id = _generate_next_event_id()

    agent_event = {
        "id": event_id,
        "event_id": event_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "claim_id": claim_id,
        "agent_name": "Reporting Agent",
        "event_type": "Dashboard Refresh",
        "input_summary": "Updated operational dashboards from Cosmos DB",
        "decision": "Insights recalculated",
        "output_summary": (
            f"Total Claims={summary['total_claims']}, "
            f"Open Claims={summary['open_claims']}"
        ),
        "next_agent": "Complete",
        "status": "Completed",
    }

    cosmos_store.insert_agent_event(_make_json_safe_document(agent_event))

    return {
        "summary": summary,
        "country_metrics": country_metrics.to_dict(orient="records"),
        "status_metrics": status_metrics.to_dict(orient="records"),
    }


def _load_container_as_dataframe(container_name: str) -> pd.DataFrame:
    """
    Load all documents from a Cosmos DB container into a pandas DataFrame.
    """

    try:
        container = cosmos_store.get_container(container_name)

        items = list(
            container.query_items(
                query="SELECT * FROM c",
                enable_cross_partition_query=True,
            )
        )

        return pd.DataFrame(items)

    except Exception:
        return pd.DataFrame()


def _claims_summary(claims_df: pd.DataFrame, payments_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate operational claims summary metrics from Cosmos DB data.
    """

    if claims_df.empty:
        return {
            "total_claims": 0,
            "open_claims": 0,
            "paid_claims": 0,
            "high_fraud_claims": 0,
            "high_severity_claims": 0,
            "total_estimated_loss": 0.0,
            "total_paid": 0.0,
        }

    claims_df = claims_df.copy()

    if "claim_status" not in claims_df.columns:
        claims_df["claim_status"] = "Unknown"

    claims_df["claim_status"] = claims_df["claim_status"].astype(str)

    claims_df["estimated_loss"] = pd.to_numeric(
        claims_df.get("estimated_loss", 0),
        errors="coerce",
    ).fillna(0)

    claims_df["fraud_risk_score"] = pd.to_numeric(
        claims_df.get("fraud_risk_score", 0),
        errors="coerce",
    ).fillna(0)

    claims_df["severity_score"] = pd.to_numeric(
        claims_df.get("severity_score", 0),
        errors="coerce",
    ).fillna(0)

    paid_claims = claims_df["claim_status"].str.lower().isin(
        ["paid", "closed", "approved"]
    ).sum()

    open_claims = claims_df["claim_status"].str.lower().isin(
        ["new", "under review", "open", "pending", "in progress", "in review"]
    ).sum()

    total_paid = 0.0

    if not payments_df.empty and "payment_amount" in payments_df.columns:
        total_paid = pd.to_numeric(
            payments_df["payment_amount"],
            errors="coerce",
        ).fillna(0).sum()

    return {
        "total_claims": int(len(claims_df)),
        "open_claims": int(open_claims),
        "paid_claims": int(paid_claims),
        "high_fraud_claims": int((claims_df["fraud_risk_score"] > 75).sum()),
        "high_severity_claims": int((claims_df["severity_score"] > 75).sum()),
        "total_estimated_loss": float(claims_df["estimated_loss"].sum()),
        "total_paid": float(total_paid),
    }


def _claims_by_country(claims_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate claim metrics grouped by country.
    """

    if claims_df.empty or "country" not in claims_df.columns:
        return pd.DataFrame(
            columns=[
                "country",
                "total_claims",
                "avg_estimated_loss",
                "avg_fraud_risk",
                "avg_severity",
            ]
        )

    claims_df = claims_df.copy()

    claims_df["estimated_loss"] = pd.to_numeric(
        claims_df.get("estimated_loss", 0),
        errors="coerce",
    ).fillna(0)

    claims_df["fraud_risk_score"] = pd.to_numeric(
        claims_df.get("fraud_risk_score", 0),
        errors="coerce",
    ).fillna(0)

    claims_df["severity_score"] = pd.to_numeric(
        claims_df.get("severity_score", 0),
        errors="coerce",
    ).fillna(0)

    grouped = (
        claims_df.groupby("country")
        .agg(
            total_claims=("claim_id", "count"),
            avg_estimated_loss=("estimated_loss", "mean"),
            avg_fraud_risk=("fraud_risk_score", "mean"),
            avg_severity=("severity_score", "mean"),
        )
        .reset_index()
    )

    grouped["avg_estimated_loss"] = grouped["avg_estimated_loss"].round(2)
    grouped["avg_fraud_risk"] = grouped["avg_fraud_risk"].round(2)
    grouped["avg_severity"] = grouped["avg_severity"].round(2)

    return grouped


def _claims_by_status(claims_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate claim counts grouped by claim status.
    """

    if claims_df.empty:
        return pd.DataFrame(columns=["claim_status", "total_claims"])

    claims_df = claims_df.copy()

    if "claim_status" not in claims_df.columns:
        claims_df["claim_status"] = "Unknown"

    grouped = (
        claims_df.groupby("claim_status")
        .size()
        .reset_index(name="total_claims")
        .sort_values("total_claims", ascending=False)
    )

    return grouped


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