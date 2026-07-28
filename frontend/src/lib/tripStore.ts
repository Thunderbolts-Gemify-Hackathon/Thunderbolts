import AsyncStorage from "@react-native-async-storage/async-storage";

import type { OneTripResult } from "@/api/marketPanier";

const KEY = "kalitao.activeTrip.v1";
const CHECKS_KEY = "kalitao.sortieChecks.v1";

export async function saveActiveTrip(trip: OneTripResult): Promise<void> {
  await AsyncStorage.setItem(KEY, JSON.stringify(trip));
}

export async function loadActiveTrip(): Promise<OneTripResult | null> {
  const raw = await AsyncStorage.getItem(KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as OneTripResult;
  } catch {
    return null;
  }
}

export async function clearActiveTrip(): Promise<void> {
  await AsyncStorage.multiRemove([KEY, CHECKS_KEY]);
}

/** Clés cochées pendant la sortie : `${pdvId}::${ingredientId}` */
export async function loadSortieChecks(): Promise<string[]> {
  const raw = await AsyncStorage.getItem(CHECKS_KEY);
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export async function saveSortieChecks(keys: string[]): Promise<void> {
  await AsyncStorage.setItem(CHECKS_KEY, JSON.stringify(keys));
}

export function checkKey(pdvId: string, ingredientId: string) {
  return `${pdvId}::${ingredientId}`;
}
