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
};

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
  const items = await readQueue();
  items.push({
    ...mutation,
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    createdAt: Date.now(),
  });
  await writeQueue(items);
  return items.length;
}

export async function peekQueue() {
  return readQueue();
}

export async function flushQueue(): Promise<{ ok: number; fail: number }> {
  const items = await readQueue();
  if (!items.length) return { ok: 0, fail: 0 };
  const remaining: QueuedMutation[] = [];
  let ok = 0;
  let fail = 0;
  for (const m of items) {
    try {
      await api(m.path, {
        method: m.method,
        body: m.body,
        token: m.token,
      });
      ok += 1;
    } catch {
      remaining.push(m);
      fail += 1;
    }
  }
  await writeQueue(remaining);
  return { ok, fail };
}
