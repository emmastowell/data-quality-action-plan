import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { DashboardSummary, Dimension } from "../api/types";

const DIMENSIONS: Dimension[] = ["completeness","accuracy","validity","timeliness","uniqueness","consistency"];

export default function Dashboard() {
  const [d, setD] = useState<DashboardSummary | null>(null);
  const [err, setErr] = useState<string>();
  useEffect(() => { api.get<DashboardSummary>("/api/dashboard").then(setD).catch(e => setErr(e.message)); }, []);
  if (err) return <p className="govuk-error-message">{err}</p>;
  if (!d) return <p className="govuk-body">Loading…</p>;
  return (
    <>
      <h1 className="govuk-heading-xl">Organisation data quality</h1>
      <dl className="govuk-summary-list">
        <div className="govuk-summary-list__row">
          <dt className="govuk-summary-list__key">Overall quality score</dt>
          <dd className="govuk-summary-list__value">{d.overall_score ?? "—"}%</dd>
        </div>
        <div className="govuk-summary-list__row">
          <dt className="govuk-summary-list__key">Critical assets</dt>
          <dd className="govuk-summary-list__value">{d.critical_active_count} of {d.critical_asset_count} active</dd>
        </div>
        <div className="govuk-summary-list__row">
          <dt className="govuk-summary-list__key">Monitored assets</dt>
          <dd className="govuk-summary-list__value">{d.monitored_active_count} of {d.monitored_asset_count} active</dd>
        </div>
        <div className="govuk-summary-list__row">
          <dt className="govuk-summary-list__key">Open issues</dt>
          <dd className="govuk-summary-list__value">{d.open_issue_count}</dd>
        </div>
        <div className="govuk-summary-list__row">
          <dt className="govuk-summary-list__key">Actions in progress</dt>
          <dd className="govuk-summary-list__value">{d.actions_in_progress}</dd>
        </div>
      </dl>

      <h2 className="govuk-heading-l">Score by dimension</h2>
      <table className="govuk-table">
        <tbody className="govuk-table__body">
          {DIMENSIONS.map(dim => (
            <tr className="govuk-table__row" key={dim}>
              <th className="govuk-table__header" style={{ textTransform: "capitalize" }}>{dim}</th>
              <td className="govuk-table__cell">{d.score_by_dimension[dim] ?? "—"}%</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2 className="govuk-heading-l">Assets at risk</h2>
      {d.assets_at_risk.length === 0 ? <p className="govuk-body">No assets below target.</p> : (
        <ul className="govuk-list govuk-list--bullet">
          {d.assets_at_risk.map(a => <li key={a.id}>{a.name} ({a.kind}) — {a.failing_rules} rule(s) below target</li>)}
        </ul>
      )}
    </>
  );
}
