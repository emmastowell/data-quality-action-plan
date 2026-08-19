import { render, screen, waitFor } from "@testing-library/react";
import Dashboard from "./Dashboard";

it("renders the overall score from the API", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({
    asset_count: 1, active_asset_count: 1, overall_score: 95,
    critical_asset_count: 1, critical_active_count: 1,
    monitored_asset_count: 0, monitored_active_count: 0,
    score_by_dimension: { completeness: 95, accuracy: null, validity: null, timeliness: null, uniqueness: null, consistency: null },
    open_issue_count: 0, actions_in_progress: 0, assets_at_risk: [],
  }), { status: 200 }));
  render(<Dashboard />);
  // "95%" appears in both the summary (overall score) and the dimension table (completeness)
  await waitFor(() => expect(screen.getAllByText("95%").length).toBeGreaterThan(0));
});

it("shows split counts for critical and monitored", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({
    asset_count: 3, active_asset_count: 2,
    critical_asset_count: 1, critical_active_count: 1,
    monitored_asset_count: 2, monitored_active_count: 1,
    overall_score: 90,
    score_by_dimension: { completeness: 90, accuracy: null, validity: null, timeliness: null, uniqueness: null, consistency: null },
    open_issue_count: 0, actions_in_progress: 0, assets_at_risk: [],
  }), { status: 200 }));
  const { default: Dashboard } = await import("./Dashboard");
  render(<Dashboard />);
  await waitFor(() => expect(screen.getByText(/Critical assets/i)).toBeInTheDocument());
  expect(screen.getByText(/Monitored assets/i)).toBeInTheDocument();
});
