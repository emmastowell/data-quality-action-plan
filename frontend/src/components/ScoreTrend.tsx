import type { Measurement } from "../api/types";
export default function ScoreTrend({ data }: { data: Measurement[] }) {
  if (data.length < 2) return <span className="govuk-body-s">Not enough data</span>;
  const scores = data.map(d => d.score);
  const min = Math.min(...scores), max = Math.max(...scores), span = max - min || 1;
  const pts = scores.map((s, i) =>
    `${(i / (scores.length - 1)) * 100},${30 - ((s - min) / span) * 28}`).join(" ");
  return (
    <svg width="120" height="30" viewBox="0 0 100 30" preserveAspectRatio="none" role="img"
         aria-label={`Trend, latest ${scores[scores.length - 1]}%`}>
      <polyline points={pts} fill="none" stroke="currentColor" strokeWidth="2" />
    </svg>
  );
}
