"""Scheduled job: refresh warehouse-SQL measurements for all active assets.

Database connectivity:
  - LOCAL runs: set LOCAL_DATABASE_URL=postgresql://... (bypasses Lakebase).
  - In-workspace (Databricks Job): pass --lakebase-instance and --pguser on
    the command line (see databricks.yml task parameters).  These are applied
    to os.environ as LAKEBASE_INSTANCE_NAME and PGUSER before server.db is
    imported, so server.db's SDK-based host resolution picks them up
    automatically.  The Lakebase host is resolved at import time via the
    Databricks SDK — no PGHOST injection is required.

The job is UNPAUSED in databricks.yml and runs daily at 06:00 Europe/London
as the app service principal.  The interactive "Run now" / "Run all" paths in
the app work independently and do not require this job.

Usage (local):
    LOCAL_DATABASE_URL=postgresql://localhost/dqap_dev WAREHOUSE_ID=<id> \
        uv run python jobs/run_measures.py

Usage (override warehouse at runtime):
    uv run python jobs/run_measures.py --warehouse-id <id>
"""
import argparse
import os
import re
import sys

# Ensure project root is on the path when run as a Databricks Job Python task.
# A serverless spark_python_task exec()s this file WITHOUT defining __file__, so
# resolve the repo root robustly (frame co_filename / cwd) and fall back safely.
def _repo_root() -> str:
    cands = []
    try:
        cands.append(os.path.abspath(__file__))  # normal / local runs
    except NameError:
        pass
    try:
        cands.append(os.path.abspath(sys._getframe().f_code.co_filename))  # exec'd file
    except Exception:
        pass
    for f in cands:
        root = os.path.dirname(os.path.dirname(f))
        if os.path.isdir(os.path.join(root, "server")):
            return root
    cwd = os.getcwd()
    for c in (cwd, os.path.dirname(cwd)):
        if os.path.isdir(os.path.join(c, "server")):
            return c
    return cwd


sys.path.insert(0, _repo_root())

# Parse --warehouse-id BEFORE importing warehouse runner so the env var is set
# in time for _real_run_sql (which reads os.environ.get("WAREHOUSE_ID")).
_parser = argparse.ArgumentParser(description="Refresh warehouse-SQL measurements")
_parser.add_argument("--warehouse-id", default=None,
                     help="Databricks SQL warehouse ID (overrides WAREHOUSE_ID env var)")
_parser.add_argument("--lakebase-instance", default=None)
_parser.add_argument("--pguser", default=None)
_args = _parser.parse_args()
if _args.warehouse_id:
    os.environ["WAREHOUSE_ID"] = _args.warehouse_id
if _args.lakebase_instance:
    os.environ["LAKEBASE_INSTANCE_NAME"] = _args.lakebase_instance
if _args.pguser:
    os.environ["PGUSER"] = _args.pguser

from server.db import get_conn_ctx, fetch_all, init_pool  # noqa: E402
from server.providers.warehouse import WarehouseSqlProvider  # noqa: E402
from server.repositories.measurements import add_measurement  # noqa: E402

_CREATED_BY = "scheduled_job"

# Read-only guard — matches the same check in WarehouseSqlProvider.measure().
_SELECT_RE = re.compile(r'^\s*(SELECT|WITH)\b', re.IGNORECASE)

_SQL = """
    SELECT r.id, r.name, r.measurement_sql, r.asset_id
    FROM quality_rules r
    JOIN data_assets a ON a.id = r.asset_id
    WHERE r.measurement_sql IS NOT NULL
      AND trim(r.measurement_sql) != ''
      AND a.status = 'active'
    ORDER BY a.id, r.name
"""


def main() -> None:
    provider = WarehouseSqlProvider()
    ok = 0
    failed = 0

    # The Lakebase pool is created open=False; the app opens it in its FastAPI
    # lifespan, but a Job has no lifespan, so open it here (skip local/test paths
    # that don't use the pool). Otherwise: PoolClosed "pool is not open yet".
    if not os.environ.get("LOCAL_DATABASE_URL"):
        init_pool().open(wait=True, timeout=30.0)

    with get_conn_ctx() as conn:
        rules = fetch_all(conn, _SQL)
        print(f"Found {len(rules)} rule(s) with measurement SQL across active assets.")

        for rule in rules:
            rid = rule["id"]
            name = rule["name"]
            sql = (rule.get("measurement_sql") or "").strip()
            try:
                # Read-only guard: skip non-SELECT/WITH queries and report as error.
                if not _SELECT_RE.match(sql):
                    raise ValueError(
                        f"measurement_sql must be a SELECT or WITH query, got: {sql[:80]!r}"
                    )
                # Per-rule savepoint — a DB error on one rule doesn't abort the batch
                # or discard measurements already committed by earlier rules.
                with conn.transaction():
                    m = provider.measure(rule, {})
                    add_measurement(conn, rid, m, _CREATED_BY)
                print(f"  OK  rule={rid} name={name!r} score={m.score}")
                ok += 1
            except Exception as exc:
                print(f"  ERR rule={rid} name={name!r} error={exc}")
                failed += 1

        conn.commit()

    print(f"\nDone — {ok} succeeded, {failed} failed.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
