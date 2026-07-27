import AsyncStorage from "@react-native-async-storage/async-storage";

import { api } from "@/api/http";

const KEY = "kalitao.offlineQueue.v1";

export type QueuedMutation = {
  id: string;
  method: "POST" | "PUT" | "PATCH" | "DELETE";
  path: string;
  body?: unknown;
  token?: string | null;
  createdAt: number;
  retries?: number;
};

export type ApiHandler = (m: QueuedMutation) => Promise<unknown>;

/** Pure: ajoute une mutation à une liste (sans AsyncStorage). */
export function appendMutation(
  items: QueuedMutation[],
  mutation: Omit<QueuedMutation, "id" | "createdAt">
): QueuedMutation[] {
  return [
    ...items,
    {
      ...mutation,
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      createdAt: Date.now(),
      retries: mutation.retries ?? 0,
    },
  ];
}

/** Pure: rejoue avec handlers ; échecs restent en file (retry++). */
export async function flushWithHandlers(
  items: QueuedMutation[],
  handlers: Record<string, ApiHandler> | ApiHandler,
  opts?: { maxRetries?: number }
): Promise<{ ok: number; fail: number; remaining: QueuedMutation[] }> {
  const maxRetries = opts?.maxRetries ?? 5;
  const remaining: QueuedMutation[] = [];
  let ok = 0;
  let fail = 0;
  for (const m of items) {
    const key = `${m.method} ${m.path}`;
    const handler =
      typeof handlers === "function"
        ? handlers
        : handlers[key] || handlers[m.path];
    try {
      if (handler) {
        await handler(m);
      } else {
        await api(m.path, {
          method: m.method,
          body: m.body,
          token: m.token,
        });
      }
      ok += 1;
    } catch {
      const retries = (m.retries ?? 0) + 1;
      if (retries <= maxRetries) {
        remaining.push({ ...m, retries });
      }
      fail += 1;
    }
  }
  return { ok, fail, remaining };
}

async function readQueue(): Promise<QueuedMutation[]> {
  const raw = await AsyncStorage.getItem(KEY);
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

async function writeQueue(items: QueuedMutation[]) {
  await AsyncStorage.setItem(KEY, JSON.stringify(items));
}

export async function enqueueMutation(
  mutation: Omit<QueuedMutation, "id" | "createdAt">
) {
  const items = appendMutation(await readQueue(), mutation);
  await writeQueue(items);
  return items.length;
}

export async function peekQueue() {
  return readQueue();
}

export async function clearQueue() {
  await writeQueue([]);
}

/**
 * Flush la file. `apiHandlers` optionnel : map path/method → handler
 * pour tests ou sync custom ; sinon appelle `api()`.
 */
export async function flushQueue(
  apiHandlers?: Record<string, ApiHandler> | ApiHandler
): Promise<{ ok: number; fail: number }> {
  const items = await readQueue();
  if (!items.length) return { ok: 0, fail: 0 };
  const result = await flushWithHandlers(
    items,
    apiHandlers ?? (async (m) =>
      api(m.path, { method: m.method, body: m.body, token: m.token })
    )
  );
  await writeQueue(result.remaining);
  return { ok: result.ok, fail: result.fail };
}
