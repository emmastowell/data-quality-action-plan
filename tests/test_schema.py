from server.db import fetch_one, apply_schema


def test_schema_creates_tables_and_enum(db_conn):
    apply_schema(db_conn)
    for t in ["data_assets", "quality_rules", "measurements", "issues", "actions"]:
        row = fetch_one(db_conn, "SELECT to_regclass(%s) AS r", (t,))
        assert row["r"] is not None, f"missing table {t}"
    # dimension enum has exactly the six government dimensions
    labels = fetch_one(db_conn,
        "SELECT array_agg(enumlabel ORDER BY enumsortorder) AS l "
        "FROM pg_enum e JOIN pg_type t ON t.oid=e.enumtypid WHERE t.typname='dimension'")
    assert labels["l"] == ["completeness","accuracy","validity","timeliness","uniqueness","consistency"]
