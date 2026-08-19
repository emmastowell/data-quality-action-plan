export type Dimension = "completeness"|"accuracy"|"validity"|"timeliness"|"uniqueness"|"consistency";
export interface Asset { id: string; name: string; description?: string; business_purpose?: string;
  source_system?: string; uc_table_ref?: string; owner_email?: string; steward_email?: string;
  criticality: "high"|"medium"|"low"; status: "draft"|"active"|"archived"; created_by?: string;
  kind: "critical"|"monitored"; }
export interface Rule { id: string; asset_id: string; name: string; dimension: Dimension;
  description?: string; measurement_method?: string; target_threshold?: number; unit: string;
  measurement_sql?: string;
  created_at?: string; updated_at?: string; created_by?: string; updated_by?: string; }
export interface Measurement { id: string; rule_id: string; score: number; measured_at: string;
  method: "manual"|"automated"; source: "manual"|"seeded"|"warehouse"|"monitoring"; evidence_note?: string; }
export interface Issue {
  id: string; asset_id: string; title: string;
  description?: string; rule_id?: string; dimension?: Dimension;
  impact_tags: string[];
  severity: "high"|"medium"|"low"; likelihood: "high"|"medium"|"low";
  root_cause_category?: string;
  status: "open"|"in_progress"|"blocked"|"resolved";
  reported_by?: string; assigned_to?: string; business_area?: string;
  data_subject?: string; impacted_systems?: string; example_reference?: string;
  system_owner?: string; related_issues?: string; comments?: string;
  status_date?: string; priority?: "high"|"medium"|"low";
  contributing_factors?: string; root_cause_detail?: string;
  created_at?: string; updated_at?: string; created_by?: string; updated_by?: string;
}
export interface Action {
  id: string; asset_id: string; title: string;
  description?: string; issue_id?: string; remediation_type?: string;
  priority: "high"|"medium"|"low"; assignee_email?: string; due_date?: string;
  status: "todo"|"in_progress"|"done"|"complete"|"no_longer_relevant"|"not_current_priority"|"not_feasible";
  start_date?: string; review_date?: string; completed_date?: string;
  success_criteria?: string; notes?: string;
  created_at?: string; updated_at?: string; created_by?: string; updated_by?: string;
}
export interface DashboardSummary { asset_count: number; active_asset_count: number;
  critical_asset_count: number; critical_active_count: number;
  monitored_asset_count: number; monitored_active_count: number;
  overall_score: number|null; score_by_dimension: Record<Dimension, number|null>;
  open_issue_count: number; actions_in_progress: number;
  assets_at_risk: { id: string; name: string; failing_rules: number; kind: "critical"|"monitored" }[]; }
export interface JourneySubStep { key: string; name: string; done: boolean;
  updated_by?: string|null; updated_at?: string|null; }
export interface JourneyStep { step: number; name: string; done: boolean;
  source: "substeps" | "manual" | "auto"; substeps: JourneySubStep[];
  updated_by?: string|null; updated_at?: string|null; }
export interface AssetTable {
  id: string; asset_id: string; catalog_name: string; schema_name: string;
  table_name: string; full_name: string; created_at?: string; created_by?: string;
}
export interface RaciRole { id: string; name: string; sort_order: number; }
export interface RaciActivity { step_label: string; key: string; activity_label: string; }
export interface RaciMatrixData { roles: RaciRole[]; activities: RaciActivity[]; cells: Record<string, Record<string, string>>; }
