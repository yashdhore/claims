from utils.data_store import (
    claims_summary,
    claims_by_country,
    claims_by_status,
    log_agent_event
)

def run_reporting_agent(claim_id: str):

    summary = claims_summary()

    log_agent_event(
        claim_id=claim_id,
        agent_name="Reporting Agent",
        event_type="Dashboard Refresh",
        input_summary="Updated operational dashboards",
        decision="Insights recalculated",
        output_summary=(
            f"Total Claims={summary['total_claims']}, "
            f"Open Claims={summary['open_claims']}"
        ),
        next_agent="Complete",
        status="Completed"
    )

    return {
        "summary": summary,
        "country_metrics": claims_by_country().to_dict(orient="records"),
        "status_metrics": claims_by_status().to_dict(orient="records")
    }
