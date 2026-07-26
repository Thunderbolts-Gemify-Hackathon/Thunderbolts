import { Feather } from "@expo/vector-icons";
import * as Location from "expo-location";
import { useState } from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";

import { colors, radius, space, type } from "@/theme";

type Props = {
  latitude: string;
  longitude: string;
  onLocated: (latitude: string, longitude: string) => void;
};

export function LocationField({ latitude, longitude, onLocated }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const located = Boolean(latitude && longitude);

  const useMyLocation = async () => {
    setLoading(true);
    setError(null);
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== "granted") {
        setError("Permission refusée. Choisis ton quartier ci-dessous à la place.");
        return;
      }
      const pos = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.Balanced,
      });
      onLocated(String(pos.coords.latitude), String(pos.coords.longitude));
    } catch {
      setError("Position indisponible. Choisis ton quartier ci-dessous à la place.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.wrap}>
      <Text style={styles.label}>Position exacte (optionnel)</Text>
      <Pressable
        onPress={() => void useMyLocation()}
        style={[styles.button, located && styles.buttonLocated]}
        disabled={loading}
      >
        {loading ? (
          <ActivityIndicator color={located ? "#F7F3EA" : colors.brand} size="small" />
        ) : (
          <Feather
            name={located ? "check-circle" : "map-pin"}
            size={18}
            color={located ? "#F7F3EA" : colors.brand}
          />
        )}
        <Text style={[styles.buttonText, located && styles.buttonTextLocated]}>
          {located ? "Position détectée" : "Utiliser ma position"}
        </Text>
      </Pressable>
      {located ? (
        <Pressable onPress={() => onLocated("", "")} hitSlop={8}>
          <Text style={styles.clear}>Revenir au choix du quartier</Text>
        </Pressable>
      ) : (
        <Text style={styles.hint}>
          Plus précis que le quartier. Sinon, choisis ton quartier ci-dessous.
        </Text>
      )}
      {error ? <Text style={styles.error}>{error}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { gap: space.xs },
  label: {
    fontSize: type.label,
    color: colors.muted,
    fontWeight: "600",
    letterSpacing: 0.3,
    textTransform: "uppercase",
  },
  button: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: space.sm,
    minHeight: 50,
    borderWidth: 1,
    borderColor: colors.brand,
    backgroundColor: colors.surface,
    borderRadius: radius.sm,
    paddingHorizontal: space.md,
  },
  buttonLocated: { backgroundColor: colors.brand },
  buttonText: { color: colors.brand, fontWeight: "700", fontSize: type.body },
  buttonTextLocated: { color: "#F7F3EA" },
  hint: { fontSize: type.small, color: colors.muted },
  clear: { fontSize: type.small, color: colors.brand, fontWeight: "600", textDecorationLine: "underline" },
  error: {
    fontSize: type.small,
    color: colors.danger,
  },
});
