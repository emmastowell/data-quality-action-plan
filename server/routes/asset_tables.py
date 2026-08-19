from fastapi import APIRouter, Request
from server.db import get_conn_ctx
from server.identity import current_user
from server.errors import not_found
from server.models import AssetTable, AssetTableCreate
from server.repositories import asset_tables as repo

router = APIRouter()


@router.get("/assets/{asset_id}/tables", response_model=list[AssetTable])
def list_tables(asset_id: str):
    with get_conn_ctx() as conn:
        return repo.list_asset_tables(conn, asset_id)


@router.post("/assets/{asset_id}/tables", response_model=AssetTable, status_code=201)
def add_table(asset_id: str, body: AssetTableCreate, request: Request):
    user = current_user(request)
    with get_conn_ctx() as conn:
        row = repo.create_asset_table(conn, asset_id, body.model_dump(), user)
        conn.commit()
    return row


@router.delete("/asset-tables/{table_id}")
def remove_table(table_id: str):
    with get_conn_ctx() as conn:
        ok = repo.delete_asset_table(conn, table_id)
        conn.commit()
    if not ok:
        raise not_found("asset table")
    return {"deleted": True}
