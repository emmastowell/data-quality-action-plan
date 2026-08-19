from fastapi import APIRouter, Query
from server.errors import AppError
import server.uc as uc

router = APIRouter()


@router.get("/uc/catalogs")
def get_catalogs():
    return {"catalogs": uc.list_catalogs()}


@router.get("/uc/schemas")
def get_schemas(catalog: str = Query(default=None)):
    if not catalog:
        raise AppError("bad_request", "catalog parameter is required", 400)
    return {"schemas": uc.list_schemas(catalog)}


@router.get("/uc/tables")
def get_tables(
    catalog: str = Query(default=None),
    schema: str = Query(default=None),
):
    if not catalog or not schema:
        raise AppError("bad_request", "catalog and schema parameters are required", 400)
    return {"tables": uc.list_tables(catalog, schema)}
