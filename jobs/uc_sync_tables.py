"""Pure (Spark-free) table specs + row coercion for the Lakebase -> UC mirror.

TABLE_SPECS is the single source of truth for which columns are mirrored and
their target Spark types. Column names here are code constants and are safe to
interpolate into SELECT statements.
"""

# type tokens: string | double | int | bool | timestamp | date | array<string>
TABLE_SPECS = {
    "data_assets": [
        ("id", "string"), ("name", "string"), ("description", "string"),
        ("business_purpose", "string"), ("source_system", "string"),
        ("uc_table_ref", "string"), ("owner_email", "string"),
        ("steward_email", "string"), ("criticality", "string"),
        ("status", "string"), ("created_at", "timestamp"),
        ("updated_at", "timestamp"), ("created_by", "string"),
        ("updated_by", "string"),
    ],
    "quality_rules": [
        ("id", "string"), ("asset_id", "string"), ("dimension", "string"),
        ("name", "string"), ("description", "string"),
        ("measurement_method", "string"), ("target_threshold", "double"),
        ("unit", "string"), ("created_at", "timestamp"),
        ("updated_at", "timestamp"), ("created_by", "string"),
        ("updated_by", "string"), ("measurement_sql", "string"),
    ],
    "measurements": [
        ("id", "string"), ("rule_id", "string"), ("score", "double"),
        ("measured_at", "timestamp"), ("method", "string"),
        ("source", "string"), ("evidence_note", "string"),
        ("sample_size", "int"), ("created_at", "timestamp"),
        ("updated_at", "timestamp"), ("created_by", "string"),
        ("updated_by", "string"),
    ],
    "issues": [
        ("id", "string"), ("asset_id", "string"), ("rule_id", "string"),
        ("title", "string"), ("description", "string"), ("dimension", "string"),
        ("impact_tags", "array<string>"), ("severity", "string"),
        ("likelihood", "string"), ("root_cause_category", "string"),
        ("status", "string"), ("created_at", "timestamp"),
        ("updated_at", "timestamp"), ("created_by", "string"),
        ("updated_by", "string"), ("reported_by", "string"),
        ("assigned_to", "string"), ("business_area", "string"),
        ("data_subject", "string"), ("impacted_systems", "string"),
        ("example_reference", "string"), ("system_owner", "string"),
        ("related_issues", "string"), ("comments", "string"),
        ("status_date", "date"), ("priority", "string"),
        ("contributing_factors", "string"), ("root_cause_detail", "string"),
    ],
    "actions": [
        ("id", "string"), ("asset_id", "string"), ("issue_id", "string"),
        ("title", "string"), ("description", "string"),
        ("remediation_type", "string"), ("priority", "string"),
        ("assignee_email", "string"), ("due_date", "date"),
        ("status", "string"), ("created_at", "timestamp"),
        ("updated_at", "timestamp"), ("created_by", "string"),
        ("updated_by", "string"), ("start_date", "date"),
        ("review_date", "date"), ("completed_date", "date"),
        ("success_criteria", "string"), ("notes", "string"),
    ],
    "asset_step_status": [
        ("asset_id", "string"), ("item_key", "string"), ("done", "bool"),
        ("updated_at", "timestamp"), ("updated_by", "string"),
    ],
    "asset_tables": [
        ("id", "string"), ("asset_id", "string"), ("catalog_name", "string"),
        ("schema_name", "string"), ("table_name", "string"),
        ("full_name", "string"), ("created_at", "timestamp"),
        ("created_by", "string"),
    ],
}


def coerce_value(value, token):
    if value is None:
        return None
    if token == "string":
        return str(value)
    if token == "double":
        return float(value)
    if token == "int":
        return int(value)
    if token == "bool":
        return bool(value)
    if token == "array<string>":
        return [str(x) for x in value]
    # timestamp / date: psycopg returns datetime.datetime / datetime.date,
    # which Spark maps directly — pass through.
    return value


def coerce_row(row, spec):
    return [coerce_value(row.get(col), token) for col, token in spec]


def column_list(spec):
    return ", ".join(col for col, _ in spec)
