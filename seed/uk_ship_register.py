from datetime import datetime, timedelta, timezone
from server.db import fetch_one
from server.repositories import insert

USER = "seed@mca.gov.uk"

# (dimension, rule name, description, target %) — one credible rule per government dimension.
RULES = [
    ("completeness", "Registered owner contact present",
     "Registered-owner contact details present for active vessels.", 99.0),
    ("accuracy", "Gross tonnage matches survey",
     "Recorded gross tonnage matches the latest survey certificate.", 98.0),
    ("validity", "IMO number well-formed",
     "IMO number conforms to the 7-digit format and check digit.", 99.9),
    ("timeliness", "Registration status current",
     "Registration/renewal status updated within SLA of survey.", 95.0),
    ("uniqueness", "IMO number unique",
     "No duplicate IMO numbers across active registrations.", 99.99),
    ("consistency", "Owner matches companies register",
     "Registered-owner name matches the owner held on the companies register.", 98.0),
]

# Six monthly scores per rule, trending gently upward toward target (final month closest to target).
TREND = {
    "completeness": [94.1, 95.0, 95.8, 96.9, 97.7, 98.6],
    "accuracy":     [90.2, 91.5, 93.0, 94.1, 95.0, 96.2],
    "validity":     [99.1, 99.3, 99.5, 99.6, 99.8, 99.9],
    "timeliness":   [82.0, 85.5, 88.0, 90.2, 92.1, 93.4],
    "uniqueness":   [98.9, 99.2, 99.4, 99.6, 99.8, 99.9],
    "consistency":  [88.4, 90.0, 91.7, 93.2, 94.5, 95.6],
}


def seed(conn) -> None:
    if fetch_one(conn, "SELECT 1 FROM data_assets WHERE name=%s", ("UK Ship Register",)):
        return

    asset = insert(conn, "data_assets", {
        "name": "UK Ship Register",
        "description": "The register of merchant and pleasure vessels flagged to the United Kingdom.",
        "business_purpose": "Establishes nationality of vessels; relied on for tonnage tax, port state control and safety.",
        "source_system": "Ship Register core system",
        "uc_table_ref": "main.mca.ship_register",
        "owner_email": "registrar@mca.gov.uk",
        "steward_email": "data.steward@mca.gov.uk",
        "criticality": "high", "status": "active",
        "created_by": USER, "updated_by": USER,
    })
    aid = asset["id"]

    now = datetime.now(timezone.utc).replace(day=1, hour=9, minute=0, second=0, microsecond=0)
    months = [now - timedelta(days=30 * (5 - i)) for i in range(6)]  # oldest → newest

    rule_ids = {}
    for dim, name, desc, target in RULES:
        rule = insert(conn, "quality_rules", {
            "asset_id": aid, "dimension": dim, "name": name, "description": desc,
            "measurement_method": "Automated rule check on the register extract.",
            "target_threshold": target, "unit": "%", "created_by": USER, "updated_by": USER,
        })
        rule_ids[dim] = rule["id"]
        for when, score in zip(months, TREND[dim]):
            insert(conn, "measurements", {
                "rule_id": rule["id"], "score": score, "measured_at": when,
                "method": "automated", "source": "seeded",
                "evidence_note": "Seeded historical measurement.", "sample_size": 250000,
                "created_by": USER, "updated_by": USER,
            })

    issue1 = insert(conn, "issues", {
        "asset_id": aid, "rule_id": rule_ids["timeliness"],
        "title": "Renewal status lags survey completion",
        "description": "Status updates trail survey sign-off by up to two weeks in regional offices.",
        "dimension": "timeliness", "impact_tags": ["operational", "reputational"],
        "severity": "high", "likelihood": "high", "root_cause_category": "process_gap",
        "status": "in_progress",
        "reported_by": "survey.ops@mca.gov.uk",
        "assigned_to": "ops.lead@mca.gov.uk",
        "business_area": "Registry Operations",
        "data_subject": "Vessel",
        "impacted_systems": "Ship Register core system, Survey Workflow Portal",
        "example_reference": "IMO 9876543 — renewal status remained 'pending' for 14 days post-survey",
        "system_owner": "registrar@mca.gov.uk",
        "related_issues": "Owner names diverge from companies register",
        "comments": "Regional offices using manual email handoffs; automation scoping in progress.",
        "status_date": "2026-06-30",
        "priority": "high",
        "contributing_factors": "Manual handoff between survey team and registry clerical staff; no API integration between systems.",
        "root_cause_detail": "Survey Workflow Portal does not emit an event on sign-off; registry staff must poll and update manually, introducing a 5–14 day lag.",
        "created_by": USER, "updated_by": USER,
    })
    insert(conn, "issues", {
        "asset_id": aid, "rule_id": rule_ids["consistency"],
        "title": "Owner names diverge from companies register",
        "description": "Free-text owner names do not always match the authoritative companies register.",
        "dimension": "consistency", "impact_tags": ["legal"],
        "severity": "medium", "likelihood": "medium", "root_cause_category": "reference_data",
        "status": "open",
        "reported_by": "data.steward@mca.gov.uk",
        "assigned_to": "data.eng@mca.gov.uk",
        "business_area": "Registry Operations",
        "data_subject": "Vessel Owner",
        "impacted_systems": "Ship Register core system, Companies House API",
        "example_reference": "Vessel SR-00412 — owner field 'Smith & Sons Ltd' vs Companies House 'Smith and Sons Limited'",
        "system_owner": "registrar@mca.gov.uk",
        "comments": "Affects approximately 3.2% of active registrations; no automated reconciliation in place.",
        "status_date": "2026-07-15",
        "priority": "medium",
        "contributing_factors": "No lookup or validation against Companies House at point of registration entry.",
        "root_cause_detail": "The registration form accepts free text for owner name with no lookup to the Companies House API, allowing variant spellings and abbreviations.",
        "created_by": USER, "updated_by": USER,
    })

    insert(conn, "actions", {
        "asset_id": aid, "issue_id": issue1["id"],
        "title": "Automate renewal-status update on survey sign-off",
        "description": "Trigger status update from the survey workflow to remove the manual lag.",
        "remediation_type": "process", "priority": "high",
        "assignee_email": "ops.lead@mca.gov.uk", "status": "complete",
        "start_date": "2026-04-01",
        "review_date": "2026-07-01",
        "completed_date": "2026-06-28",
        "success_criteria": "Renewal status updated within 24 hours of survey sign-off for ≥98% of cases; no manual handoff required.",
        "notes": "API integration delivered in Sprint 14. Post-go-live monitoring confirmed <4 hour average lag. Closed early.",
        "created_by": USER, "updated_by": USER,
    })
    insert(conn, "actions", {
        "asset_id": aid,
        "title": "Reconcile owner names against companies register nightly",
        "description": "Add a nightly reconciliation job flagging mismatches for stewardship review.",
        "remediation_type": "reference_data", "priority": "medium",
        "assignee_email": "data.eng@mca.gov.uk", "status": "in_progress",
        "start_date": "2026-07-01",
        "review_date": "2026-09-30",
        "success_criteria": "Nightly job running; mismatch rate reported in DQAP dashboard; stewardship team reviewing flagged records within 5 working days.",
        "notes": "Companies House API access approved. Reconciliation logic in development; dashboard widget scoped for Q3.",
        "created_by": USER, "updated_by": USER,
    })
