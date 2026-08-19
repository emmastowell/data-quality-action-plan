import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { Asset } from "../api/types";
import StatusTag from "../components/StatusTag";
import AssetForm from "../components/AssetForm";

function AssetTable({ assets }: { assets: Asset[] }) {
  if (assets.length === 0) return <p className="govuk-body">None yet.</p>;
  return (
    <table className="govuk-table">
      <thead className="govuk-table__head"><tr className="govuk-table__row">
        <th scope="col" className="govuk-table__header">Name</th><th scope="col" className="govuk-table__header">Criticality</th>
        <th scope="col" className="govuk-table__header">Status</th>
      </tr></thead>
      <tbody className="govuk-table__body">
        {assets.map(a => (
          <tr className="govuk-table__row" key={a.id}>
            <td className="govuk-table__cell"><Link className="govuk-link" to={`/assets/${a.id}`}>{a.name}</Link></td>
            <td className="govuk-table__cell">{a.criticality}</td>
            <td className="govuk-table__cell"><StatusTag status={a.status} /></td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default function AssetsList() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [adding, setAdding] = useState(false);
  const [err, setErr] = useState<string>();
  const load = () => api.get<Asset[]>("/api/assets").then(setAssets).catch(e => setErr(e.message));
  useEffect(() => { load(); }, []);
  async function create(v: Partial<Asset>) {
    try { setErr(undefined); await api.post<Asset>("/api/assets", v); setAdding(false); load(); }
    catch (e) { setErr((e as Error).message); }
  }
  const critical = assets.filter(a => a.kind === "critical");
  const monitored = assets.filter(a => a.kind === "monitored");
  return (
    <>
      <h1 className="govuk-heading-xl">Data assets</h1>
      {err && <p className="govuk-error-message">{err}</p>}
      <p className="govuk-body">Each asset has its own data quality action plan.</p>
      <button className="govuk-button" onClick={() => setAdding(a => !a)}>
        {adding ? "Cancel" : "Add a data asset"}
      </button>
      {adding && <AssetForm onSubmit={create} />}
      <h2 className="govuk-heading-l">Critical data assets</h2>
      <AssetTable assets={critical} />
      <h2 className="govuk-heading-l">Monitored data assets</h2>
      <AssetTable assets={monitored} />
    </>
  );
}
