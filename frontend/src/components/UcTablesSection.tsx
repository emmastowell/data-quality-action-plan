import { useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import type { AssetTable } from "../api/types";
import AuditLine from "./AuditLine";

interface UcTable { name: string; full_name: string; table_type: string | null; }

export default function UcTablesSection({ assetId }: { assetId: string }) {
  const [linked, setLinked] = useState<AssetTable[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [showPicker, setShowPicker] = useState(false);

  // Cascading picker state
  const [catalogs, setCatalogs] = useState<string[]>([]);
  const [catalog, setCatalog] = useState("");
  const [schemas, setSchemas] = useState<string[]>([]);
  const [schema, setSchema] = useState("");
  const [tables, setTables] = useState<UcTable[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const [catalogsLoading, setCatalogsLoading] = useState(false);
  const [schemasLoading, setSchemasLoading] = useState(false);
  const [tablesLoading, setTablesLoading] = useState(false);
  const [addingLoading, setAddingLoading] = useState(false);

  // Track whether catalogs have been fetched for this picker session
  const catalogsFetched = useRef(false);

  function loadLinked() {
    api.get<AssetTable[]>(`/api/assets/${assetId}/tables`)
      .then(setLinked)
      .catch(err => setError(err instanceof Error ? err.message : "Could not load linked tables."));
  }

  useEffect(() => { loadLinked(); }, [assetId]);

  async function openPicker() {
    setShowPicker(true);
    if (!catalogsFetched.current) {
      catalogsFetched.current = true;
      setCatalogsLoading(true);
      try {
        const res = await api.get<{ catalogs: string[] }>("/api/uc/catalogs");
        setCatalogs(res.catalogs);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not load catalogs.");
      } finally {
        setCatalogsLoading(false);
      }
    }
  }

  function closePicker() {
    setShowPicker(false);
    setCatalog("");
    setSchemas([]);
    setSchema("");
    setTables([]);
    setSelected(new Set());
    catalogsFetched.current = false;
  }

  async function onCatalogChange(e: React.ChangeEvent<HTMLSelectElement>) {
    const val = e.target.value;
    setCatalog(val);
    setSchema("");
    setSchemas([]);
    setTables([]);
    setSelected(new Set());
    if (!val) return;
    setSchemasLoading(true);
    try {
      const res = await api.get<{ schemas: string[] }>(`/api/uc/schemas?catalog=${encodeURIComponent(val)}`);
      setSchemas(res.schemas);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load schemas.");
    } finally {
      setSchemasLoading(false);
    }
  }

  async function onSchemaChange(e: React.ChangeEvent<HTMLSelectElement>) {
    const val = e.target.value;
    setSchema(val);
    setTables([]);
    setSelected(new Set());
    if (!val) return;
    setTablesLoading(true);
    try {
      const res = await api.get<{ tables: UcTable[] }>(
        `/api/uc/tables?catalog=${encodeURIComponent(catalog)}&schema=${encodeURIComponent(val)}`
      );
      setTables(res.tables);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load tables.");
    } finally {
      setTablesLoading(false);
    }
  }

  function toggleTable(fullName: string) {
    setSelected(prev => {
      const next = new Set(prev);
      if (next.has(fullName)) next.delete(fullName); else next.add(fullName);
      return next;
    });
  }

  async function addSelected() {
    if (!selected.size) return;
    setAddingLoading(true);
    setError(null);
    try {
      await Promise.all(
        tables
          .filter(t => selected.has(t.full_name))
          .map(t =>
            api.post(`/api/assets/${assetId}/tables`, {
              catalog_name: catalog,
              schema_name: schema,
              table_name: t.name,
            }).catch(err => {
              // 409 conflict = already linked — safe to ignore.
              // The api client throws the backend message ("resource already exists"),
              // not the HTTP status code, so match on the message text.
              const msg: string = err instanceof Error ? err.message : "";
              if (!msg.includes("already exists")) throw err;
            })
          )
      );
      loadLinked();
      closePicker();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not add tables. Please try again.");
    } finally {
      setAddingLoading(false);
    }
  }

  async function removeTable(tableId: string) {
    setError(null);
    try {
      await api.del(`/api/asset-tables/${tableId}`);
      loadLinked();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not remove table. Please try again.");
    }
  }

  return (
    <div className="govuk-!-margin-bottom-6">
      <h2 className="govuk-heading-m">Unity Catalog tables</h2>

      {error && (
        <p className="govuk-error-message" role="alert">
          <span className="govuk-visually-hidden">Error:</span> {error}
        </p>
      )}

      {linked.length === 0 ? (
        <p className="govuk-body govuk-hint">No Unity Catalog tables linked yet.</p>
      ) : (
        <table className="govuk-table govuk-!-margin-bottom-3">
          <thead className="govuk-table__head">
            <tr className="govuk-table__row">
              <th scope="col" className="govuk-table__header">Full name</th>
              <th scope="col" className="govuk-table__header">Linked</th>
              <th scope="col" className="govuk-table__header">Action</th>
            </tr>
          </thead>
          <tbody className="govuk-table__body">
            {linked.map(t => (
              <tr className="govuk-table__row" key={t.id}>
                <td className="govuk-table__cell">
                  <code>{t.full_name}</code>
                </td>
                <td className="govuk-table__cell">
                  <AuditLine created_by={t.created_by} created_at={t.created_at} />
                </td>
                <td className="govuk-table__cell">
                  <button
                    className="govuk-button govuk-button--secondary govuk-!-margin-bottom-0"
                    onClick={() => removeTable(t.id)}
                  >
                    Remove
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {!showPicker ? (
        <button
          className="govuk-button govuk-button--secondary"
          onClick={openPicker}
        >
          Add tables
        </button>
      ) : (
        <div className="govuk-!-margin-top-2">
          <h3 className="govuk-heading-s">Add Unity Catalog tables</h3>

          {/* Catalog select */}
          <div className="govuk-form-group">
            <label className="govuk-label" htmlFor="uc-catalog-select">
              Catalog
            </label>
            {catalogsLoading && (
              <p className="govuk-hint">Loading catalogs…</p>
            )}
            {!catalogsLoading && (
              <select
                className="govuk-select"
                id="uc-catalog-select"
                value={catalog}
                onChange={onCatalogChange}
                disabled={catalogsLoading}
              >
                <option value="">— select catalog —</option>
                {catalogs.map(c => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            )}
          </div>

          {/* Schema select — shown once a catalog is chosen */}
          {catalog && (
            <div className="govuk-form-group">
              <label className="govuk-label" htmlFor="uc-schema-select">
                Schema
              </label>
              {schemasLoading && (
                <p className="govuk-hint">Loading schemas…</p>
              )}
              {!schemasLoading && (
                <select
                  className="govuk-select"
                  id="uc-schema-select"
                  value={schema}
                  onChange={onSchemaChange}
                  disabled={schemasLoading}
                >
                  <option value="">— select schema —</option>
                  {schemas.map(s => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              )}
            </div>
          )}

          {/* Tables checkboxes — shown once a schema is chosen */}
          {schema && (
            <div className="govuk-form-group">
              <fieldset className="govuk-fieldset">
                <legend className="govuk-fieldset__legend govuk-fieldset__legend--s">
                  Tables
                </legend>
                {tablesLoading && (
                  <p className="govuk-hint">Loading tables…</p>
                )}
                {!tablesLoading && tables.length === 0 && (
                  <p className="govuk-hint">No tables found in this schema.</p>
                )}
                {!tablesLoading && tables.length > 0 && (
                  <div className="govuk-checkboxes govuk-checkboxes--small">
                    {tables.map(t => (
                      <div className="govuk-checkboxes__item" key={t.full_name}>
                        <input
                          className="govuk-checkboxes__input"
                          id={`uc-table-${t.full_name}`}
                          type="checkbox"
                          checked={selected.has(t.full_name)}
                          onChange={() => toggleTable(t.full_name)}
                        />
                        <label
                          className="govuk-label govuk-checkboxes__label"
                          htmlFor={`uc-table-${t.full_name}`}
                        >
                          {t.full_name}
                        </label>
                      </div>
                    ))}
                  </div>
                )}
              </fieldset>
            </div>
          )}

          <div className="govuk-button-group">
            <button
              className="govuk-button"
              onClick={addSelected}
              disabled={selected.size === 0 || addingLoading}
            >
              {addingLoading ? "Adding…" : "Add selected tables"}
            </button>
            <button
              className="govuk-button govuk-button--secondary"
              onClick={closePicker}
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
