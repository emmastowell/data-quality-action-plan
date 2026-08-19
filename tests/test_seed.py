from server.db import fetch_one
from seed.uk_ship_register import seed


def test_seed_creates_full_example(db_conn):
    seed(db_conn)
    asset = fetch_one(db_conn, "SELECT id FROM data_assets WHERE name=%s", ("UK Ship Register",))
    assert asset is not None
    n_rules = fetch_one(db_conn, "SELECT count(*) AS n FROM quality_rules WHERE asset_id=%s", (asset["id"],))["n"]
    assert n_rules == 6                       # one per dimension
    n_meas = fetch_one(db_conn, """SELECT count(*) AS n FROM measurements m
        JOIN quality_rules r ON r.id=m.rule_id WHERE r.asset_id=%s""", (asset["id"],))["n"]
    assert n_meas >= 36                        # 6 rules x ~6 months


def test_seed_is_idempotent(db_conn):
    seed(db_conn)
    seed(db_conn)
    n = fetch_one(db_conn, "SELECT count(*) AS n FROM data_assets WHERE name=%s", ("UK Ship Register",))["n"]
    assert n == 1
