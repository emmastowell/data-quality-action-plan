import { render } from "@testing-library/react";
import ScoreTrend from "./ScoreTrend";
it("renders a polyline for >=2 points", () => {
  const { container } = render(<ScoreTrend data={[
    { id:"1", rule_id:"r", score:90, measured_at:"2026-01-01", method:"seeded" as any, source:"seeded" },
    { id:"2", rule_id:"r", score:95, measured_at:"2026-02-01", method:"seeded" as any, source:"seeded" },
  ]} />);
  expect(container.querySelector("polyline")).toBeTruthy();
});
