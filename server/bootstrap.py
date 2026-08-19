import os
from setup import run_setup


def _flag(name: str) -> bool:
    return os.environ.get(name, "").lower() in ("1", "true", "yes")


def maybe_bootstrap(conn) -> str:
    if not _flag("RUN_SETUP_ON_START"):
        return "skipped"
    seed = _flag("SEED_ON_START")
    run_setup(conn, reset=False, seed=seed)
    conn.commit()
    return "schema+seed" if seed else "schema"
