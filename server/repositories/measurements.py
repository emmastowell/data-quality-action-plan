from server.repositories import insert, list_where


def add_measurement(conn, rule_id, m, user: str) -> dict:
    return insert(conn, "measurements", {
        "rule_id": rule_id, "score": m.score, "measured_at": m.measured_at,
        "method": m.method, "source": m.source, "evidence_note": m.evidence_note,
        "sample_size": m.sample_size, "created_by": user, "updated_by": user,
    })


def list_measurements(conn, rule_id):
    return list_where(conn, "measurements", {"rule_id": rule_id}, order_by="measured_at ASC")


def latest_by_rule(conn, rule_id):
    rows = list_where(conn, "measurements", {"rule_id": rule_id}, order_by="measured_at DESC")
    return rows[0] if rows else None
