import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Action, Issue } from "../api/types";
import AuditLine from "./AuditLine";
import { SummaryList, priorityClass } from "./shared";

const REMEDIATION_TYPES: { value: string; label: string }[] = [
  { value: "data_cleanse", label: "Data cleanse" },
  { value: "process_improvement", label: "Process improvement" },
  { value: "system_fix", label: "System fix" },
  { value: "training", label: "Training" },
  { value: "governance", label: "Governance" },
  { value: "new_standard", label: "New standard" },
  { value: "monitoring", label: "Monitoring" },
  { value: "policy_update", label: "Policy update" },
];

const ACTION_STATUSES: { value: string; label: string }[] = [
  { value: "todo", label: "To do" },
  { value: "in_progress", label: "In progress" },
  { value: "complete", label: "Complete" },
  { value: "no_longer_relevant", label: "No longer relevant" },
  { value: "not_current_priority", label: "Not current priority" },
  { value: "not_feasible", label: "Not feasible" },
  { value: "done", label: "Done (legacy)" },
];

interface ActionFormState {
  title: string; description: string; issue_id: string; remediation_type: string;
  assignee_email: string; priority: string;
  start_date: string; due_date: string; review_date: string; completed_date: string;
  success_criteria: string; notes: string; status: string;
}

const BLANK: ActionFormState = {
  title: "", description: "", issue_id: "", remediation_type: "",
  assignee_email: "", priority: "medium",
  start_date: "", due_date: "", review_date: "", completed_date: "",
  success_criteria: "", notes: "", status: "todo",
};

function toState(a: Action): ActionFormState {
  return {
    title: a.title, description: a.description ?? "", issue_id: a.issue_id ?? "",
    remediation_type: a.remediation_type ?? "", assignee_email: a.assignee_email ?? "",
    priority: a.priority, start_date: a.start_date ?? "", due_date: a.due_date ?? "",
    review_date: a.review_date ?? "", completed_date: a.completed_date ?? "",
    success_criteria: a.success_criteria ?? "", notes: a.notes ?? "", status: a.status,
  };
}

function cleanBody(v: ActionFormState): Record<string, unknown> {
  const body: Record<string, unknown> = {};
  for (const [k, val] of Object.entries(v)) {
    if (val !== "" && val !== undefined) body[k] = val;
  }
  return body;
}

function actionTagClass(status: string): string {
  const m: Record<string, string> = {
    todo: "govuk-tag--grey", in_progress: "govuk-tag--yellow",
    done: "govuk-tag--green", complete: "govuk-tag--green",
    no_longer_relevant: "govuk-tag--grey", not_current_priority: "govuk-tag--grey",
    not_feasible: "govuk-tag--orange",
  };
  return m[status] ?? "";
}

interface ActionFormProps {
  initial: ActionFormState;
  issues: Issue[];
  onSubmit: (body: Record<string, unknown>) => Promise<void>;
  onCancel: () => void;
  submitLabel: string;
}

export function ActionForm({ initial, issues, onSubmit, onCancel, submitLabel }: ActionFormProps) {
  const [v, setV] = useState<ActionFormState>(initial);
  const [titleError, setTitleError] = useState<string>();
  const [submitError, setSubmitError] = useState<string>();

  const set = (k: keyof ActionFormState) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
      setV(prev => ({ ...prev, [k]: e.target.value }));

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!v.title.trim()) { setTitleError("Enter a title for the action"); return; }
    setTitleError(undefined);
    try {
      await onSubmit(cleanBody(v));
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : "Could not save. Please try again.");
    }
  }

  const anyError = titleError || submitError;

  return (
    <form onSubmit={submit}>
      {anyError && (
        <div className="govuk-error-summary" role="alert">
          <h2 className="govuk-error-summary__title">There is a problem</h2>
          <div className="govuk-error-summary__body"><p className="govuk-body">{anyError}</p></div>
        </div>
      )}

      <div className={`govuk-form-group${titleError ? " govuk-form-group--error" : ""}`}>
        <label className="govuk-label govuk-label--s" htmlFor="af-title">
          Title <span aria-hidden="true">*</span>
        </label>
        {titleError && <p className="govuk-error-message" id="af-title-err">{titleError}</p>}
        <input
          className={`govuk-input govuk-input--width-30${titleError ? " govuk-input--error" : ""}`}
          id="af-title" value={v.title} onChange={set("title")}
          aria-describedby={titleError ? "af-title-err" : undefined}
        />
      </div>

      <div className="govuk-form-group">
        <label className="govuk-label govuk-label--s" htmlFor="af-desc">Description</label>
        <textarea className="govuk-textarea" id="af-desc" rows={3} value={v.description} onChange={set("description")} />
      </div>

      <div className="govuk-grid-row">
        <div className="govuk-grid-column-one-half">
          <div className="govuk-form-group">
            <label className="govuk-label govuk-label--s" htmlFor="af-issue">Linked issue</label>
            <select className="govuk-select" id="af-issue" value={v.issue_id} onChange={set("issue_id")}>
              <option value="">— none —</option>
              {issues.map(i => <option key={i.id} value={i.id}>{i.title}</option>)}
            </select>
          </div>
        </div>
        <div className="govuk-grid-column-one-half">
          <div className="govuk-form-group">
            <label className="govuk-label govuk-label--s" htmlFor="af-rem">Remediation type</label>
            <select className="govuk-select" id="af-rem" value={v.remediation_type} onChange={set("remediation_type")}>
              <option value="">— none —</option>
              {REMEDIATION_TYPES.map(rt => <option key={rt.value} value={rt.value}>{rt.label}</option>)}
            </select>
          </div>
        </div>
      </div>

      <div className="govuk-grid-row">
        <div className="govuk-grid-column-one-half">
          <div className="govuk-form-group">
            <label className="govuk-label govuk-label--s" htmlFor="af-asgn">Action owner / assignee</label>
            <input className="govuk-input" id="af-asgn" value={v.assignee_email} onChange={set("assignee_email")} />
          </div>
        </div>
        <div className="govuk-grid-column-one-half">
          <div className="govuk-form-group">
            <label className="govuk-label govuk-label--s" htmlFor="af-pri">Priority</label>
            <select className="govuk-select" id="af-pri" value={v.priority} onChange={set("priority")}>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
        </div>
      </div>

      <div className="govuk-grid-row">
        <div className="govuk-grid-column-one-half">
          <div className="govuk-form-group">
            <label className="govuk-label govuk-label--s" htmlFor="af-start">Start date</label>
            <input
              className="govuk-input govuk-input--width-10"
              type="date" id="af-start" value={v.start_date} onChange={set("start_date")}
            />
          </div>
        </div>
        <div className="govuk-grid-column-one-half">
          <div className="govuk-form-group">
            <label className="govuk-label govuk-label--s" htmlFor="af-due">Target date</label>
            <input
              className="govuk-input govuk-input--width-10"
              type="date" id="af-due" value={v.due_date} onChange={set("due_date")}
            />
          </div>
        </div>
      </div>

      <div className="govuk-grid-row">
        <div className="govuk-grid-column-one-half">
          <div className="govuk-form-group">
            <label className="govuk-label govuk-label--s" htmlFor="af-rev">Review date</label>
            <input
              className="govuk-input govuk-input--width-10"
              type="date" id="af-rev" value={v.review_date} onChange={set("review_date")}
            />
          </div>
        </div>
        <div className="govuk-grid-column-one-half">
          <div className="govuk-form-group">
            <label className="govuk-label govuk-label--s" htmlFor="af-comp">Completed date</label>
            <input
              className="govuk-input govuk-input--width-10"
              type="date" id="af-comp" value={v.completed_date} onChange={set("completed_date")}
            />
          </div>
        </div>
      </div>

      <div className="govuk-form-group">
        <label className="govuk-label govuk-label--s" htmlFor="af-sc">Success criteria</label>
        <textarea className="govuk-textarea" id="af-sc" rows={3} value={v.success_criteria} onChange={set("success_criteria")} />
      </div>

      <div className="govuk-form-group">
        <label className="govuk-label govuk-label--s" htmlFor="af-notes">Notes</label>
        <textarea className="govuk-textarea" id="af-notes" rows={3} value={v.notes} onChange={set("notes")} />
      </div>

      <div className="govuk-form-group">
        <label className="govuk-label govuk-label--s" htmlFor="af-st">Status</label>
        <select className="govuk-select" id="af-st" value={v.status} onChange={set("status")}>
          {ACTION_STATUSES.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
        </select>
      </div>

      <div className="govuk-button-group">
        <button className="govuk-button" type="submit">{submitLabel}</button>
        <button className="govuk-button govuk-button--secondary" type="button" onClick={onCancel}>Cancel</button>
      </div>
    </form>
  );
}

export default function ActionsPanel({ assetId }: { assetId: string }) {
  const [actions, setActions] = useState<Action[]>([]);
  const [issues, setIssues] = useState<Issue[]>([]);
  const [showAdd, setShowAdd] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  const loadActions = () => api.get<Action[]>(`/api/assets/${assetId}/actions`).then(setActions);

  useEffect(() => {
    loadActions();
    api.get<Issue[]>(`/api/assets/${assetId}/issues`).then(setIssues);
  }, [assetId]);

  async function addAction(body: Record<string, unknown>) {
    await api.post(`/api/assets/${assetId}/actions`, body);
    setShowAdd(false);
    loadActions();
  }

  async function editAction(id: string, body: Record<string, unknown>) {
    await api.patch(`/api/actions/${id}`, body);
    setEditingId(null);
    loadActions();
  }

  function linkedIssueTitle(issueId: string | undefined): string {
    if (!issueId) return "";
    return issues.find(i => i.id === issueId)?.title ?? issueId;
  }

  return (
    <>
      <h2 className="govuk-heading-l">Improvement actions</h2>

      {actions.map(a => (
        <div key={a.id} className="govuk-!-margin-bottom-6">
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
            <strong className={`govuk-tag ${actionTagClass(a.status)}`}>
              {a.status.replace(/_/g, " ")}
            </strong>
            <strong className={`govuk-tag ${priorityClass(a.priority)}`}>{a.priority}</strong>
            <span className="govuk-body-l govuk-!-font-weight-bold govuk-!-margin-bottom-0">{a.title}</span>
          </div>

          {editingId === a.id ? (
            <div className="govuk-!-margin-top-3">
              <ActionForm
                initial={toState(a)}
                issues={issues}
                onSubmit={body => editAction(a.id, body)}
                onCancel={() => setEditingId(null)}
                submitLabel="Save changes"
              />
            </div>
          ) : (
            <>
              <SummaryList rows={[
                { key: "Description", value: a.description ?? "" },
                { key: "Linked issue", value: linkedIssueTitle(a.issue_id) },
                { key: "Remediation type", value: a.remediation_type?.replace(/_/g, " ") ?? "" },
                { key: "Assignee", value: a.assignee_email ?? "" },
                { key: "Start date", value: a.start_date ?? "" },
                { key: "Target date", value: a.due_date ?? "" },
                { key: "Review date", value: a.review_date ?? "" },
                { key: "Completed date", value: a.completed_date ?? "" },
                { key: "Success criteria", value: a.success_criteria ?? "" },
                { key: "Notes", value: a.notes ?? "" },
              ]} />
              <AuditLine
                created_by={a.created_by}
                created_at={a.created_at}
                updated_by={a.updated_by}
                updated_at={a.updated_at}
              />
              <div className="govuk-button-group govuk-!-margin-top-2">
                <button
                  className="govuk-button govuk-button--secondary govuk-!-margin-bottom-0"
                  onClick={() => setEditingId(a.id)}
                >
                  Edit
                </button>
              </div>
            </>
          )}
        </div>
      ))}

      {showAdd ? (
        <div>
          <h3 className="govuk-heading-m">Add a new action</h3>
          <ActionForm
            initial={BLANK}
            issues={issues}
            onSubmit={addAction}
            onCancel={() => setShowAdd(false)}
            submitLabel="Add action"
          />
        </div>
      ) : (
        <button
          className="govuk-button govuk-button--secondary"
          onClick={() => setShowAdd(true)}
        >
          Add an action
        </button>
      )}
    </>
  );
}
