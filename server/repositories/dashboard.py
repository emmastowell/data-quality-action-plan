from server.db import fetch_all, fetch_one

_DIMENSIONS = ["completeness", "accuracy", "validity", "timeliness", "uniqueness", "consistency"]

# Latest measurement per rule, joined to its rule/asset. LATERAL gives the newest row per rule.
_LATEST = """
SELECT r.id AS rule_id, r.asset_id, r.dimension, r.target_threshold,
       m.score, a.name AS asset_name, a.kind AS asset_kind
FROM quality_rules r
JOIN data_assets a ON a.id = r.asset_id AND a.status = 'active'
LEFT JOIN LATERAL (
    SELECT score FROM measurements
    WHERE rule_id = r.id ORDER BY measured_at DESC LIMIT 1
) m ON true
"""


def dashboard_summary(conn) -> dict:
    rows = fetch_all(conn, _LATEST)
    scored = [r for r in rows if r["score"] is not None]

    def mean(vals):
        return round(sum(vals) / len(vals), 2) if vals else None

    overall = mean([float(r["score"]) for r in scored])
    by_dim = {d: mean([float(r["score"]) for r in scored if r["dimension"] == d]) for d in _DIMENSIONS}

    at_risk = {}
    for r in scored:
        if r["target_threshold"] is not None and float(r["score"]) < float(r["target_threshold"]):
            entry = at_risk.setdefault(r["asset_id"], {"id": r["asset_id"], "name": r["asset_name"],
                                                        "kind": r["asset_kind"], "failing_rules": 0})
            entry["failing_rules"] += 1

    counts = fetch_one(conn, """
        SELECT (SELECT count(*) FROM data_assets) AS asset_count,
               (SELECT count(*) FROM data_assets WHERE status='active') AS active_asset_count,
               (SELECT count(*) FROM data_assets WHERE kind='critical') AS critical_asset_count,
               (SELECT count(*) FROM data_assets WHERE kind='critical' AND status='active') AS critical_active_count,
               (SELECT count(*) FROM data_assets WHERE kind='monitored') AS monitored_asset_count,
               (SELECT count(*) FROM data_assets WHERE kind='monitored' AND status='active') AS monitored_active_count,
               (SELECT count(*) FROM issues WHERE status IN ('open','blocked')) AS open_issue_count,
               (SELECT count(*) FROM actions WHERE status='in_progress') AS actions_in_progress
    """)
    return {
        "asset_count": counts["asset_count"],
        "active_asset_count": counts["active_asset_count"],
        "critical_asset_count": counts["critical_asset_count"],
        "critical_active_count": counts["critical_active_count"],
        "monitored_asset_count": counts["monitored_asset_count"],
        "monitored_active_count": counts["monitored_active_count"],
        "overall_score": overall,
        "score_by_dimension": by_dim,
        "open_issue_count": counts["open_issue_count"],
        "actions_in_progress": counts["actions_in_progress"],
        "assets_at_risk": list(at_risk.values()),
    }
