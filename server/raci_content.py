# Canonical RACI content transcribed verbatim from
# frontend/src/components/RaciMatrix.tsx (RACI_DATA and COLUMN_HEADERS).
# This module is the single source of truth for default activities and cells;
# the React component will be replaced in Task 4 to consume the API instead.

RACI_DEFAULT_ROLES: list[str] = [
    "Data steward / Business SME",
    "Data custodian / Technical SME",
    "Business analyst",
    "Data analyst",
    "Information Asset Owner / Manager",
    "Data owner / Process owner",
    "Data user",
]

# RACI_ACTIVITIES: ordered list of all 30 activities across 7 steps.
# key = f"s{step_number}-{0-based_index_within_step}"
RACI_ACTIVITIES: list[dict] = [
    # Step 1 — Identify critical data (4 activities)
    {"step_label": "Step 1 — Identify critical data", "key": "s1-0", "activity_label": "Identify primary purpose"},
    {"step_label": "Step 1 — Identify critical data", "key": "s1-1", "activity_label": "Identify critical data items"},
    {"step_label": "Step 1 — Identify critical data", "key": "s1-2", "activity_label": "Identify purpose of each critical data item"},
    {"step_label": "Step 1 — Identify critical data", "key": "s1-3", "activity_label": "Identify and log suspected data issues"},
    # Step 2 — Identify data quality rules (3 activities)
    {"step_label": "Step 2 — Identify data quality rules", "key": "s2-0", "activity_label": "Define business DQ rules"},
    {"step_label": "Step 2 — Identify data quality rules", "key": "s2-1", "activity_label": "Define acceptable level for thresholds"},
    {"step_label": "Step 2 — Identify data quality rules", "key": "s2-2", "activity_label": "Document DQAP metrics"},
    # Step 3 — Assess current data quality (5 activities)
    {"step_label": "Step 3 — Assess current data quality", "key": "s3-0", "activity_label": "Run technical DQ rules against critical data items"},
    {"step_label": "Step 3 — Assess current data quality", "key": "s3-1", "activity_label": "Review results against DQ rules and thresholds"},
    {"step_label": "Step 3 — Assess current data quality", "key": "s3-2", "activity_label": "Document findings"},
    {"step_label": "Step 3 — Assess current data quality", "key": "s3-3", "activity_label": "Update DQAP"},
    {"step_label": "Step 3 — Assess current data quality", "key": "s3-4", "activity_label": "Prioritise using Data Quality Issues Framework"},
    # Step 4 — Prioritise improvements and set goals (5 activities)
    {"step_label": "Step 4 — Prioritise improvements and set goals", "key": "s4-0", "activity_label": "Identify areas for improvement"},
    {"step_label": "Step 4 — Prioritise improvements and set goals", "key": "s4-1", "activity_label": "Prioritise improvements"},
    {"step_label": "Step 4 — Prioritise improvements and set goals", "key": "s4-2", "activity_label": "Consider factors"},
    {"step_label": "Step 4 — Prioritise improvements and set goals", "key": "s4-3", "activity_label": "Identify return on investment (ROI)"},
    {"step_label": "Step 4 — Prioritise improvements and set goals", "key": "s4-4", "activity_label": "Set improvement goals"},
    # Step 5 — Identify root cause and take action (5 activities)
    {"step_label": "Step 5 — Identify root cause and take action", "key": "s5-0", "activity_label": "Execute root cause analysis"},
    {"step_label": "Step 5 — Identify root cause and take action", "key": "s5-1", "activity_label": "Define resolution options"},
    {"step_label": "Step 5 — Identify root cause and take action", "key": "s5-2", "activity_label": "Assess different options"},
    {"step_label": "Step 5 — Identify root cause and take action", "key": "s5-3", "activity_label": "Define action priorities and set target dates"},
    {"step_label": "Step 5 — Identify root cause and take action", "key": "s5-4", "activity_label": "Resolve root cause(s)"},
    # Step 6 — Report on data quality (4 activities)
    {"step_label": "Step 6 — Report on data quality", "key": "s6-0", "activity_label": "Execute data cleansing"},
    {"step_label": "Step 6 — Report on data quality", "key": "s6-1", "activity_label": "Identify stakeholders and stakeholder groups"},
    {"step_label": "Step 6 — Report on data quality", "key": "s6-2", "activity_label": "Create a communication plan"},
    {"step_label": "Step 6 — Report on data quality", "key": "s6-3", "activity_label": "Communicate resolution and target date"},
    # Step 7 — Repeat / measure over time (4 activities)
    {"step_label": "Step 7 — Repeat / measure over time", "key": "s7-0", "activity_label": "Establish the frequency of checks"},
    {"step_label": "Step 7 — Repeat / measure over time", "key": "s7-1", "activity_label": "Run manual / automated checks"},
    {"step_label": "Step 7 — Repeat / measure over time", "key": "s7-2", "activity_label": "Create feedback loops"},
    {"step_label": "Step 7 — Repeat / measure over time", "key": "s7-3", "activity_label": "Monitor and assess results and take appropriate action"},
]

ACTIVITY_KEYS: set[str] = {a["key"] for a in RACI_ACTIVITIES}

# RACI_DEFAULT_CELLS: activity_key -> {role_name -> value}
# Values are verbatim strings from the TypeScript source (including empty strings).
# The seed skips empty-string values to keep the cells table sparse.
_DS = "Data steward / Business SME"
_DC = "Data custodian / Technical SME"
_BA = "Business analyst"
_DA = "Data analyst"
_IA = "Information Asset Owner / Manager"
_DO = "Data owner / Process owner"
_DU = "Data user"

RACI_DEFAULT_CELLS: dict[str, dict[str, str]] = {
    # Step 1
    "s1-0": {_DS: "R",  _DC: "",    _BA: "",  _DA: "",  _IA: "A (Risk)",    _DO: "A (Quality)",    _DU: "C"},
    "s1-1": {_DS: "R",  _DC: "",    _BA: "",  _DA: "",  _IA: "A (Risk)",    _DO: "A (Quality)",    _DU: "C"},
    "s1-2": {_DS: "R",  _DC: "",    _BA: "",  _DA: "",  _IA: "A (Risk)",    _DO: "A (Quality)",    _DU: "C"},
    "s1-3": {_DS: "R",  _DC: "C",   _BA: "",  _DA: "",  _IA: "A (Risk)",    _DO: "A (Quality)",    _DU: "C"},
    # Step 2
    "s2-0": {_DS: "R",  _DC: "C",   _BA: "C", _DA: "",  _IA: "",            _DO: "A (Quality)",    _DU: "C"},
    "s2-1": {_DS: "R",  _DC: "",    _BA: "",  _DA: "",  _IA: "",            _DO: "A (Quality)",    _DU: "C"},
    "s2-2": {_DS: "R",  _DC: "",    _BA: "",  _DA: "",  _IA: "",            _DO: "A (Quality)",    _DU: ""},
    # Step 3
    "s3-0": {_DS: "I",  _DC: "R",   _BA: "",  _DA: "R", _IA: "",            _DO: "A (Quality)",    _DU: ""},
    "s3-1": {_DS: "R",  _DC: "",    _BA: "",  _DA: "R", _IA: "",            _DO: "A (Quality)",    _DU: ""},
    "s3-2": {_DS: "R",  _DC: "",    _BA: "",  _DA: "",  _IA: "",            _DO: "A (Quality)",    _DU: ""},
    "s3-3": {_DS: "R",  _DC: "",    _BA: "",  _DA: "",  _IA: "",            _DO: "A (Quality)",    _DU: ""},
    "s3-4": {_DS: "R",  _DC: "",    _BA: "",  _DA: "",  _IA: "A (Risk) / C", _DO: "A (Quality) / C", _DU: ""},
    # Step 4
    "s4-0": {_DS: "R",  _DC: "",    _BA: "",  _DA: "",  _IA: "",            _DO: "A (Quality)",    _DU: "C"},
    "s4-1": {_DS: "R",  _DC: "",    _BA: "",  _DA: "",  _IA: "A (Risk) / C", _DO: "A (Quality) / C", _DU: "C"},
    "s4-2": {_DS: "R",  _DC: "C",   _BA: "",  _DA: "",  _IA: "A (Risk)",    _DO: "A (Quality) / C", _DU: "C"},
    "s4-3": {_DS: "R",  _DC: "",    _BA: "",  _DA: "",  _IA: "",            _DO: "A (Quality) / C", _DU: "C"},
    "s4-4": {_DS: "R",  _DC: "",    _BA: "",  _DA: "",  _IA: "A (Risk)",    _DO: "A (Quality) / R", _DU: "C"},
    # Step 5
    "s5-0": {_DS: "R",  _DC: "R",   _BA: "R", _DA: "C", _IA: "",            _DO: "A (Quality)",    _DU: "C"},
    "s5-1": {_DS: "R",  _DC: "C",   _BA: "C", _DA: "C", _IA: "",            _DO: "A (Quality)",    _DU: "C"},
    "s5-2": {_DS: "R",  _DC: "C",   _BA: "",  _DA: "C", _IA: "A (Risk) / C", _DO: "A (Quality) / C", _DU: "C"},
    "s5-3": {_DS: "R",  _DC: "C",   _BA: "",  _DA: "C", _IA: "A (Risk) / C", _DO: "A (Quality) / C", _DU: "C"},
    "s5-4": {_DS: "R",  _DC: "R",   _BA: "",  _DA: "C", _IA: "A (Risk) / C", _DO: "A (Quality) / C", _DU: "C"},
    # Step 6
    "s6-0": {_DS: "R",  _DC: "R",   _BA: "",  _DA: "C", _IA: "A (Risk) / C", _DO: "A (Quality) / C", _DU: "C"},
    "s6-1": {_DS: "C",  _DC: "",    _BA: "",  _DA: "C", _IA: "A (Risk) / C", _DO: "R (Quality) / A", _DU: "C"},
    "s6-2": {_DS: "C",  _DC: "",    _BA: "",  _DA: "",  _IA: "A (Risk) / I", _DO: "R (Quality) / A", _DU: "C"},
    "s6-3": {_DS: "C",  _DC: "",    _BA: "",  _DA: "",  _IA: "A (Risk) / I", _DO: "R (Quality) / A", _DU: "I"},
    # Step 7
    "s7-0": {_DS: "R",  _DC: "",    _BA: "",  _DA: "C", _IA: "A (Risk) / I", _DO: "A (Quality) / I", _DU: "C"},
    "s7-1": {_DS: "",   _DC: "R (automated)", _BA: "", _DA: "R (manual)", _IA: "A (Risk)", _DO: "A (Quality)", _DU: ""},
    "s7-2": {_DS: "R",  _DC: "R",   _BA: "",  _DA: "",  _IA: "A (Risk)",    _DO: "A (Quality)",    _DU: "C"},
    "s7-3": {_DS: "R",  _DC: "",    _BA: "",  _DA: "",  _IA: "A (Risk) / I", _DO: "A (Quality) / I", _DU: "C"},
}
