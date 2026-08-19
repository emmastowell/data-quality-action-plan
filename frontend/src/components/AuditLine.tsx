function fmtDate(iso: string): string {
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

interface AuditLineProps {
  created_by?: string;
  created_at?: string;
  updated_by?: string | null;
  updated_at?: string | null;
}

export default function AuditLine({ created_by, created_at, updated_by, updated_at }: AuditLineProps) {
  const parts: string[] = [];
  if (created_by || created_at) {
    let s = "Logged";
    if (created_by) s += ` by ${created_by}`;
    if (created_at) s += ` on ${fmtDate(created_at)}`;
    parts.push(s);
  }
  if (updated_at && updated_at !== created_at) {
    const prefix = parts.length > 0 ? "updated" : "Last updated";
    let s = prefix;
    if (updated_by) s += ` by ${updated_by}`;
    s += ` on ${fmtDate(updated_at)}`;
    parts.push(s);
  }
  if (!parts.length) return null;
  return <p className="govuk-hint govuk-!-margin-top-1 govuk-!-margin-bottom-2">{parts.join(" · ")}</p>;
}
