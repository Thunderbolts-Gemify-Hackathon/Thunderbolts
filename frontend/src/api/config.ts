import { Platform } from "react-native";

/**
 * URL de l'API KaliTao.
 * - Web / simulateur iOS : localhost OK
 * - Téléphone physique : mets l'IP LAN du Mac, ex. http://192.168.10.65:8000
 *   via EXPO_PUBLIC_API_URL dans `.env` ou en lançant :
 *   EXPO_PUBLIC_API_URL=http://192.168.x.x:8000 npx expo start
 */
const FALLBACK =
  Platform.OS === "android" ? "http://10.0.2.2:8000" : "http://127.0.0.1:8000";

export const API_URL = (process.env.EXPO_PUBLIC_API_URL || FALLBACK).replace(/\/$/, "");
