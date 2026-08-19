import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Rule, Measurement, Dimension } from "../api/types";
import ScoreTrend from "./ScoreTrend";
import AuditLine from "./AuditLine";

const DIMS: Dimension[] = ["completeness","accuracy","validity","timeliness","uniqueness","consistency"];

interface RunAllResult { rule_id: string; name: string; score?: number; error?: string; }

export default function RulesPanel({ assetId }: { assetId: string }) {
  const [rules, setRules] = useState<Rule[]>([]);
  const [trends, setTrends] = useState<Record<string, Measurement[]>>({});
  const [runningRule, setRunningRule] = useState<string | null>(null);
  const [editingSqlId, setEditingSqlId] = useState<string | null>(null);
  const [sqlDraft, setSqlDraft] = useState<Record<string, string>>({});
  const [runAllLoading, setRunAllLoading] = useState(false);
  const [runAllResults, setRunAllResults] = useState<RunAllResult[] | null>(null);
  const [panelError, setPanelError] = useState<string | null>(null);

  const load = async () => {
    const rs = await api.get<Rule[]>(`/api/assets/${assetId}/rules`);
    setRules(rs);
    const entries = await Promise.all(rs.map(async r =>
      [r.id, await api.get<Measurement[]>(`/api/rules/${r.id}/measurements`)] as const));
    setTrends(Object.fromEntries(entries));
  };

  const reloadMeasurements = async (ruleId: string) => {
    const ms = await api.get<Measurement[]>(`/api/rules/${ruleId}/measurements`);
    setTrends(prev => ({ ...prev, [ruleId]: ms }));
  };

  useEffect(() => { load(); }, [assetId]);

  async function addRule(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    const sqlVal = (f.get("measurement_sql") as string ?? "").trim();
    setPanelError(null);
    try {
      await api.post(`/api/assets/${assetId}/rules`, {
        name: f.get("name"), dimension: f.get("dimension"),
        target_threshold: Number(f.get("target")) || null,
        ...(sqlVal ? { measurement_sql: sqlVal } : {}),
      });
      e.currentTarget.reset();
      await load();
    } catch (err) {
      setPanelError(err instanceof Error ? err.message : "Could not add rule. Please try again.");
    }
  }

  async function recordScore(ruleId: string, score: number) {
    await api.post(`/api/rules/${ruleId}/measurements`, { score });
    load();
  }

  async function runNow(ruleId: string) {
    setRunningRule(ruleId);
    setPanelError(null);
    setRunAllResults(null);
    try {
      await api.post<Measurement>(`/api/rules/${ruleId}/measure/run`, {});
      await reloadMeasurements(ruleId);
    } catch (err) {
      setPanelError(err instanceof Error ? err.message : "Could not run measurement. Please try again.");
    } finally {
      setRunningRule(null);
    }
  }

  async function saveSql(ruleId: string) {
    // Send "" (empty string) when cleared — NOT null. The backend treats a
    // blank measurement_sql as "no SQL" (the (.strip() checks), and exclude_none
    // would silently drop null leaving the old SQL in place.
    const sql = (sqlDraft[ruleId] ?? "").trim();
    setPanelError(null);
    try {
      await api.patch<Rule>(`/api/rules/${ruleId}`, { measurement_sql: sql });
      setEditingSqlId(null);
      await load();
    } catch (err) {
      setPanelError(err instanceof Error ? err.message : "Could not save SQL. Please try again.");
    }
  }

  async function runAll() {
    setRunAllLoading(true);
    setRunAllResults(null);
    setPanelError(null);
    try {
      const res = await api.post<{ results: RunAllResult[] }>(
        `/api/assets/${assetId}/measure/run-all`, {}
      );
      setRunAllResults(res.results);
      await load();
    } catch (err) {
      setPanelError(err instanceof Error ? err.message : "Could not run all measures. Please try again.");
    } finally {
      setRunAllLoading(false);
    }
  }

  const sqlRulesCount = rules.filter(r => r.measurement_sql).length;

  return (
    <>
      <h2 className="govuk-heading-l">Rules &amp; assessment</h2>

      {panelError && (
        <p className="govuk-error-message" role="alert">{panelError}</p>
      )}

      <div className="govuk-!-margin-bottom-4" style={{ display: "flex", alignItems: "center", gap: "1rem", flexWrap: "wrap" }}>
        <button
          className="govuk-button govuk-button--secondary govuk-!-margin-bottom-0"
          onClick={runAll}
          disabled={runAllLoading || sqlRulesCount === 0}
        >
          {runAllLoading ? "Running…" : `Run all SQL measures${sqlRulesCount > 0 ? ` (${sqlRulesCount})` : ""}`}
        </button>
        {sqlRulesCount === 0 && (
          <span className="govuk-hint govuk-!-margin-bottom-0">Add measurement SQL to a rule to enable this.</span>
        )}
      </div>

      {runAllResults && (
        <div className="govuk-inset-text govuk-!-margin-bottom-4">
          <p className="govuk-body govuk-!-font-weight-bold govuk-!-margin-bottom-1">
            Ran {runAllResults.length} measure{runAllResults.length !== 1 ? "s" : ""},
            {" "}{runAllResults.filter(r => r.score !== undefined).length} succeeded.
          </p>
          <ul className="govuk-list govuk-list--bullet govuk-!-margin-bottom-0">
            {runAllResults.map(r => (
              <li key={r.rule_id}>
                <strong>{r.name}:</strong>{" "}
                {r.error
                  ? <span style={{ color: "#d4351c" }}>{r.error}</span>
                  : <span>{r.score}</span>}
              </li>
            ))}
          </ul>
        </div>
      )}

      <table className="govuk-table">
        <thead className="govuk-table__head">
          <tr className="govuk-table__row">
            <th className="govuk-table__header">Dimension</th>
            <th className="govuk-table__header">Rule</th>
            <th className="govuk-table__header">Target</th>
            <th className="govuk-table__header">Latest</th>
            <th className="govuk-table__header">Trend</th>
            <th className="govuk-table__header">Measure</th>
          </tr>
        </thead>
        <tbody className="govuk-table__body">
          {rules.map(r => {
            const ms = trends[r.id] ?? [];
            const latest = ms.length ? ms[ms.length - 1].score : undefined;
            const isRunning = runningRule === r.id;
            const isEditingSql = editingSqlId === r.id;
            return (
              <tr className="govuk-table__row" key={r.id}>
                <td className="govuk-table__cell" style={{ textTransform: "capitalize" }}>{r.dimension}</td>
                <td className="govuk-table__cell">
                  <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", flexWrap: "wrap" }}>
                    <span>{r.name}</span>
                    {r.measurement_sql && (
                      <strong className="govuk-tag govuk-tag--blue" style={{ fontSize: "0.75rem" }}>SQL</strong>
                    )}
                  </div>
                  <AuditLine
                    created_by={r.created_by} created_at={r.created_at}
                    updated_by={r.updated_by} updated_at={r.updated_at}
                  />
                  {isEditingSql ? (
                    <div className="govuk-!-margin-top-2">
                      <label className="govuk-label govuk-label--s" htmlFor={`sql-${r.id}`}>
                        Measurement SQL
                      </label>
                      <div className="govuk-hint">SELECT/WITH query returning one number</div>
                      <textarea
                        className="govuk-textarea"
                        id={`sql-${r.id}`}
                        rows={3}
                        value={sqlDraft[r.id] ?? r.measurement_sql ?? ""}
                        onChange={e => setSqlDraft(prev => ({ ...prev, [r.id]: e.target.value }))}
                        style={{ fontFamily: "monospace", fontSize: "0.8rem" }}
                      />
                      <div className="govuk-button-group govuk-!-margin-top-1">
                        <button
                          className="govuk-button govuk-button--secondary govuk-!-margin-bottom-0"
                          type="button"
                          onClick={() => saveSql(r.id)}
                        >
                          Save SQL
                        </button>
                        <button
                          className="govuk-link"
                          type="button"
                          onClick={() => setEditingSqlId(null)}
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div>
                      <button
                        className="govuk-link"
                        type="button"
                        style={{ fontSize: "0.8rem" }}
                        onClick={() => {
                          setSqlDraft(prev => ({ ...prev, [r.id]: r.measurement_sql ?? "" }));
                          setEditingSqlId(r.id);
                        }}
                      >
                        {r.measurement_sql ? "Edit SQL" : "Add SQL"}
                      </button>
                    </div>
                  )}
                </td>
                <td className="govuk-table__cell">{r.target_threshold ?? "—"}{r.unit}</td>
                <td className="govuk-table__cell">{latest ?? "—"}</td>
                <td className="govuk-table__cell"><ScoreTrend data={ms} /></td>
                <td className="govuk-table__cell">
                  {r.measurement_sql && (
                    <div className="govuk-!-margin-bottom-2">
                      <button
                        className="govuk-button govuk-button--secondary govuk-!-margin-bottom-0"
                        type="button"
                        disabled={isRunning}
                        onClick={() => runNow(r.id)}
                      >
                        {isRunning ? "Running…" : "Run now"}
                      </button>
                    </div>
                  )}
                  <form onSubmit={e => {
                    e.preventDefault();
                    const val = Number((e.currentTarget.elements.namedItem("s") as HTMLInputElement).value);
                    if (!Number.isNaN(val)) recordScore(r.id, val);
                  }}>
                    <input className="govuk-input govuk-input--width-4" name="s" type="number" step="0.1" />
                    <button className="govuk-button govuk-button--secondary" type="submit">Add</button>
                  </form>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      <form onSubmit={addRule} className="govuk-!-margin-top-4">
        <h3 className="govuk-heading-m">Add a rule</h3>
        <div className="govuk-form-group">
          <label className="govuk-label" htmlFor="ar-name">Rule name</label>
          <input
            className="govuk-input govuk-input--width-20"
            id="ar-name" name="name"
            placeholder="Rule name" required
          />
        </div>
        <div className="govuk-form-group">
          <label className="govuk-label" htmlFor="ar-dim">Dimension</label>
          <select className="govuk-select" id="ar-dim" name="dimension">
            {DIMS.map(d => <option key={d} value={d}>{d}</option>)}
          </select>
        </div>
        <div className="govuk-form-group">
          <label className="govuk-label" htmlFor="ar-target">Target (%)</label>
          <input
            className="govuk-input govuk-input--width-4"
            id="ar-target" name="target"
            type="number" step="0.1" placeholder="Target %"
          />
        </div>
        <div className="govuk-form-group">
          <label className="govuk-label" htmlFor="ar-sql">
            Measurement SQL <span className="govuk-visually-hidden">(optional)</span>
          </label>
          <div className="govuk-hint">
            Optional. A SELECT/WITH query returning one number, e.g.{" "}
            <code>SELECT 100.0*count_if(imo IS NOT NULL)/count(*) FROM catalog.schema.table</code>
          </div>
          <textarea
            className="govuk-textarea"
            id="ar-sql" name="measurement_sql"
            rows={3}
            style={{ fontFamily: "monospace" }}
          />
        </div>
        <button className="govuk-button" type="submit">Add rule</button>
      </form>
    </>
  );
}
