import { useState } from "react";
import type { Asset } from "../api/types";

type Values = Partial<Asset> & { name?: string };
export default function AssetForm({ initial, onSubmit }: { initial?: Values; onSubmit: (v: Values) => void }) {
  const [v, setV] = useState<Values>(initial ?? { criticality: "medium", status: "draft", kind: "critical" });
  const [error, setError] = useState<string>();
  const set = (k: keyof Values) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => setV({ ...v, [k]: e.target.value });
  function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!v.name?.trim()) { setError("Enter a name for the data asset"); return; }
    setError(undefined); onSubmit(v);
  }
  return (
    <form onSubmit={submit}>
      {error && (
        <div className="govuk-error-summary" role="alert">
          <h2 className="govuk-error-summary__title">There is a problem</h2>
          <div className="govuk-error-summary__body"><p className="govuk-body">{error}</p></div>
        </div>
      )}
      <div className="govuk-form-group">
        <label className="govuk-label" htmlFor="name">Name</label>
        <input className="govuk-input" id="name" value={v.name ?? ""} onChange={set("name")} />
      </div>
      <div className="govuk-form-group">
        <label className="govuk-label" htmlFor="purpose">Business purpose</label>
        <textarea className="govuk-textarea" id="purpose" value={v.business_purpose ?? ""} onChange={set("business_purpose")} />
      </div>
      <div className="govuk-form-group">
        <label className="govuk-label" htmlFor="owner">Owner email</label>
        <input className="govuk-input" id="owner" value={v.owner_email ?? ""} onChange={set("owner_email")} />
      </div>
      <div className="govuk-form-group">
        <label className="govuk-label" htmlFor="crit">Criticality</label>
        <select className="govuk-select" id="crit" value={v.criticality} onChange={set("criticality")}>
          <option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option>
        </select>
      </div>
      <div className="govuk-form-group">
        <label className="govuk-label" htmlFor="kind">Asset kind</label>
        <select className="govuk-select" id="kind" value={v.kind ?? "critical"} onChange={set("kind")}>
          <option value="critical">Critical</option>
          <option value="monitored">Monitored</option>
        </select>
      </div>
      <div className="govuk-form-group">
        <label className="govuk-label" htmlFor="status">Status</label>
        <select className="govuk-select" id="status" value={v.status} onChange={set("status")}>
          <option value="draft">Draft</option><option value="active">Active</option><option value="archived">Archived</option>
        </select>
      </div>
      <button className="govuk-button" type="submit">Save</button>
    </form>
  );
}
