from fastapi import APIRouter, Request
from server.db import get_conn_ctx
from server.identity import current_user
from server.errors import not_found
from server.models import Issue, IssueCreate, IssueUpdate
from server.repositories import issues as repo

router = APIRouter()


@router.post("/assets/{asset_id}/issues", response_model=Issue, status_code=201)
def create(asset_id: str, body: IssueCreate, request: Request):
    with get_conn_ctx() as conn:
        row = repo.create_issue(conn, asset_id, body.model_dump(exclude_none=True), current_user(request))
        conn.commit()
    return row


@router.get("/assets/{asset_id}/issues", response_model=list[Issue])
def list_for_asset(asset_id: str):
    with get_conn_ctx() as conn:
        return repo.list_issues(conn, asset_id)


@router.patch("/issues/{issue_id}", response_model=Issue)
def update(issue_id: str, body: IssueUpdate, request: Request):
    with get_conn_ctx() as conn:
        row = repo.update_issue(conn, issue_id, body.model_dump(exclude_none=True), current_user(request))
        conn.commit()
    if not row:
        raise not_found("issue")
    return row


@router.delete("/issues/{issue_id}")
def delete(issue_id: str):
    with get_conn_ctx() as conn:
        ok = repo.delete_issue(conn, issue_id)
        conn.commit()
    if not ok:
        raise not_found("issue")
    return {"deleted": True}
