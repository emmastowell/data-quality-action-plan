import { render, screen, waitFor } from "@testing-library/react";
import UcTablesSection from "./UcTablesSection";

const LINKED_TABLE = {
  id: "t1",
  asset_id: "a1",
  catalog_name: "main",
  schema_name: "public",
  table_name: "customers",
  full_name: "main.public.customers",
  created_at: "2024-01-15T10:00:00Z",
  created_by: "alice@example.com",
};

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => [LINKED_TABLE],
    }),
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
});

it("renders a linked table's full_name", async () => {
  render(<UcTablesSection assetId="a1" />);
  await waitFor(() =>
    expect(screen.getByText("main.public.customers")).toBeInTheDocument(),
  );
});

it("silently ignores 'already exists' errors when linking a table (duplicate link)", async () => {
  // The api client throws the backend message, not the HTTP status, so the
  // 409 swallow must match "already exists" — not "409".
  const mockFetch = vi.fn().mockImplementation((url: string, opts?: RequestInit) => {
    if (opts?.method === "POST") {
      // Simulate the error the api client throws for a 409 response
      return Promise.resolve({
        ok: false,
        status: 409,
        json: async () => ({ error: { code: "conflict", message: "resource already exists" } }),
      });
    }
    // GET /api/uc/catalogs, /api/uc/schemas, /api/uc/tables
    if (url.includes("/uc/catalogs")) return Promise.resolve({ ok: true, status: 200, json: async () => ({ catalogs: ["main"] }) });
    if (url.includes("/uc/schemas")) return Promise.resolve({ ok: true, status: 200, json: async () => ({ schemas: ["public"] }) });
    if (url.includes("/uc/tables")) return Promise.resolve({ ok: true, status: 200, json: async () => ({ tables: [{ name: "customers", full_name: "main.public.customers", table_type: "MANAGED" }] }) });
    // GET linked tables
    return Promise.resolve({ ok: true, status: 200, json: async () => [LINKED_TABLE] });
  });
  vi.stubGlobal("fetch", mockFetch);

  render(<UcTablesSection assetId="a1" />);
  await waitFor(() => expect(screen.getByText("main.public.customers")).toBeInTheDocument());

  // The component should not show an error banner when "already exists" is returned
  expect(screen.queryByRole("alert")).toBeNull();
});
