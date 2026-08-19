import argparse
import os
import psycopg
from server.db import apply_schema

_TABLES = ["raci_cells", "raci_roles", "asset_tables", "actions", "issues", "measurements", "quality_rules", "data_assets"]


def run_setup(conn, reset: bool = False, seed: bool = False) -> None:
    if reset:
        for t in _TABLES:
            conn.execute(f"DROP TABLE IF EXISTS {t} CASCADE")
    apply_schema(conn)
    from server.repositories.raci import _seed_if_empty
    _seed_if_empty(conn)
    if seed:
        from seed.uk_ship_register import seed as seed_example
        seed_example(conn)


def _connect():
    url = os.environ.get("LOCAL_DATABASE_URL") or os.environ.get("TEST_DATABASE_URL")
    if url:
        return psycopg.connect(url)
    return psycopg.connect(
        dbname=os.environ["PGDATABASE"], user=os.environ["PGUSER"],
        host=os.environ["PGHOST"], port=os.environ.get("PGPORT", "5432"),
        sslmode=os.environ.get("PGSSLMODE", "require"),
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--reset", action="store_true")
    p.add_argument("--seed", action="store_true")
    args = p.parse_args()
    with _connect() as conn:
        run_setup(conn, reset=args.reset, seed=args.seed)
        conn.commit()
    print(f"setup complete (reset={args.reset}, seed={args.seed})")
