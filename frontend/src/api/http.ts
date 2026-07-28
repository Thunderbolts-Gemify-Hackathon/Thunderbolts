import { API_URL } from "./config";
import {
  getAuthBundle,
  notifyAuthBundleChange,
  type AuthBundle,
} from "@/lib/authTokens";

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

type Options = {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  token?: string | null;
  /** Access JWT optionnel (sinon authTokens.accessToken). */
  accessToken?: string | null;
  /** Ne pas tenter de refresh sur 401. */
  skipRefresh?: boolean;
};

let refreshInFlight: Promise<boolean> | null = null;

async function tryRefresh(): Promise<boolean> {
  if (refreshInFlight) return refreshInFlight;
  refreshInFlight = (async () => {
    const { refreshToken, apiToken } = getAuthBundle();
    if (!refreshToken) return false;
    try {
      const res = await fetch(`${API_URL}/utilisateurs/refresh`, {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      if (!res.ok) return false;
      const data = (await res.json()) as {
        access_token: string;
        refresh_token: string;
        api_token?: string;
      };
      const next: AuthBundle = {
        apiToken: data.api_token ?? apiToken,
        accessToken: data.access_token,
        refreshToken: data.refresh_token,
      };
      notifyAuthBundleChange(next);
      return true;
    } catch {
      return false;
    } finally {
      refreshInFlight = null;
    }
  })();
  return refreshInFlight;
}

export async function api<T>(path: string, options: Options = {}): Promise<T> {
  const auth = getAuthBundle();
  const headers: Record<string, string> = {
    Accept: "application/json",
  };
  if (options.body !== undefined) {
    headers["Content-Type"] = "application/json";
  }

  const apiToken = options.token ?? auth.apiToken;
  const accessToken = options.accessToken ?? auth.accessToken;
  if (accessToken) {
    headers.Authorization = `Bearer ${accessToken}`;
  }
  if (apiToken) {
    headers["X-API-Token"] = apiToken;
  }

  const url = `${API_URL}${path}`;
  let res: Response;
  try {
    res = await fetch(url, {
      method: options.method ?? "GET",
      headers,
      body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    });
  } catch {
    throw new ApiError(
      0,
      `Reseau: impossible d'atteindre ${url}. Verifie Wi-Fi, IP Mac, et uvicorn --host 0.0.0.0`
    );
  }

  if (res.status === 401 && !options.skipRefresh && auth.refreshToken) {
    const ok = await tryRefresh();
    if (ok) {
      return api(path, { ...options, skipRefresh: true });
    }
  }

  if (!res.ok) {
    let detail = `Erreur ${res.status}`;
    try {
      const data = await res.json();
      if (typeof data?.detail === "string") detail = data.detail;
      else if (Array.isArray(data?.detail)) {
        detail = data.detail
          .map((d: { msg?: string }) => d.msg ?? JSON.stringify(d))
          .join(", ");
      }
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export async function pingApi(): Promise<string> {
  const data = await api<{ status: string; service: string }>("/health");
  return `${data.service}: ${data.status}`;
}
