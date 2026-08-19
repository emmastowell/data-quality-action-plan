"""Warehouse SQL provider — executes a SQL statement on a Databricks SQL
warehouse and records the first numeric cell as the quality score.

Mock seam: call set_sql_runner(fn) with a callable (sql: str) -> float to
bypass the real SDK.  Call set_sql_runner(None) to restore real access.
Tests inject a fake runner so they never need live Databricks credentials.
"""
import os
import re
from datetime import datetime, timezone

from server.errors import AppError
from server.providers.base import Measurement

_sql_runner = None

# Only SELECT / WITH queries are permitted as measurement SQL.
_SELECT_RE = re.compile(r'^\s*(SELECT|WITH)\b', re.IGNORECASE)


def set_sql_runner(fn) -> None:
    """Override the SQL runner backend (pass None to restore real SDK access)."""
    global _sql_runner
    _sql_runner = fn


def run_sql(sql: str) -> float:
    """Execute *sql* and return the first cell of the first row as a float.

    Delegates to the injected fake when set_sql_runner() has been called;
    otherwise calls the real Databricks Statement Execution API.
    """
    if _sql_runner is not None:
        return float(_sql_runner(sql))
    return _real_run_sql(sql)


def _real_run_sql(sql: str) -> float:
    warehouse_id = os.environ.get("WAREHOUSE_ID")
    if not warehouse_id:
        raise AppError("config_error", "WAREHOUSE_ID environment variable not set", 500)

    from server.uc import get_ws
    try:
        result = get_ws().statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=sql,
            wait_timeout="30s",
        )
    except Exception as exc:
        raise AppError("measure_failed", f"SQL warehouse execution error: {exc}", 502) from exc

    # Fix #3: explicit None guard before touching data_array
    if result.result is None:
        raise AppError("measure_failed", "SQL returned no result object", 502)

    try:
        rows = result.result.data_array
        if not rows or not rows[0]:
            raise AppError("measure_failed", "SQL returned no rows — expected one numeric row", 502)
        return float(rows[0][0])
    except AppError:
        raise
    except (TypeError, ValueError) as exc:
        raise AppError("measure_failed", f"SQL result is not numeric: {exc}", 502) from exc
    except Exception as exc:
        raise AppError("measure_failed", f"Could not read result from SQL response: {exc}", 502) from exc


class WarehouseSqlProvider:
    """AssessmentProvider that runs a SQL statement on a Databricks SQL warehouse."""

    def measure(self, rule: dict, payload: dict) -> Measurement:
        # Fix #6: treat empty/whitespace-only SQL as missing
        sql = (rule.get("measurement_sql") or "").strip()
        if not sql:
            raise AppError("no_measurement_sql", "rule has no measurement SQL", 400)

        # Fix #2: read-only guard — only SELECT / WITH queries permitted
        if not _SELECT_RE.match(sql):
            raise AppError("unsafe_sql", "measurement_sql must be a SELECT or WITH query", 400)

        score = run_sql(sql)
        return Measurement(
            score=score,
            measured_at=datetime.now(timezone.utc),
            method="automated",
            source="warehouse",
            evidence_note="Ran measurement SQL on warehouse",
        )
