import { render, screen, waitFor } from "@testing-library/react";
import JourneyTaskList from "./JourneyTaskList";

it("renders step name and checkboxes from API", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(
      JSON.stringify([
        {
          step: 1,
          name: "Catalogue the asset",
          done: false,
          source: "substeps",
          substeps: [
            { key: "1a", name: "Define metadata", done: false },
            { key: "1b", name: "Confirm owner", done: true },
          ],
        },
      ]),
      { status: 200 },
    ),
  );

  render(<JourneyTaskList assetId="asset-1" />);

  await waitFor(() => expect(screen.getByText(/Catalogue the asset/)).toBeInTheDocument());
  expect(screen.getByLabelText(/1\. Catalogue the asset/)).toBeInTheDocument();
  expect(screen.getByLabelText(/1a\. Define metadata/)).toBeInTheDocument();
  expect(screen.getByLabelText(/1b\. Confirm owner/)).toBeInTheDocument();
  // parent checkbox is disabled (completed via sub-steps)
  expect(screen.getByLabelText(/1\. Catalogue the asset/)).toBeDisabled();
});
