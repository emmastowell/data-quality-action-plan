import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Issue, Rule, Dimension } from "../api/types";
import AuditLine from "./AuditLine";
import { SummaryList, priorityClass } from "./shared";

const DIMS: Dimension[] = ["completeness","accuracy","validity","timeliness","uniqueness","consistency"];
const ROOT_CAUSE_CATS = ["People","Process","System","Data","Standards","Governance"];
const IMPACT_OPTIONS = ["reputational","legal","financial","operational"];

interface IssueFormState {
  title: string; description: string; rule_id: string; dimension: string;
  reported_by: string; assigned_to: string; business_area: string;
  data_subject: string; impacted_systems: string; example_reference: string;
  system_owner: string; related_issues: string; comments: string;
  priority: string; severity: string; likelihood: string;
  impact_tags: string[];
  root_cause_category: string; contributing_factors: string; root_cause_detail: string;
  status: string; status_date: string;
}

const BLANK: IssueFormState = {
  title: "", description: "", rule_id: "", dimension: "",
  reported_by: "", assigned_to: "", business_area: "", data_subject: "",
  impacted_systems: "", example_reference: "", system_owner: "",
  related_issues: "", comments: "", priority: "medium", severity: "medium",
  likelihood: "medium", impact_tags: [], root_cause_category: "",
  contributing_factors: "", root_cause_detail: "", status: "open", status_date: "",
};

function toState(i: Issue): IssueFormState {
  return {
    title: i.title, description: i.description ?? "", rule_id: i.rule_id ?? "",
    dimension: i.dimension ?? "", reported_by: i.reported_by ?? "",
    assigned_to: i.assigned_to ?? "", business_area: i.business_area ?? "",
    data_subject: i.data_subject ?? "", impacted_systems: i.impacted_systems ?? "",
    example_reference: i.example_reference ?? "", system_owner: i.system_owner ?? "",
    related_issues: i.related_issues ?? "", comments: i.comments ?? "",
    priority: i.priority ?? "medium", severity: i.severity, likelihood: i.likelihood,
    impact_tags: i.impact_tags,
    root_cause_category: i.root_cause_category ?? "",
    contributing_factors: i.contributing_factors ?? "",
    root_cause_detail: i.root_cause_detail ?? "",
    status: i.status, status_date: i.status_date ?? "",
  };
}

function cleanBody(v: IssueFormState): Record<string, unknown> {
  const body: Record<string, unknown> = { impact_tags: v.impact_tags };
  for (const [k, val] of Object.entries(v)) {
    if (k === "impact_tags") continue;
    if (val !== "" && val !== undefined) body[k] = val;
  }
  return body;
}

function issueTagClass(status: string): string {
  const m: Record<string, string> = {
    open: "govuk-tag--red", in_progress: "govuk-tag--yellow",
    blocked: "govuk-tag--orange", resolved: "govuk-tag--green",
  };
  return m[status] ?? "";
}

interface IssueFormProps {
  initial: IssueFormState;
  rules: Rule[];
  onSubmit: (body: Record<string, unknown>) => Promise<void>;
  onCancel: () => void;
  submitLabel: string;
}

export function IssueForm({ initial, rules, onSubmit, onCancel, submitLabel }: IssueFormProps) {
  const [v, setV] = useState<IssueFormState>(initial);
  const [titleError, setTitleError] = useState<string>();
  const [submitError, setSubmitError] = useState<string>();

  const set = (k: keyof Omit<IssueFormState, "impact_tags">) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
      setV(prev => ({ ...prev, [k]: e.target.value }));

  function toggleTag(tag: string) {
    setV(prev => ({
      ...prev,
      impact_tags: prev.impact_tags.includes(tag)
        ? prev.impact_tags.filter(t => t !== tag)
        : [...prev.impact_tags, tag],
    }));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!v.title.trim()) { setTitleError("Enter a title for the issue"); return; }
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
        <label className="govuk-label govuk-label--s" htmlFor="if-title">
          Title <span aria-hidden="true">*</span>
        </label>
        {titleError && <p className="govuk-error-message" id="if-title-err">{titleError}</p>}
        <input
          className={`govuk-input govuk-input--width-30${titleError ? " govuk-input--error" : ""}`}
          id="if-title" value={v.title} onChange={set("title")}
          aria-describedby={titleError ? "if-title-err" : undefined}
        />
      </div>

      <div className="govuk-form-group">
        <label className="govuk-label govuk-label--s" htmlFor="if-desc">Description</label>
        <textarea className="govuk-textarea" id="if-desc" rows={3} value={v.description} onChange={set("description")} />
      </div>

      <div className="govuk-grid-row">
        <div className="govuk-grid-column-one-half">
          <div className="govuk-form-group">
            <label className="govuk-label govuk-label--s" htmlFor="if-rule">Rule</label>
            <select className="govuk-select" id="if-rule" value={v.rule_id} onChange={set("rule_id")}>
              <option value="">— none —</option>
              {rules.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}
            </select>
          </div>
        </div>
        <div className="govuk-grid-column-one-half">
          <div className="govuk-form-group">
            <label className="govuk-label govuk-label--s" htmlFor="if-dim">Dimension</label>
            <select className="govuk-select" id="if-dim" value={v.dimension} onChange={set("dimension")}>
              <option value="">— none —</option>
              {DIMS.map(d => <option key={d} value={d}>{d}</option>)}
            </select>
          </div>
        </div>
      </div>

      <div className="govuk-grid-row">
        <div className="govuk-grid-column-one-third">
          <div className="govuk-form-group">
            <label className="govuk-label govuk-label--s" htmlFor="if-sev">Severity</label>
            <select className="govuk-select" id="if-sev" value={v.severity} onChange={set("severity")}>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
        </div>
        <div className="govuk-grid-column-one-third">
          <div className="govuk-form-group">
            <label className="govuk-label govuk-label--s" htmlFor="if-lik">Likelihood</label>
            <select className="govuk-select" id="if-lik" value={v.likelihood} onChange={set("likelihood")}>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
        </div>
        <div className="govuk-grid-column-one-third">
          <div className="govuk-form-group">
            <label className="govuk-label govuk-label--s" htmlFor="if-pri">Priority</label>
            <select className="govuk-select" id="if-pri" value={v.priority} onChange={set("priority")}>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
        </div>
      </div>

      <div className="govuk-form-group">
        <fieldset className="govuk-fieldset">
          <legend className="govuk-fieldset__legend govuk-fieldset__legend--s">Impact</legend>
          <div className="govuk-checkboxes govuk-checkboxes--small">
            {IMPACT_OPTIONS.map(tag => (
              <div className="govuk-checkboxes__item" key={tag}>
                <input
                  className="govuk-checkboxes__input"
                  id={`if-impact-${tag}`}
                  type="checkbox"
                  checked={v.impact_tags.includes(tag)}
                  onChange={() => toggleTag(tag)}
                />
                <label className="govuk-label govuk-checkboxes__label" htmlFor={`if-impact-${tag}`}>
                  {tag.charAt(0).toUpperCase() + tag.slice(1)}
                </label>
              </div>
            ))}
          </div>
        </fieldset>
      </div>

      <div className="govuk-grid-row">
        <div className="govuk-grid-column-one-half">
          <div className="govuk-form-group">
            <label className="govuk-label govuk-label--s" htmlFor="if-rep">Reported by</label>
            <input className="govuk-input" id="if-rep" value={v.reported_by} onChange={set("reported_by")} />
          </div>
        </div>
        <div className="govuk-grid-column-one-half">
          <div className="govuk-form-group">
            <label className="govuk-label govuk-label--s" htmlFor="if-asgn">Assigned to (SME)</label>
            <input className="govuk-input" id="if-asgn" value={v.assigned_to} onChange={set("assigned_to")} />
          </div>
        </div>
      </div>

      <div className="govuk-grid-row">
        <div className="govuk-grid-column-one-half">
          <div className="govuk-form-group">
            <label className="govuk-label govuk-label--s" htmlFor="if-ba">Business area</label>
            <input className="govuk-input" id="if-ba" value={v.business_area} onChange={set("business_area")} />
          </div>
        </div>
        <div className="govuk-grid-column-one-half">
          <div className="govuk-form-group">
            <label className="govuk-label govuk-label--s" htmlFor="if-ds">Data subject</label>
            <input className="govuk-input" id="if-ds" value={v.data_subject} onChange={set("data_subject")} />
          </div>
        </div>
      </div>

      <div className="govuk-grid-row">
        <div className="govuk-grid-column-one-half">
          <div className="govuk-form-group">
            <label className="govuk-label govuk-label--s" htmlFor="if-is">Impacted systems</label>
            <input className="govuk-input" id="if-is" value={v.impacted_systems} onChange={set("impacted_systems")} />
          </div>
        </div>
        <div className="govuk-grid-column-one-half">
          <div className="govuk-form-group">
            <label className="govuk-label govuk-label--s" htmlFor="if-so">System owner</label>
            <input className="govuk-input" id="if-so" value={v.system_owner} onChange={set("system_owner")} />
          </div>
        </div>
      </div>

      <div className="govuk-form-group">
        <label className="govuk-label govuk-label--s" htmlFor="if-ex">Example record / link</label>
        <input className="govuk-input" id="if-ex" value={v.example_reference} onChange={set("example_reference")} />
      </div>

      <div className="govuk-form-group">
        <label className="govuk-label govuk-label--s" htmlFor="if-ri">Related issues</label>
        <textarea className="govuk-textarea" id="if-ri" rows={2} value={v.related_issues} onChange={set("related_issues")} />
      </div>

      <div className="govuk-form-group">
        <label className="govuk-label govuk-label--s" htmlFor="if-rcc">Root cause category</label>
        <select className="govuk-select" id="if-rcc" value={v.root_cause_category} onChange={set("root_cause_category")}>
          <option value="">— none —</option>
          {ROOT_CAUSE_CATS.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      <div className="govuk-form-group">
        <label className="govuk-label govuk-label--s" htmlFor="if-cf">Contributing factors</label>
        <textarea className="govuk-textarea" id="if-cf" rows={3} value={v.contributing_factors} onChange={set("contributing_factors")} />
      </div>

      <div className="govuk-form-group">
        <label className="govuk-label govuk-label--s" htmlFor="if-rcd">Root cause to address</label>
        <textarea className="govuk-textarea" id="if-rcd" rows={3} value={v.root_cause_detail} onChange={set("root_cause_detail")} />
      </div>

      <div className="govuk-grid-row">
        <div className="govuk-grid-column-one-half">
          <div className="govuk-form-group">
            <label className="govuk-label govuk-label--s" htmlFor="if-st">Status</label>
            <select className="govuk-select" id="if-st" value={v.status} onChange={set("status")}>
              <option value="open">Open</option>
              <option value="in_progress">In progress</option>
              <option value="blocked">Blocked</option>
              <option value="resolved">Resolved</option>
            </select>
          </div>
        </div>
        <div className="govuk-grid-column-one-half">
          <div className="govuk-form-group">
            <label className="govuk-label govuk-label--s" htmlFor="if-sd">Status date</label>
            <input
              className="govuk-input govuk-input--width-10"
              type="date"
              id="if-sd"
              value={v.status_date}
              onChange={set("status_date")}
            />
          </div>
        </div>
      </div>

      <div className="govuk-form-group">
        <label className="govuk-label govuk-label--s" htmlFor="if-com">Comments</label>
        <textarea className="govuk-textarea" id="if-com" rows={3} value={v.comments} onChange={set("comments")} />
      </div>

      <div className="govuk-button-group">
        <button className="govuk-button" type="submit">{submitLabel}</button>
        <button className="govuk-button govuk-button--secondary" type="button" onClick={onCancel}>Cancel</button>
      </div>
    </form>
  );
}

export default function IssuesPanel({ assetId }: { assetId: string }) {
  const [issues, setIssues] = useState<Issue[]>([]);
  const [rules, setRules] = useState<Rule[]>([]);
  const [showAdd, setShowAdd] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [panelError, setPanelError] = useState<string | null>(null);

  const loadIssues = () => api.get<Issue[]>(`/api/assets/${assetId}/issues`).then(setIssues);

  useEffect(() => {
    loadIssues();
    api.get<Rule[]>(`/api/assets/${assetId}/rules`).then(setRules);
  }, [assetId]);

  async function addIssue(body: Record<string, unknown>) {
    await api.post(`/api/assets/${assetId}/issues`, body);
    setShowAdd(false);
    loadIssues();
  }

  async function editIssue(id: string, body: Record<string, unknown>) {
    await api.patch(`/api/issues/${id}`, body);
    setEditingId(null);
    loadIssues();
  }

  async function resolve(id: string) {
    try {
      await api.patch(`/api/issues/${id}`, { status: "resolved" });
      setPanelError(null);
      loadIssues();
    } catch (err) {
      setPanelError(err instanceof Error ? err.message : "Could not resolve issue. Please try again.");
    }
  }

  return (
    <>
      <h2 className="govuk-heading-l">Data issues</h2>
      {panelError && <p className="govuk-error-message">{panelError}</p>}

      {issues.map(i => (
        <div key={i.id} className="govuk-!-margin-bottom-6">
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
            <strong className={`govuk-tag ${issueTagClass(i.status)}`}>
              {i.status.replace(/_/g, " ")}
            </strong>
            {i.priority && (
              <strong className={`govuk-tag ${priorityClass(i.priority)}`}>{i.priority}</strong>
            )}
            <span className="govuk-body-l govuk-!-font-weight-bold govuk-!-margin-bottom-0">{i.title}</span>
          </div>

          {editingId === i.id ? (
            <div className="govuk-!-margin-top-3">
              <IssueForm
                initial={toState(i)}
                rules={rules}
                onSubmit={body => editIssue(i.id, body)}
                onCancel={() => setEditingId(null)}
                submitLabel="Save changes"
              />
            </div>
          ) : (
            <>
              <SummaryList rows={[
                { key: "Description", value: i.description ?? "" },
                { key: "Dimension", value: i.dimension ?? "" },
                { key: "Severity", value: i.severity },
                { key: "Likelihood", value: i.likelihood },
                { key: "Impact", value: i.impact_tags.join(", ") },
                { key: "Reported by", value: i.reported_by ?? "" },
                { key: "Assigned to", value: i.assigned_to ?? "" },
                { key: "Business area", value: i.business_area ?? "" },
                { key: "Data subject", value: i.data_subject ?? "" },
                { key: "Impacted systems", value: i.impacted_systems ?? "" },
                { key: "System owner", value: i.system_owner ?? "" },
                { key: "Example record", value: i.example_reference ?? "" },
                { key: "Related issues", value: i.related_issues ?? "" },
                { key: "Root cause category", value: i.root_cause_category ?? "" },
                { key: "Contributing factors", value: i.contributing_factors ?? "" },
                { key: "Root cause to address", value: i.root_cause_detail ?? "" },
                { key: "Status date", value: i.status_date ?? "" },
                { key: "Comments", value: i.comments ?? "" },
              ]} />
              <AuditLine
                created_by={i.created_by}
                created_at={i.created_at}
                updated_by={i.updated_by}
                updated_at={i.updated_at}
              />
              <div className="govuk-button-group govuk-!-margin-top-2">
                <button
                  className="govuk-button govuk-button--secondary govuk-!-margin-bottom-0"
                  onClick={() => setEditingId(i.id)}
                >
                  Edit
                </button>
                {i.status !== "resolved" && (
                  <button className="govuk-link" onClick={() => resolve(i.id)}>Resolve</button>
                )}
              </div>
            </>
          )}
        </div>
      ))}

      {showAdd ? (
        <div>
          <h3 className="govuk-heading-m">Log a new issue</h3>
          <IssueForm
            initial={BLANK}
            rules={rules}
            onSubmit={addIssue}
            onCancel={() => setShowAdd(false)}
            submitLabel="Log issue"
          />
        </div>
      ) : (
        <button
          className="govuk-button govuk-button--secondary"
          onClick={() => setShowAdd(true)}
        >
          Log an issue
        </button>
      )}
    </>
  );
}
