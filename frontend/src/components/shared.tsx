export function priorityClass(p: string): string {
  return p === "high" ? "govuk-tag--red" : p === "medium" ? "govuk-tag--yellow" : "govuk-tag--grey";
}

export function SummaryList({ rows }: { rows: { key: string; value: string }[] }) {
  const filled = rows.filter(r => r.value);
  if (!filled.length) return null;
  return (
    <dl className="govuk-summary-list govuk-summary-list--no-border govuk-!-margin-top-2">
      {filled.map(r => (
        <div className="govuk-summary-list__row" key={r.key}>
          <dt className="govuk-summary-list__key">{r.key}</dt>
          <dd className="govuk-summary-list__value">{r.value}</dd>
        </div>
      ))}
    </dl>
  );
}
