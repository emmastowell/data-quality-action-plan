import { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import type { Asset } from "../api/types";
import StatusTag from "../components/StatusTag";
import JourneyTaskList from "../components/JourneyTaskList";
import RulesPanel from "../components/RulesPanel";
import IssuesPanel from "../components/IssuesPanel";
import ActionsPanel from "../components/ActionsPanel";
import AssetForm from "../components/AssetForm";
import RaciMatrix from "../components/RaciMatrix";
import UcTablesSection from "../components/UcTablesSection";

type Tab = "journey" | "rules" | "issues" | "actions" | "raci";

const TABS: { id: Tab; label: string }[] = [
  { id: "journey", label: "Action plan progress" },
  { id: "rules", label: "Rules & assessment" },
  { id: "issues", label: "Data issues" },
  { id: "actions", label: "Improvement actions" },
  { id: "raci", label: "RACI matrix" },
];

export default function AssetDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [asset, setAsset] = useState<Asset | null>(null);
  const [editing, setEditing] = useState(false);
  const [activeTab, setActiveTab] = useState<Tab>("journey");

  function loadAsset() {
    if (id) api.get<Asset>(`/api/assets/${id}`).then(setAsset);
  }

  useEffect(() => { loadAsset(); }, [id]);

  async function save(values: Partial<Asset> & { name?: string }) {
    await api.patch(`/api/assets/${id}`, values);
    setEditing(false);
    loadAsset();
  }

  async function archive() {
    if (!confirm("Archive this asset? It will no longer appear as active.")) return;
    await api.del(`/api/assets/${id}`);
    navigate("/assets");
  }

  if (!asset || !id) return <p className="govuk-body">Loading…</p>;

  return (
    <>
      <Link className="govuk-back-link" to="/assets">Back to assets</Link>
      <h1 className="govuk-heading-xl">{asset.name} <StatusTag status={asset.status} /></h1>
      {asset.business_purpose && <p className="govuk-body">{asset.business_purpose}</p>}

      <div className="govuk-button-group">
        <button
          className="govuk-button govuk-button--secondary"
          onClick={() => setEditing(!editing)}
        >
          {editing ? "Cancel edit" : "Edit asset"}
        </button>
        <button
          className="govuk-button govuk-button--warning"
          onClick={archive}
        >
          Archive
        </button>
        <Link className="govuk-link" to={`/assets/${id}/export`}>Export this plan</Link>
      </div>

      {editing && (
        <div className="govuk-!-margin-bottom-6">
          <AssetForm initial={asset} onSubmit={save} />
        </div>
      )}

      <div className="govuk-!-margin-top-6 govuk-!-margin-bottom-6">
        <UcTablesSection assetId={id} />
      </div>

      <div className="govuk-tabs govuk-!-margin-top-6">
        <ul className="govuk-tabs__list" role="tablist">
          {TABS.map(tab => (
            <li
              key={tab.id}
              role="presentation"
              className={`govuk-tabs__list-item${activeTab === tab.id ? " govuk-tabs__list-item--selected" : ""}`}
            >
              <a
                className="govuk-tabs__tab"
                href={`#panel-${tab.id}`}
                role="tab"
                id={`tab-${tab.id}`}
                aria-selected={activeTab === tab.id}
                aria-controls={`panel-${tab.id}`}
                onClick={(e) => { e.preventDefault(); setActiveTab(tab.id); }}
              >
                {tab.label}
              </a>
            </li>
          ))}
        </ul>

        <div
          className="govuk-tabs__panel"
          role="tabpanel"
          id={`panel-${activeTab}`}
          aria-labelledby={`tab-${activeTab}`}
        >
          {activeTab === "journey" && <JourneyTaskList assetId={id} />}
          {activeTab === "rules" && <RulesPanel assetId={id} />}
          {activeTab === "issues" && <IssuesPanel assetId={id} />}
          {activeTab === "actions" && <ActionsPanel assetId={id} />}
          {activeTab === "raci" && <RaciMatrix />}
        </div>
      </div>
    </>
  );
}
