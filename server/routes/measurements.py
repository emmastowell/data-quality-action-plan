from fastapi import APIRouter, Request
from server.db import get_conn_ctx
from server.identity import current_user
from server.errors import AppError, not_found
from server.models import Measurement, MeasurementCreate
from server.providers import get_provider
from server.repositories import measurements as repo
from server.repositories.assets import get_asset
from server.repositories.rules import get_rule, list_rules

router = APIRouter()


@router.post("/rules/{rule_id}/measurements", response_model=Measurement, status_code=201)
def record(rule_id: str, body: MeasurementCreate, request: Request):
    with get_conn_ctx() as conn:
        rule = get_rule(conn, rule_id)
        if not rule:
            raise not_found("rule")
        m = get_provider().measure(rule, body.model_dump(exclude_none=True))
        row = repo.add_measurement(conn, rule_id, m, current_user(request))
        conn.commit()
    return row


@router.get("/rules/{rule_id}/measurements", response_model=list[Measurement])
def list_for_rule(rule_id: str):
    with get_conn_ctx() as conn:
        return repo.list_measurements(conn, rule_id)


@router.post("/rules/{rule_id}/measure/run", response_model=Measurement)
def run_measure(rule_id: str, request: Request):
    """Run the warehouse SQL for a single rule and record the result immediately."""
    with get_conn_ctx() as conn:
        rule = get_rule(conn, rule_id)
        if not rule:
            raise not_found("rule")
        # Fix #6: treat whitespace-only SQL as absent
        if not (rule.get("measurement_sql") or "").strip():
            raise AppError("no_measurement_sql", "rule has no measurement SQL", 400)
        m = get_provider("warehouse").measure(rule, {})
        row = repo.add_measurement(conn, rule_id, m, current_user(request))
        conn.commit()
    return row


@router.post("/assets/{asset_id}/measure/run-all")
def run_all_measures(asset_id: str, request: Request):
    """Run warehouse SQL for every rule on the asset that has measurement_sql set.

    Each rule is wrapped in a savepoint so a DB error on one rule cannot
    poison the batch — remaining rules still run and commit cleanly.
    Failures are reported per-rule; the endpoint always returns 200 unless
    the asset itself doesn't exist.

    Returns {"results": [{rule_id, name, score} | {rule_id, name, error}, ...]}.
    """
    user = current_user(request)
    provider = get_provider("warehouse")
    results = []

    with get_conn_ctx() as conn:
        # Fix #5: 404 if asset doesn't exist, consistent with other endpoints
        if not get_asset(conn, asset_id):
            raise not_found("asset")

        # Fix #6: filter out blank/whitespace-only SQL alongside None
        rules = [r for r in list_rules(conn, asset_id)
                 if (r.get("measurement_sql") or "").strip()]

        for rule in rules:
            rid = rule["id"]
            name = rule["name"]
            try:
                # Fix #3: savepoint per rule so a DB error can't poison siblings
                with conn.transaction():
                    m = provider.measure(rule, {})
                    repo.add_measurement(conn, rid, m, user)
                results.append({"rule_id": rid, "name": name, "score": m.score})
            except Exception as exc:
                results.append({"rule_id": rid, "name": name, "error": str(exc)})

        conn.commit()

    return {"results": results}
