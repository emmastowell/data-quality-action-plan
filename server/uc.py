"""Unity Catalog access helpers.

Mock seam: call set_uc_provider(obj) with an object that implements
list_catalogs() / list_schemas(catalog) / list_tables(catalog, schema)
to bypass the real SDK.  Call set_uc_provider(None) to restore real access.
Tests use this so they never need live Databricks credentials.
"""
from typing import NoReturn

_uc_provider = None


def set_uc_provider(obj) -> None:
    """Override the UC backend (use None to restore real SDK access)."""
    global _uc_provider
    _uc_provider = obj


# Cached workspace client — built lazily so importing this module never
# requires Databricks credentials (tests override via set_uc_provider).
_ws = None


def get_ws():
    global _ws
    if _ws is None:
        from databricks.sdk import WorkspaceClient
        _ws = WorkspaceClient()
    return _ws


def _uc_error(exc) -> NoReturn:
    from server.errors import AppError
    raise AppError("uc_error", "could not reach Unity Catalog", 502) from exc


def list_catalogs() -> list[str]:
    if _uc_provider is not None:
        return _uc_provider.list_catalogs()
    try:
        return [c.name for c in get_ws().catalogs.list() if c.name]
    except Exception as exc:
        _uc_error(exc)


def list_schemas(catalog: str) -> list[str]:
    if _uc_provider is not None:
        return _uc_provider.list_schemas(catalog)
    try:
        return [s.name for s in get_ws().schemas.list(catalog_name=catalog) if s.name]
    except Exception as exc:
        _uc_error(exc)


def list_tables(catalog: str, schema: str) -> list[dict]:
    if _uc_provider is not None:
        return _uc_provider.list_tables(catalog, schema)
    try:
        results = []
        for t in get_ws().tables.list(catalog_name=catalog, schema_name=schema):
            results.append({
                "name": t.name,
                "full_name": t.full_name or f"{catalog}.{schema}.{t.name}",
                "table_type": t.table_type.value if t.table_type else None,
            })
        return results
    except Exception as exc:
        _uc_error(exc)
