import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { JourneyStep } from "../api/types";
import AuditLine from "./AuditLine";

const SOURCE_LABEL: Record<JourneyStep["source"], string> = {
  substeps: "from sub-steps",
  manual: "manual",
  auto: "auto",
};

export default function JourneyTaskList({ assetId }: { assetId: string }) {
  const [steps, setSteps] = useState<JourneyStep[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get<JourneyStep[]>(`/api/assets/${assetId}/journey`).then(setSteps);
  }, [assetId]);

  async function toggle(key: string, current: boolean) {
    try {
      const updated = await api.put<JourneyStep[]>(
        `/api/assets/${assetId}/journey/${key}`,
        { done: !current },
      );
      setSteps(updated);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update the step. Please try again.");
    }
  }

  return (
    <div className="govuk-form-group">
      {error && <p className="govuk-error-message">{error}</p>}
      {steps.map((s) => {
        const parentId = `journey-step-${s.step}`;
        const isAutoCompleted = s.source === "substeps";

        return (
          <div key={s.step} style={{ marginBottom: "1.5rem" }}>
            {/* Parent step row */}
            <div className="govuk-checkboxes__item">
              <input
                className="govuk-checkboxes__input"
                id={parentId}
                type="checkbox"
                checked={s.done}
                disabled={isAutoCompleted}
                onChange={() => { if (!isAutoCompleted) void toggle(String(s.step), s.done); }}
                aria-describedby={isAutoCompleted ? `${parentId}-hint` : undefined}
              />
              <label className="govuk-label govuk-checkboxes__label" htmlFor={parentId}>
                {s.step}. {s.name}{" "}
                <span className="govuk-hint" style={{ display: "inline", fontSize: "0.875rem", color: "#505a5f" }}>
                  ({SOURCE_LABEL[s.source]})
                </span>
              </label>
              {isAutoCompleted && (
                <div id={`${parentId}-hint`} className="govuk-hint govuk-checkboxes__hint">
                  Completed via sub-steps
                </div>
              )}
              {(s.updated_by || s.updated_at) && (
                <AuditLine updated_by={s.updated_by} updated_at={s.updated_at} />
              )}
            </div>

            {/* Sub-step rows — always editable */}
            {s.substeps.length > 0 && (
              <div
                className="govuk-checkboxes govuk-checkboxes--small"
                style={{ paddingLeft: "2.5rem", marginTop: "0.5rem" }}
              >
                {s.substeps.map((sub) => {
                  const subId = `journey-substep-${sub.key}`;
                  return (
                    <div className="govuk-checkboxes__item" key={sub.key}>
                      <input
                        className="govuk-checkboxes__input"
                        id={subId}
                        type="checkbox"
                        checked={sub.done}
                        onChange={() => toggle(sub.key, sub.done)}
                      />
                      <label className="govuk-label govuk-checkboxes__label" htmlFor={subId}>
                        {sub.key}. {sub.name}
                      </label>
                      {(sub.updated_by || sub.updated_at) && (
                        <AuditLine updated_by={sub.updated_by} updated_at={sub.updated_at} />
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
