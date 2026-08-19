from fastapi import APIRouter, Request
from server.db import get_conn_ctx
from server.identity import current_user
from server.errors import not_found
from server.models import Rule, RuleCreate, RuleUpdate
from server.repositories import rules as repo

router = APIRouter()


@router.post("/assets/{asset_id}/rules", response_model=Rule, status_code=201)
def create(asset_id: str, body: RuleCreate, request: Request):
    with get_conn_ctx() as conn:
        row = repo.create_rule(conn, asset_id, body.model_dump(exclude_none=True), current_user(request))
        conn.commit()
    return row


@router.get("/assets/{asset_id}/rules", response_model=list[Rule])
def list_for_asset(asset_id: str):
    with get_conn_ctx() as conn:
        return repo.list_rules(conn, asset_id)


@router.patch("/rules/{rule_id}", response_model=Rule)
def update(rule_id: str, body: RuleUpdate, request: Request):
    with get_conn_ctx() as conn:
        row = repo.update_rule(conn, rule_id, body.model_dump(exclude_none=True), current_user(request))
        conn.commit()
    if not row:
        raise not_found("rule")
    return row


@router.delete("/rules/{rule_id}")
def delete(rule_id: str):
    with get_conn_ctx() as conn:
        ok = repo.delete_rule(conn, rule_id)
        conn.commit()
    if not ok:
        raise not_found("rule")
    return {"deleted": True}
