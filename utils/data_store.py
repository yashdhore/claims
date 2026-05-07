# utils/data_store.py
"""
CSV data access layer for the Claims Agent Prototype.

This module keeps all file I/O in one place so your Streamlit screens and
agent functions can read/write data without duplicating CSV logic.

Expected project structure:

claims-agent-prototype/
  data/
    policies.csv
    adjusters.csv
    claims.csv
    payments.csv
    claim_notes.csv
    tasks.csv
    documents.csv
    agent_events.csv

  utils/
    data_store.py
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd


# -------------------------------------------------------------------
# Paths
# -------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

FILES = {
    "policies": DATA_DIR / "policies.csv",
    "adjusters": DATA_DIR / "adjusters.csv",
    "claims": DATA_DIR / "claims.csv",
    "payments": DATA_DIR / "payments.csv",
    "claim_notes": DATA_DIR / "claim_notes.csv",
    "tasks": DATA_DIR / "tasks.csv",
    "documents": DATA_DIR / "documents.csv",
    "agent_events": DATA_DIR / "agent_events.csv",
}


# -------------------------------------------------------------------
# Generic helpers
# -------------------------------------------------------------------

def ensure_data_dir() -> None:
    """Ensure the data directory exists."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def read_csv(name: str) -> pd.DataFrame:
    """
    Read one CSV by logical name.

    Example:
        claims_df = read_csv("claims")
    """
    if name not in FILES:
        raise ValueError(f"Unknown CSV name: {name}. Valid names: {list(FILES.keys())}")

    path = FILES[name]

    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    return pd.read_csv(path)


def write_csv(name: str, df: pd.DataFrame) -> None:
    """
    Write one CSV by logical name.
    """
    if name not in FILES:
        raise ValueError(f"Unknown CSV name: {name}. Valid names: {list(FILES.keys())}")

    ensure_data_dir()
    df.to_csv(FILES[name], index=False)


def append_row(name: str, row: Dict[str, Any]) -> pd.DataFrame:
    """
    Append a row to a CSV and return the updated DataFrame.
    """
    df = read_csv(name)

    new_row_df = pd.DataFrame([row])
    updated_df = pd.concat([df, new_row_df], ignore_index=True)

    write_csv(name, updated_df)
    return updated_df


def now_ts() -> str:
    """Return current timestamp as a display-friendly string."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def generate_next_id(df: pd.DataFrame, id_column: str, prefix: str, width: int = 5) -> str:
    """
    Generate the next ID using an existing ID column.

    Example:
        CLM00001 -> CLM00002
        PAY00001 -> PAY00002
        EVT00001 -> EVT00002
    """
    if df.empty or id_column not in df.columns:
        return f"{prefix}{1:0{width}d}"

    existing_ids = df[id_column].dropna().astype(str)

    max_num = 0
    for value in existing_ids:
        if value.startswith(prefix):
            numeric_part = value.replace(prefix, "", 1)
            if numeric_part.isdigit():
                max_num = max(max_num, int(numeric_part))

    return f"{prefix}{max_num + 1:0{width}d}"


# -------------------------------------------------------------------
# Read helpers
# -------------------------------------------------------------------

def load_all_data() -> Dict[str, pd.DataFrame]:
    """
    Load all CSVs into a dictionary.

    Useful for dashboards.
    """
    return {name: read_csv(name) for name in FILES}


def get_policies() -> pd.DataFrame:
    return read_csv("policies")


def get_adjusters() -> pd.DataFrame:
    return read_csv("adjusters")


def get_claims() -> pd.DataFrame:
    return read_csv("claims")


def get_payments() -> pd.DataFrame:
    return read_csv("payments")


def get_claim_notes() -> pd.DataFrame:
    return read_csv("claim_notes")


def get_tasks() -> pd.DataFrame:
    return read_csv("tasks")


def get_documents() -> pd.DataFrame:
    return read_csv("documents")


def get_agent_events() -> pd.DataFrame:
    return read_csv("agent_events")


# -------------------------------------------------------------------
# Lookup helpers
# -------------------------------------------------------------------

def get_policy(policy_id: str) -> Optional[Dict[str, Any]]:
    policies = get_policies()
    match = policies[policies["policy_id"].astype(str) == str(policy_id)]

    if match.empty:
        return None

    return match.iloc[0].to_dict()


def get_claim(claim_id: str) -> Optional[Dict[str, Any]]:
    claims = get_claims()
    match = claims[claims["claim_id"].astype(str) == str(claim_id)]

    if match.empty:
        return None

    return match.iloc[0].to_dict()


def get_adjuster(adjuster_id: str) -> Optional[Dict[str, Any]]:
    adjusters = get_adjusters()
    match = adjusters[adjusters["adjuster_id"].astype(str) == str(adjuster_id)]

    if match.empty:
        return None

    return match.iloc[0].to_dict()


def get_claim_related_records(claim_id: str) -> Dict[str, pd.DataFrame]:
    """
    Return all records related to a single claim.
    Useful for Claim Detail / Agent Command Center screens.
    """
    claim_id = str(claim_id)

    return {
        "claim": pd.DataFrame([get_claim(claim_id)]) if get_claim(claim_id) else pd.DataFrame(),
        "payments": get_payments().query("claim_id == @claim_id"),
        "notes": get_claim_notes().query("claim_id == @claim_id"),
        "tasks": get_tasks().query("claim_id == @claim_id"),
        "documents": get_documents().query("claim_id == @claim_id"),
        "agent_events": get_agent_events().query("claim_id == @claim_id"),
    }


# -------------------------------------------------------------------
# Claim helpers
# -------------------------------------------------------------------

def create_claim(claim_data: Dict[str, Any]) -> str:
    """
    Add a new claim to claims.csv.

    The caller can provide claim fields from the FNOL form.
    This function generates claim_id if not provided.
    """
    claims = get_claims()

    if "claim_id" not in claim_data or not claim_data["claim_id"]:
        claim_data["claim_id"] = generate_next_id(claims, "claim_id", "CLM", 5)

    append_row("claims", claim_data)
    return claim_data["claim_id"]


def update_claim(claim_id: str, updates: Dict[str, Any]) -> pd.DataFrame:
    """
    Update one claim row in claims.csv.

    Example:
        update_claim("CLM00101", {"claim_status": "Approved"})
    """
    claims = get_claims()
    claim_id = str(claim_id)

    mask = claims["claim_id"].astype(str) == claim_id

    if not mask.any():
        raise ValueError(f"Claim not found: {claim_id}")

    for column, value in updates.items():
        if column not in claims.columns:
            claims[column] = None
        claims.loc[mask, column] = value

    write_csv("claims", claims)
    return claims


def update_claim_status(claim_id: str, status: str) -> pd.DataFrame:
    """Shortcut to update claim_status."""
    return update_claim(claim_id, {"claim_status": status})


# -------------------------------------------------------------------
# Agent event helpers
# -------------------------------------------------------------------

def log_agent_event(
    claim_id: str,
    agent_name: str,
    event_type: str,
    input_summary: str,
    decision: str,
    output_summary: str,
    next_agent: str,
    status: str = "Completed",
) -> str:
    """
    Append an event to agent_events.csv.

    This is the main audit trail for your agentic demo.
    """
    events = get_agent_events()

    event_id = generate_next_id(events, "event_id", "EVT", 5)

    row = {
        "event_id": event_id,
        "timestamp": now_ts(),
        "claim_id": claim_id,
        "agent_name": agent_name,
        "event_type": event_type,
        "input_summary": input_summary,
        "decision": decision,
        "output_summary": output_summary,
        "next_agent": next_agent,
        "status": status,
    }

    append_row("agent_events", row)
    return event_id


# -------------------------------------------------------------------
# Notes, tasks, documents, payments
# -------------------------------------------------------------------

def add_claim_note(
    claim_id: str,
    adjuster_id: str,
    note_text: str,
    note_date: Optional[str] = None,
) -> str:
    notes = get_claim_notes()

    note_id = generate_next_id(notes, "note_id", "NOTE", 5)

    row = {
        "note_id": note_id,
        "claim_id": claim_id,
        "adjuster_id": adjuster_id,
        "note_date": note_date or datetime.now().date().isoformat(),
        "note_text": note_text,
    }

    append_row("claim_notes", row)
    return note_id


def add_task(
    claim_id: str,
    assigned_to: str,
    task_type: str,
    task_status: str = "Open",
    due_date: Optional[str] = None,
) -> str:
    tasks = get_tasks()

    task_id = generate_next_id(tasks, "task_id", "TASK", 5)

    row = {
        "task_id": task_id,
        "claim_id": claim_id,
        "assigned_to": assigned_to,
        "task_type": task_type,
        "task_status": task_status,
        "due_date": due_date or datetime.now().date().isoformat(),
    }

    append_row("tasks", row)
    return task_id


def add_document(
    claim_id: str,
    document_type: str,
    file_name: str,
    uploaded_date: Optional[str] = None,
) -> str:
    documents = get_documents()

    document_id = generate_next_id(documents, "document_id", "DOC", 5)

    row = {
        "document_id": document_id,
        "claim_id": claim_id,
        "document_type": document_type,
        "uploaded_date": uploaded_date or datetime.now().date().isoformat(),
        "file_name": file_name,
    }

    append_row("documents", row)
    return document_id


def add_payment(
    claim_id: str,
    country: str,
    state: str,
    payment_amount: float,
    payment_status: str = "Pending",
    payment_method: str = "ACH",
    payment_date: Optional[str] = None,
) -> str:
    payments = get_payments()

    payment_id = generate_next_id(payments, "payment_id", "PAY", 5)

    row = {
        "payment_id": payment_id,
        "claim_id": claim_id,
        "country": country,
        "state": state,
        "payment_date": payment_date or datetime.now().date().isoformat(),
        "payment_amount": round(float(payment_amount), 2),
        "payment_status": payment_status,
        "payment_method": payment_method,
    }

    append_row("payments", row)
    return payment_id


# -------------------------------------------------------------------
# Dashboard helpers
# -------------------------------------------------------------------

def claims_summary() -> Dict[str, Any]:
    """
    Return common KPI metrics for dashboard cards.
    """
    claims = get_claims()
    payments = get_payments()

    total_claims = len(claims)
    open_claims = len(claims[claims["claim_status"].isin(["New", "Under Review"])])
    paid_claims = len(claims[claims["claim_status"].isin(["Paid", "Closed"])])

    high_fraud_claims = len(claims[claims["fraud_risk_score"] >= 75]) if "fraud_risk_score" in claims else 0
    high_severity_claims = len(claims[claims["severity_score"] >= 75]) if "severity_score" in claims else 0

    total_estimated_loss = float(claims["estimated_loss"].sum()) if "estimated_loss" in claims else 0.0
    total_paid = float(payments["payment_amount"].sum()) if not payments.empty and "payment_amount" in payments else 0.0

    return {
        "total_claims": total_claims,
        "open_claims": open_claims,
        "paid_claims": paid_claims,
        "high_fraud_claims": high_fraud_claims,
        "high_severity_claims": high_severity_claims,
        "total_estimated_loss": round(total_estimated_loss, 2),
        "total_paid": round(total_paid, 2),
    }


def claims_by_country() -> pd.DataFrame:
    claims = get_claims()

    if "country" not in claims.columns:
        return pd.DataFrame()

    return (
        claims.groupby("country", as_index=False)
        .agg(
            total_claims=("claim_id", "count"),
            avg_estimated_loss=("estimated_loss", "mean"),
            avg_fraud_risk=("fraud_risk_score", "mean"),
            avg_severity=("severity_score", "mean"),
        )
        .round(2)
    )


def claims_by_status() -> pd.DataFrame:
    claims = get_claims()

    return (
        claims.groupby("claim_status", as_index=False)
        .agg(total_claims=("claim_id", "count"))
        .sort_values("total_claims", ascending=False)
    )


# -------------------------------------------------------------------
# Validation helper
# -------------------------------------------------------------------

def validate_required_files() -> Dict[str, bool]:
    """
    Check whether all expected CSV files exist.
    """
    return {name: path.exists() for name, path in FILES.items()}


if __name__ == "__main__":
    print("Validating CSV files...")
    results = validate_required_files()

    for name, exists in results.items():
        print(f"{name}: {'OK' if exists else 'MISSING'}")

    if all(results.values()):
        print("\nAll required CSV files are present.")
        print("Claims summary:")
        print(claims_summary())
    else:
        print("\nSome files are missing. Check your data/ folder.")
