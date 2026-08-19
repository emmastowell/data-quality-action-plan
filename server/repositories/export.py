import types as _types

from server.db import fetch_all, fetch_one, execute

# ---------------------------------------------------------------------------
# Step definitions
# ---------------------------------------------------------------------------

STEP_DEFS = [
    (1, "Identify critical data", [
        ("1a", "Catalogue the asset (name, owner, purpose, users)"),
        ("1b", "Confirm why it's critical (decisions/services impacted)"),
    ]),
    (2, "Identify data quality rules", [
        ("2a", "Define rules per dimension"),
        ("2b", "Set target thresholds"),
    ]),
    (3, "Assess current data quality", [
        ("3a", "Take baseline measurements"),
        ("3b", "Record evidence & confidence"),
    ]),
    (4, "Prioritise improvements and set goals", [
        ("4a", "Score impact × likelihood × effort"),
        ("4b", "Set targets/SLAs & assign owners"),
    ]),
    (5, "Identify root cause and take action", [
        ("5a", "Identify root cause"),
        ("5b", "Log remediation actions"),
    ]),
    (6, "Report on data quality", [
        ("6a", "Produce the report/dashboard"),
        ("6b", "Share with stakeholders"),
    ]),
    (7, "Repeat / measure over time", [
        ("7a", "Set monitoring cadence"),
        ("7b", "Review trends over time"),
    ]),
]

# All valid item_key values: "1".."7" + "1a","1b",.."7b"
VALID_KEYS: frozenset[str] = frozenset(
    [str(s) for s, _, _ in STEP_DEFS]
    + [key for _, _, subs in STEP_DEFS for key, _ in subs]
)


# ---------------------------------------------------------------------------
# Repository helpers
# ---------------------------------------------------------------------------

_ABSENT_STATUS = _types.MappingProxyType({"done": False, "updated_by": None, "updated_at": None})


def get_step_statuses(conn, asset_id) -> dict[str, dict]:
    """Return item_key→{done, updated_by, updated_at} mapping (only stored rows)."""
    rows = fetch_all(
        conn,
        "SELECT item_key, done, updated_by, updated_at FROM asset_step_status WHERE asset_id = %s",
        (asset_id,),
    )
    return {
        row["item_key"]: {
            "done": bool(row["done"]),
            "updated_by": row["updated_by"],
            "updated_at": row["updated_at"],
        }
        for row in rows
    }


def set_step_status(conn, asset_id, item_key: str, done: bool, user: str) -> None:
    """UPSERT a single step/sub-step status."""
    execute(
        conn,
        """
        INSERT INTO asset_step_status (asset_id, item_key, done, updated_by)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (asset_id, item_key)
        DO UPDATE SET done = EXCLUDED.done,
                      updated_at = now(),
                      updated_by = EXCLUDED.updated_by
        """,
        (asset_id, item_key, done, user),
    )


# ---------------------------------------------------------------------------
# Journey derivation
# ---------------------------------------------------------------------------

def journey(conn, asset_id) -> list[dict]:
    def has(sql):
        return fetch_one(conn, sql, (asset_id,))["n"] > 0

    asset = fetch_one(conn, "SELECT count(*) AS n FROM data_assets WHERE id=%s", (asset_id,))["n"] > 0
    rules = has("SELECT count(*) AS n FROM quality_rules WHERE asset_id=%s")
    meas = has("""SELECT count(*) AS n FROM measurements m
                  JOIN quality_rules r ON r.id=m.rule_id WHERE r.asset_id=%s""")
    actions = has("SELECT count(*) AS n FROM actions WHERE asset_id=%s")
    issues = has("SELECT count(*) AS n FROM issues WHERE asset_id=%s")

    # Step 7: done when any rule has >=2 measurements
    repeat = fetch_one(conn, """
        SELECT bool_or(c >= 2) AS ok FROM (
          SELECT count(*) AS c FROM measurements m
          JOIN quality_rules r ON r.id=m.rule_id WHERE r.asset_id=%s GROUP BY m.rule_id
        ) s""", (asset_id,))["ok"] or False

    auto_done = {1: asset, 2: rules, 3: meas, 4: actions, 5: issues, 6: meas, 7: repeat}

    statuses = get_step_statuses(conn, asset_id)

    result = []
    for step_num, step_name, subs in STEP_DEFS:
        sub_a_key, sub_b_key = subs[0][0], subs[1][0]
        sub_a_row = statuses.get(sub_a_key, _ABSENT_STATUS)
        sub_b_row = statuses.get(sub_b_key, _ABSENT_STATUS)
        sub_a_done = sub_a_row["done"]
        sub_b_done = sub_b_row["done"]
        parent_key = str(step_num)
        parent_row = statuses.get(parent_key, _ABSENT_STATUS)

        if sub_a_done and sub_b_done:
            effective_done = True
            source = "substeps"
        elif parent_key in statuses:
            effective_done = parent_row["done"]
            source = "manual"
        else:
            effective_done = bool(auto_done[step_num])
            source = "auto"

        result.append({
            "step": step_num,
            "name": step_name,
            "done": effective_done,
            "source": source,
            "updated_by": parent_row["updated_by"],
            "updated_at": parent_row["updated_at"],
            "substeps": [
                {
                    "key": key,
                    "name": name,
                    "done": row["done"],
                    "updated_by": row["updated_by"],
                    "updated_at": row["updated_at"],
                }
                for key, name in subs
                for row in (statuses.get(key, _ABSENT_STATUS),)
            ],
        })

    return result


# ---------------------------------------------------------------------------
# Export / plan rows
# ---------------------------------------------------------------------------

def plan_rows(conn, asset_id) -> list[dict]:
    return fetch_all(conn, """
        SELECT a.name AS asset, r.dimension, r.name AS rule, r.target_threshold, r.unit,
               (SELECT score FROM measurements WHERE rule_id=r.id ORDER BY measured_at DESC LIMIT 1) AS latest_score,
               (SELECT count(*) FROM issues i WHERE i.rule_id=r.id) AS linked_issues
        FROM quality_rules r JOIN data_assets a ON a.id=r.asset_id
        WHERE r.asset_id=%s ORDER BY r.dimension, r.name""", (asset_id,))
