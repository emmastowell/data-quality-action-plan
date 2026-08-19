import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import AssetsList from "./AssetsList";

it("groups assets into critical and monitored sections", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify([
    { id: "1", name: "Ship Register", criticality: "high", status: "active", kind: "critical" },
    { id: "2", name: "Weather Feed", criticality: "low", status: "active", kind: "monitored" },
  ]), { status: 200 }));
  render(<MemoryRouter><AssetsList /></MemoryRouter>);
  await waitFor(() => expect(screen.getByText("Ship Register")).toBeInTheDocument());
  expect(screen.getByRole("heading", { name: /Critical data assets/i })).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: /Monitored data assets/i })).toBeInTheDocument();
});
