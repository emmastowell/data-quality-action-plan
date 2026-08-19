import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import RulesPanel from "./RulesPanel";

const RULE_WITH_SQL = {
  id: "r1",
  asset_id: "a1",
  name: "IMO completeness",
  dimension: "completeness",
  unit: "%",
  measurement_sql: "SELECT 100.0*count_if(imo IS NOT NULL)/count(*) FROM main.public.ships",
};

const RULE_NO_SQL = {
  id: "r2",
  asset_id: "a1",
  name: "No SQL rule",
  dimension: "accuracy",
  unit: "%",
};

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation((url: string) => {
      if (url.includes("/measurements")) {
        return Promise.resolve({ ok: true, status: 200, json: async () => [] });
      }
      return Promise.resolve({ ok: true, status: 200, json: async () => [RULE_WITH_SQL, RULE_NO_SQL] });
    }),
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
});

it("shows a Run now button for a rule that has measurement_sql", async () => {
  render(<RulesPanel assetId="a1" />);
  await waitFor(() => expect(screen.getByText("IMO completeness")).toBeInTheDocument());
  expect(screen.getByRole("button", { name: "Run now" })).toBeInTheDocument();
});

it("does not show a Run now button for a rule without measurement_sql", async () => {
  render(<RulesPanel assetId="a1" />);
  await waitFor(() => expect(screen.getByText("No SQL rule")).toBeInTheDocument());
  // Only one "Run now" button: for the SQL rule
  expect(screen.getAllByRole("button", { name: "Run now" })).toHaveLength(1);
});

it("shows a SQL tag for a rule that has measurement_sql", async () => {
  render(<RulesPanel assetId="a1" />);
  await waitFor(() => expect(screen.getByText("SQL")).toBeInTheDocument());
});

it("shows Add SQL link for a rule without measurement_sql", async () => {
  render(<RulesPanel assetId="a1" />);
  await waitFor(() => expect(screen.getByText("No SQL rule")).toBeInTheDocument());
  expect(screen.getByText("Add SQL")).toBeInTheDocument();
});

it("PATCHes measurement_sql as empty string (not null) when clearing SQL", async () => {
  // Clearing SQL must send "" so the backend can persist it and disable Run now.
  // Sending null would be stripped by exclude_none and leave the old SQL in place.
  const mockFetch = vi.fn().mockImplementation((url: string, opts?: RequestInit) => {
    if (opts?.method === "PATCH") {
      const body = JSON.parse(opts.body as string);
      // Assert "" is sent, not null
      expect(body.measurement_sql).toBe("");
      return Promise.resolve({ ok: true, status: 200, json: async () => ({ ...RULE_WITH_SQL, measurement_sql: "" }) });
    }
    if (url.includes("/measurements")) {
      return Promise.resolve({ ok: true, status: 200, json: async () => [] });
    }
    return Promise.resolve({ ok: true, status: 200, json: async () => [RULE_WITH_SQL] });
  });
  vi.stubGlobal("fetch", mockFetch);

  render(<RulesPanel assetId="a1" />);
  await waitFor(() => expect(screen.getByText("IMO completeness")).toBeInTheDocument());

  // Open SQL editor
  fireEvent.click(screen.getByText("Edit SQL"));
  // Clear the SQL content — select the edit textarea by its label name
  // (the add-rule form also has a textarea but its label is "Measurement SQL (optional)")
  const textarea = screen.getByRole("textbox", { name: "Measurement SQL" });
  fireEvent.change(textarea, { target: { value: "" } });
  // Save
  fireEvent.click(screen.getByRole("button", { name: "Save SQL" }));

  await waitFor(() =>
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/rules/r1",
      expect.objectContaining({ method: "PATCH" }),
    ),
  );
});

it("POSTs to /api/rules/{id}/measure/run when Run now is clicked", async () => {
  const MEASUREMENT = {
    id: "m1", rule_id: "r1", score: 95.5,
    measured_at: "2026-08-11T12:00:00Z",
    method: "automated", source: "warehouse",
  };
  const mockFetch = vi.fn().mockImplementation((url: string, opts?: RequestInit) => {
    if (opts?.method === "POST") {
      return Promise.resolve({ ok: true, status: 200, json: async () => MEASUREMENT });
    }
    if (url.includes("/measurements")) {
      return Promise.resolve({ ok: true, status: 200, json: async () => [] });
    }
    return Promise.resolve({ ok: true, status: 200, json: async () => [RULE_WITH_SQL] });
  });
  vi.stubGlobal("fetch", mockFetch);

  render(<RulesPanel assetId="a1" />);
  await waitFor(() => expect(screen.getByText("IMO completeness")).toBeInTheDocument());

  fireEvent.click(screen.getByRole("button", { name: "Run now" }));

  await waitFor(() =>
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/rules/r1/measure/run",
      expect.objectContaining({ method: "POST" }),
    ),
  );
});
