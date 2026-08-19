async function req<T>(method: string, path: string, body?: unknown): Promise<T> {
  const res = await fetch(path, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(detail?.error?.message || `${method} ${path} failed (${res.status})`);
  }
  return res.status === 204 ? (undefined as T) : res.json();
}
export const api = {
  get: <T,>(p: string) => req<T>("GET", p),
  post: <T,>(p: string, b: unknown) => req<T>("POST", p, b),
  patch: <T,>(p: string, b: unknown) => req<T>("PATCH", p, b),
  put: <T,>(p: string, b: unknown) => req<T>("PUT", p, b),
  del: (p: string) => req<void>("DELETE", p),
};
