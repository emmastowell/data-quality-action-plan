"""Scheduled-job task 2: mirror all Lakebase app tables into Unity Catalog.

Runs after run_measures. Reads each app table from Lakebase and overwrites the
matching Delta table in <catalog>.<schema> via serverless Spark (full refresh).

Connectivity: identical to the app — mints a Lakebase OAuth token via the SDK.
In a Job runtime PGHOST/PGUSER are not injected, so this script sets
LAKEBASE_INSTANCE_NAME / PGUSER from CLI args BEFORE importing server.db, and
server.db._resolve_pg_params derives the host from the instance.

Usage (local, against local Postgres — no Spark needed there, so this is
normally run only in-workspace):
    uv run python jobs/sync_to_uc.py --catalog cat --schema dqap \\
        --lakebase-instance my-inst --pguser <sp-id>
"""
import argparse
import os
import sys

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


def _configure() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mirror Lakebase app tables into Unity Catalog")
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--lakebase-instance", default=None)
    parser.add_argument("--pguser", default=None)
    parser.add_argument("--warehouse-id", default=None)  # accepted for parity; unused here
    args = parser.parse_args()

    # Set connection env BEFORE importing server.db (it reads these at pool build).
    if args.lakebase_instance:
        os.environ["LAKEBASE_INSTANCE_NAME"] = args.lakebase_instance
    if args.pguser:
        os.environ["PGUSER"] = args.pguser

    return args


def build_struct(spec):
    from pyspark.sql.types import (
        StructType, StructField, StringType, DoubleType, IntegerType,
        BooleanType, TimestampType, DateType, ArrayType,
    )
    makers = {
        "string": StringType,
        "double": DoubleType,
        "int": IntegerType,
        "bool": BooleanType,
        "timestamp": TimestampType,
        "date": DateType,
        "array<string>": lambda: ArrayType(StringType()),
    }
    return StructType([StructField(col, makers[token](), True) for col, token in spec])


def sync_table(spark, conn, name, spec, catalog, schema):
    from jobs.uc_sync_tables import coerce_row, column_list
    from server.db import fetch_all
    rows = fetch_all(conn, f"SELECT {column_list(spec)} FROM {name}")
    data = [coerce_row(r, spec) for r in rows]
    df = spark.createDataFrame(data, build_struct(spec))
    target = f"{catalog}.{schema}.{name}"
    df.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(target)
    return len(data)


def main():
    args = _configure()

    # Lazy imports — after _configure() has set env vars that server.db reads.
    from server.db import get_conn_ctx, init_pool
    from jobs.uc_sync_tables import TABLE_SPECS
    from pyspark.sql import SparkSession

    spark = SparkSession.builder.getOrCreate()

    # Pool is created open=False (the app opens it in its FastAPI lifespan; a Job
    # has none). Open it here so get_conn_ctx doesn't raise PoolClosed.
    if not os.environ.get("LOCAL_DATABASE_URL"):
        init_pool().open(wait=True, timeout=30.0)

    catalog, schema = args.catalog, args.schema
    ok, failed = 0, 0
    with get_conn_ctx() as conn:
        for name, spec in TABLE_SPECS.items():
            try:
                n = sync_table(spark, conn, name, spec, catalog, schema)
                print(f"  OK  {catalog}.{schema}.{name}: {n} row(s)")
                ok += 1
            except Exception as exc:  # noqa: BLE001 — isolate per-table failures
                print(f"  ERR {catalog}.{schema}.{name}: {exc}")
                failed += 1

    print(f"\nDone — {ok} table(s) mirrored, {failed} failed.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
