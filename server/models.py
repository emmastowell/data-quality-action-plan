from datetime import date, datetime
from typing import Literal, Optional
from pydantic import BaseModel

Dimension = Literal["completeness", "accuracy", "validity", "timeliness", "uniqueness", "consistency"]
Criticality = Literal["high", "medium", "low"]
AssetStatus = Literal["draft", "active", "archived"]
AssetKind = Literal["critical", "monitored"]
Severity = Literal["high", "medium", "low"]
RootCause = Literal["capture_ux", "integration_etl", "process_gap", "reference_data", "infrastructure", "other"]
IssueStatus = Literal["open", "in_progress", "blocked", "resolved"]
MeasureMethod = Literal["manual", "automated"]
MeasureSource = Literal["manual", "seeded", "warehouse", "monitoring"]
Remediation = Literal["front_end_validation", "etl_fix", "training", "reference_data", "data_repair", "process", "other"]
# 'complete' is canonical terminal status; 'todo'/'done' retained as legacy aliases.
ActionStatus = Literal["todo", "in_progress", "done", "complete", "no_longer_relevant", "not_current_priority", "not_feasible"]


class AssetCreate(BaseModel):
    name: str
    description: Optional[str] = None
    business_purpose: Optional[str] = None
    source_system: Optional[str] = None
    uc_table_ref: Optional[str] = None
    owner_email: Optional[str] = None
    steward_email: Optional[str] = None
    criticality: Criticality = "medium"
    status: AssetStatus = "draft"
    kind: AssetKind = "critical"


class AssetUpdate(AssetCreate):
    name: Optional[str] = None
    criticality: Optional[Criticality] = None
    status: Optional[AssetStatus] = None
    kind: Optional[AssetKind] = None


class Asset(AssetCreate):
    id: str
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None


class RuleCreate(BaseModel):
    name: str
    dimension: Dimension
    description: Optional[str] = None
    measurement_method: Optional[str] = None
    measurement_sql: Optional[str] = None
    target_threshold: Optional[float] = None
    unit: str = "%"


class RuleUpdate(RuleCreate):
    name: Optional[str] = None
    dimension: Optional[Dimension] = None
    unit: Optional[str] = None


class Rule(RuleCreate):
    id: str
    asset_id: str
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None


class MeasurementCreate(BaseModel):
    score: float
    evidence_note: Optional[str] = None
    sample_size: Optional[int] = None
    measured_at: Optional[datetime] = None


class Measurement(BaseModel):
    id: str
    rule_id: str
    score: float
    measured_at: datetime
    method: MeasureMethod
    source: MeasureSource
    evidence_note: Optional[str] = None
    sample_size: Optional[int] = None


class IssueCreate(BaseModel):
    title: str
    description: Optional[str] = None
    rule_id: Optional[str] = None
    dimension: Optional[Dimension] = None
    impact_tags: list[str] = []
    severity: Severity = "medium"
    likelihood: Severity = "medium"
    root_cause_category: Optional[RootCause] = None
    status: IssueStatus = "open"
    # GOV.UK DQAP extended fields
    reported_by: Optional[str] = None
    assigned_to: Optional[str] = None
    business_area: Optional[str] = None
    data_subject: Optional[str] = None
    impacted_systems: Optional[str] = None
    example_reference: Optional[str] = None
    system_owner: Optional[str] = None
    related_issues: Optional[str] = None
    comments: Optional[str] = None
    status_date: Optional[date] = None
    priority: Optional[Severity] = None
    contributing_factors: Optional[str] = None
    root_cause_detail: Optional[str] = None


class IssueUpdate(IssueCreate):
    title: Optional[str] = None
    impact_tags: Optional[list[str]] = None
    severity: Optional[Severity] = None
    likelihood: Optional[Severity] = None
    status: Optional[IssueStatus] = None


class Issue(IssueCreate):
    id: str
    asset_id: str
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None


class ActionCreate(BaseModel):
    title: str
    description: Optional[str] = None
    issue_id: Optional[str] = None
    remediation_type: Optional[Remediation] = None
    priority: Severity = "medium"
    assignee_email: Optional[str] = None
    due_date: Optional[date] = None
    status: ActionStatus = "todo"
    # GOV.UK DQAP extended fields
    start_date: Optional[date] = None
    review_date: Optional[date] = None
    completed_date: Optional[date] = None
    success_criteria: Optional[str] = None
    notes: Optional[str] = None


class ActionUpdate(ActionCreate):
    title: Optional[str] = None
    priority: Optional[Severity] = None
    status: Optional[ActionStatus] = None


class Action(ActionCreate):
    id: str
    asset_id: str
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None


class AssetTableCreate(BaseModel):
    catalog_name: str
    schema_name: str
    table_name: str


class AssetTable(BaseModel):
    id: str
    asset_id: str
    catalog_name: str
    schema_name: str
    table_name: str
    full_name: str
    created_at: datetime
    created_by: Optional[str] = None


class RaciRole(BaseModel):
    id: str
    name: str
    sort_order: int


class RaciActivity(BaseModel):
    step_label: str
    key: str
    activity_label: str


class RaciMatrix(BaseModel):
    roles: list[RaciRole]
    activities: list[RaciActivity]
    cells: dict[str, dict[str, str]]


class RaciRoleCreate(BaseModel):
    name: str


class RaciCellUpdate(BaseModel):
    activity_key: str
    role_id: str
    value: str = ""


class DashboardSummary(BaseModel):
    asset_count: int
    active_asset_count: int
    critical_asset_count: int
    critical_active_count: int
    monitored_asset_count: int
    monitored_active_count: int
    overall_score: Optional[float]
    score_by_dimension: dict[str, Optional[float]]
    open_issue_count: int
    actions_in_progress: int
    assets_at_risk: list[dict]
