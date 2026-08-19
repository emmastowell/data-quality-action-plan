const COLOUR: Record<string, string> = { draft: "govuk-tag--grey", active: "govuk-tag--blue", archived: "govuk-tag--yellow" };
export default function StatusTag({ status }: { status: string }) {
  return <strong className={`govuk-tag ${COLOUR[status] ?? ""}`}>{status.replace("_", " ")}</strong>;
}
