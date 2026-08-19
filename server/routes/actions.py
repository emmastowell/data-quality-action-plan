from fastapi import APIRouter, Request
from server.db import get_conn_ctx
from server.identity import current_user
from server.errors import not_found
from server.models import Action, ActionCreate, ActionUpdate
from server.repositories import actions as repo

router = APIRouter()


@router.post("/assets/{asset_id}/actions", response_model=Action, status_code=201)
def create(asset_id: str, body: ActionCreate, request: Request):
    with get_conn_ctx() as conn:
        row = repo.create_action(conn, asset_id, body.model_dump(exclude_none=True), current_user(request))
        conn.commit()
    return row


@router.get("/assets/{asset_id}/actions", response_model=list[Action])
def list_for_asset(asset_id: str):
    with get_conn_ctx() as conn:
        return repo.list_actions(conn, asset_id)


@router.patch("/actions/{action_id}", response_model=Action)
def update(action_id: str, body: ActionUpdate, request: Request):
    with get_conn_ctx() as conn:
        row = repo.update_action(conn, action_id, body.model_dump(exclude_none=True), current_user(request))
        conn.commit()
    if not row:
        raise not_found("action")
    return row


@router.delete("/actions/{action_id}")
def delete(action_id: str):
    with get_conn_ctx() as conn:
        ok = repo.delete_action(conn, action_id)
        conn.commit()
    if not ok:
        raise not_found("action")
    return {"deleted": True}
