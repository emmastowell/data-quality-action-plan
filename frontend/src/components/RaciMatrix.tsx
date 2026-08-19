import { Fragment, useEffect, useState } from "react";
import { api } from "../api/client";
import type { RaciMatrixData, RaciRole } from "../api/types";

export default function RaciMatrix() {
  const [data, setData] = useState<RaciMatrixData | null>(null);
  const [err, setErr] = useState<string>();
  const [newRole, setNewRole] = useState("");
  const [editing, setEditing] = useState(false);
  const load = () => api.get<RaciMatrixData>("/api/raci").then(setData).catch(e => setErr(e.message));
  useEffect(() => { load(); }, []);

  async function addRole() {
    const name = newRole.trim();
    if (!name) return;
    try { setErr(undefined); await api.post("/api/raci/roles", { name }); setNewRole(""); load(); }
    catch (e) { setErr((e as Error).message); }
  }
  async function removeRole(role: RaciRole) {
    if (!confirm(`Remove role "${role.name}" and its responsibilities?`)) return;
    try { setErr(undefined); await api.del(`/api/raci/roles/${role.id}`); load(); }
    catch (e) { setErr((e as Error).message); }
  }
  async function renameRole(role: RaciRole, name: string) {
    const trimmed = name.trim();
    if (!trimmed || trimmed === role.name) return;
    try { setErr(undefined); await api.patch(`/api/raci/roles/${role.id}`, { name: trimmed }); load(); }
    catch (e) { setErr((e as Error).message); load(); }
  }
  async function saveCell(activityKey: string, roleId: string, value: string) {
    try { setErr(undefined); await api.put("/api/raci/cells", { activity_key: activityKey, role_id: roleId, value }); }
    catch (e) { setErr((e as Error).message); load(); }
  }

  if (err && !data) return <p className="govuk-error-message">{err}</p>;
  if (!data) return <p className="govuk-body">Loading…</p>;

  // group activities by step_label, preserving order
  const groups: { step: string; keys: typeof data.activities }[] = [];
  for (const a of data.activities) {
    const g = groups.find(x => x.step === a.step_label);
    if (g) g.keys.push(a); else groups.push({ step: a.step_label, keys: [a] });
  }

  return (
    <div>
      <h2 className="govuk-heading-m">RACI matrix</h2>
      <p className="govuk-body">
        Your organisation's RACI matrix, seeded from the GOV.UK Data Quality Action Plan template.
        Select <strong>Edit RACI matrix</strong> to add or remove roles, rename them, or change
        responsibilities — changes apply across all assets.
      </p>
      <p className="govuk-body govuk-!-font-size-16">
        <strong>R</strong> = Responsible &nbsp; <strong>A</strong> = Accountable &nbsp;
        <strong>C</strong> = Consulted &nbsp; <strong>I</strong> = Informed
      </p>
      {err && <p className="govuk-error-message">{err}</p>}

      <button className="govuk-button govuk-button--secondary" onClick={() => setEditing(v => !v)}>
        {editing ? "Done editing" : "Edit RACI matrix"}
      </button>

      {editing && (
        <div className="govuk-form-group" style={{ display: "flex", gap: "0.5rem", alignItems: "flex-end" }}>
          <div style={{ flex: "0 0 auto" }}>
            <label className="govuk-label" htmlFor="new-role">Add a role</label>
            <input className="govuk-input" id="new-role" style={{ width: "16rem" }}
                   value={newRole} onChange={e => setNewRole(e.target.value)} />
          </div>
          <button className="govuk-button govuk-button--secondary govuk-!-margin-bottom-0" onClick={addRole}>
            Add role
          </button>
        </div>
      )}

      <div style={{ overflowX: "auto", maxWidth: "100%", width: "100%" }}>
        <table className="govuk-table" style={{ width: "100%", tableLayout: "fixed", minWidth: "640px" }}>
          <thead className="govuk-table__head">
            <tr className="govuk-table__row">
              <th scope="col" className="govuk-table__header" style={{ verticalAlign: "bottom", width: "22%" }}>Activity</th>
              {data.roles.map(role => (
                <th key={role.id} scope="col" className="govuk-table__header"
                    style={{ verticalAlign: "bottom", overflowWrap: "anywhere" }}>
                  {editing ? (
                    <>
                      <input key={`role-${role.id}-${role.name}`} className="govuk-input"
                             defaultValue={role.name} onBlur={e => renameRole(role, e.target.value)} />
                      <br />
                      <button
                        style={{ background: "none", border: 0, padding: 0, color: "#d4351c", cursor: "pointer", font: "inherit" }}
                        onClick={() => removeRole(role)}>Remove</button>
                    </>
                  ) : role.name}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="govuk-table__body">
            {groups.map(group => (
              <Fragment key={group.step}>
                <tr className="govuk-table__row" style={{ backgroundColor: "#f3f2f1" }}>
                  <td className="govuk-table__cell" colSpan={data.roles.length + 1}
                      style={{ fontWeight: "bold" }}>{group.step}</td>
                </tr>
                {group.keys.map(act => (
                  <tr key={act.key} className="govuk-table__row">
                    <td className="govuk-table__cell">{act.activity_label}</td>
                    {data.roles.map(role => (
                      <td key={role.id} className="govuk-table__cell" style={{ overflowWrap: "anywhere" }}>
                        {editing ? (
                          <input
                            key={`${act.key}-${role.id}-${data.cells[act.key]?.[role.id] ?? ""}`}
                            className="govuk-input"
                            defaultValue={data.cells[act.key]?.[role.id] ?? ""}
                            onBlur={e => saveCell(act.key, role.id, e.target.value.trim())} />
                        ) : (data.cells[act.key]?.[role.id] ?? "")}
                      </td>
                    ))}
                  </tr>
                ))}
              </Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
