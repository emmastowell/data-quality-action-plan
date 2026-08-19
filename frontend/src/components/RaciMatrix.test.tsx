import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import RaciMatrix from "./RaciMatrix";

const MATRIX = {
  roles: [{ id: "r1", name: "Data steward / Business SME", sort_order: 0 }],
  activities: [{ step_label: "Step 1 — Identify critical data", key: "s1-0", activity_label: "Identify primary purpose" }],
  cells: { "s1-0": { r1: "R" } },
};

function mockFetch() {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify(MATRIX), { status: 200 }));
}

it("renders read-only by default — no editable inputs", async () => {
  mockFetch();
  render(<RaciMatrix />);
  await waitFor(() => expect(screen.getByText("Identify primary purpose")).toBeInTheDocument());
  expect(screen.getByText("Data steward / Business SME")).toBeInTheDocument();
  // cell value shown as text, not an input
  expect(screen.queryByDisplayValue("R")).toBeNull();
  // no add-role field until editing
  expect(screen.queryByLabelText("Add a role")).toBeNull();
  expect(screen.getByRole("button", { name: /Edit RACI matrix/i })).toBeInTheDocument();
});

it("reveals editable inputs after clicking Edit", async () => {
  mockFetch();
  render(<RaciMatrix />);
  await waitFor(() => expect(screen.getByText("Identify primary purpose")).toBeInTheDocument());
  fireEvent.click(screen.getByRole("button", { name: /Edit RACI matrix/i }));
  // cell is now an editable input, role name is editable, add-role field appears
  expect(screen.getByDisplayValue("R")).toBeInTheDocument();
  expect(screen.getByDisplayValue("Data steward / Business SME")).toBeInTheDocument();
  expect(screen.getByLabelText("Add a role")).toBeInTheDocument();
});
