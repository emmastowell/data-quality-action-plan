import uuid as _uuid
from fastapi import APIRouter, Request
from server.db import get_conn_ctx
from server.identity import current_user
from server.errors import AppError, not_found
from server.models import RaciMatrix, RaciRole, RaciRoleCreate, RaciCellUpdate
from server.raci_content import ACTIVITY_KEYS
from server.repositories import raci as repo


def _parse_uuid(value: str, *, not_found_resource: str | None = None, error_code: str | None = None):
    """Parse a UUID string; raise a clean HTTP error on failure instead of letting
    Postgres raise InvalidTextRepresentation → 500."""
    try:
        return _uuid.UUID(value)
    except ValueError:
        if not_found_resource:
            raise not_found(not_found_resource)
        raise AppError(error_code or "invalid_id", f"{value!r} is not a valid id", 422)

router = APIRouter()


@router.get("/raci", response_model=RaciMatrix)
def get_raci():
    with get_conn_ctx() as conn:
        m = repo.get_matrix(conn)
        conn.commit()  # persist any lazy seed
    return m


@router.post("/raci/roles", response_model=RaciRole, status_code=201)
def add_role(body: RaciRoleCreate, request: Request):
    name = body.name.strip()
    if not name:
        raise AppError("invalid_name", "role name is required", 422)
    user = current_user(request)
    with get_conn_ctx() as conn:
        row = repo.add_role(conn, name, user)
        conn.commit()
    return row


@router.patch("/raci/roles/{role_id}", response_model=RaciRole)
def rename_role(role_id: str, body: RaciRoleCreate, request: Request):
    name = body.name.strip()
    if not name:
        raise AppError("invalid_name", "role name is required", 422)
    _parse_uuid(role_id, not_found_resource="raci role")
    with get_conn_ctx() as conn:
        row = repo.rename_role(conn, role_id, name)
        conn.commit()
    if not row:
        raise not_found("raci role")
    return row


@router.delete("/raci/roles/{role_id}")
def delete_role(role_id: str):
    _parse_uuid(role_id, not_found_resource="raci role")
    with get_conn_ctx() as conn:
        ok = repo.delete_role(conn, role_id)
        conn.commit()
    if not ok:
        raise not_found("raci role")
    return {"deleted": role_id}


@router.put("/raci/cells")
def put_cell(body: RaciCellUpdate, request: Request):
    if body.activity_key not in ACTIVITY_KEYS:
        raise AppError("unknown_activity", f"unknown activity_key {body.activity_key!r}", 422)
    _parse_uuid(body.role_id, error_code="invalid_role")
    user = current_user(request)
    with get_conn_ctx() as conn:
        repo.upsert_cell(conn, body.activity_key, body.role_id, body.value.strip(), user)
        conn.commit()
    return {"ok": True}
