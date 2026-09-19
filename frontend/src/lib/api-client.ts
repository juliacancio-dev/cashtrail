const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

let accessToken: string | null = null;

/** Access token só existe em memória (ADR-006) — nunca em localStorage/sessionStorage. */
export function setAccessToken(token: string | null): void {
  accessToken = token;
}

export async function refreshAccessToken(): Promise<boolean> {
  const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
    method: "POST",
    credentials: "include",
  });

  if (!response.ok) {
    setAccessToken(null);
    return false;
  }

  const data = (await response.json()) as { access_token: string };
  setAccessToken(data.access_token);
  return true;
}

async function request(path: string, options: RequestInit = {}, allowRetry = true): Promise<Response> {
  const headers = new Headers(options.headers);
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  if (options.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
    // Necessário para o cookie httpOnly de refresh trafegar (ADR-006).
    credentials: "include",
  });

  if (response.status === 401 && allowRetry && path !== "/auth/refresh") {
    const refreshed = await refreshAccessToken();
    if (refreshed) return request(path, options, false);
  }

  return response;
}

export const apiClient = {
  get: (path: string) => request(path),
  post: (path: string, body?: unknown) =>
    request(path, { method: "POST", body: body !== undefined ? JSON.stringify(body) : undefined }),
  patch: (path: string, body?: unknown) =>
    request(path, { method: "PATCH", body: body !== undefined ? JSON.stringify(body) : undefined }),
  delete: (path: string) => request(path, { method: "DELETE" }),
};
