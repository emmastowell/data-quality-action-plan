import csv
import io
from fastapi import APIRouter, Request
from fastapi.responses import Response
from pydantic import BaseModel

from server.db import get_conn_ctx, fetch_one
from server.errors import AppError, not_found
from server.identity import current_user
from server.repositories import export as repo

router = APIRouter()


class StepStatusBody(BaseModel):
    done: bool


@router.get("/assets/{asset_id}/journey")
def get_journey(asset_id: str):
    with get_conn_ctx() as conn:
        return repo.journey(conn, asset_id)


@router.put("/assets/{asset_id}/journey/{item_key}")
def put_journey_item(asset_id: str, item_key: str, body: StepStatusBody, request: Request):
    # Validate item_key
    if item_key not in repo.VALID_KEYS:
        raise AppError("invalid_item", "unknown journey item", 422)

    with get_conn_ctx() as conn:
        # 404 if asset doesn't exist
        row = fetch_one(conn, "SELECT id FROM data_assets WHERE id = %s", (asset_id,))
        if not row:
            raise not_found("asset")

        repo.set_step_status(conn, asset_id, item_key, body.done, current_user(request))
        conn.commit()
        return repo.journey(conn, asset_id)


@router.get("/assets/{asset_id}/export")
def export(asset_id: str, format: str = "json"):
    with get_conn_ctx() as conn:
        rows = repo.plan_rows(conn, asset_id)
    if format == "csv":
        buf = io.StringIO()
        fieldnames = ["asset", "dimension", "rule", "target_threshold", "unit", "latest_score", "linked_issues"]
        w = csv.DictWriter(buf, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
        return Response(buf.getvalue(), media_type="text/csv",
                        headers={"Content-Disposition": f'attachment; filename="dqap_{asset_id}.csv"'})
    return rows
