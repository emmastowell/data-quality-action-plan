from fastapi import APIRouter, Request
from server.db import get_conn_ctx
from server.identity import current_user
from server.errors import not_found
from server.models import Asset, AssetCreate, AssetUpdate
from server.repositories import assets as repo

router = APIRouter()


@router.post("/assets", response_model=Asset, status_code=201)
def create(body: AssetCreate, request: Request):
    user = current_user(request)
    with get_conn_ctx() as conn:
        row = repo.create_asset(conn, body.model_dump(exclude_none=True), user)
        conn.commit()
    return row


@router.get("/assets", response_model=list[Asset])
def list_all():
    with get_conn_ctx() as conn:
        return repo.list_assets(conn)


@router.get("/assets/{asset_id}", response_model=Asset)
def get_one(asset_id: str):
    with get_conn_ctx() as conn:
        row = repo.get_asset(conn, asset_id)
    if not row:
        raise not_found("asset")
    return row


@router.patch("/assets/{asset_id}", response_model=Asset)
def update(asset_id: str, body: AssetUpdate, request: Request):
    user = current_user(request)
    with get_conn_ctx() as conn:
        row = repo.update_asset(conn, asset_id, body.model_dump(exclude_none=True), user)
        conn.commit()
    if not row:
        raise not_found("asset")
    return row


@router.delete("/assets/{asset_id}", response_model=Asset)
def archive(asset_id: str, request: Request):
    user = current_user(request)
    with get_conn_ctx() as conn:
        row = repo.archive_asset(conn, asset_id, user)
        conn.commit()
    if not row:
        raise not_found("asset")
    return row
