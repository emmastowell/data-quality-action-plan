import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../api/client";

type Row = { asset: string; dimension: string; rule: string; target_threshold: number | null; unit: string; latest_score: number | null; linked_issues: number };
export default function ExportPage() {
  const { id } = useParams<{ id: string }>();
  const [rows, setRows] = useState<Row[]>([]);
  useEffect(() => { if (id) api.get<Row[]>(`/api/assets/${id}/export`).then(setRows); }, [id]);
  return (
    <>
      <Link className="govuk-back-link" to={`/assets/${id}`}>Back to plan</Link>
      <h1 className="govuk-heading-xl">Export data quality action plan</h1>
      <a className="govuk-button" href={`/api/assets/${id}/export?format=csv`}>Download CSV</a>
      <table className="govuk-table">
        <thead className="govuk-table__head"><tr className="govuk-table__row">
          <th className="govuk-table__header">Dimension</th><th className="govuk-table__header">Rule</th>
          <th className="govuk-table__header">Target</th><th className="govuk-table__header">Latest score</th>
          <th className="govuk-table__header">Linked issues</th>
        </tr></thead>
        <tbody className="govuk-table__body">
          {rows.map((r, i) => (
            <tr className="govuk-table__row" key={i}>
              <td className="govuk-table__cell" style={{ textTransform: "capitalize" }}>{r.dimension}</td>
              <td className="govuk-table__cell">{r.rule}</td>
              <td className="govuk-table__cell">{r.target_threshold ?? "—"}{r.unit}</td>
              <td className="govuk-table__cell">{r.latest_score ?? "—"}</td>
              <td className="govuk-table__cell">{r.linked_issues}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
