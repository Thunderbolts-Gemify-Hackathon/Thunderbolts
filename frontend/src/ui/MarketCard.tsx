import { Feather } from "@expo/vector-icons";
import { Linking, Pressable, StyleSheet, Text, View } from "react-native";

import { formatAr, type MarketMatch } from "@/api/market";
import { formatTrajet } from "@/lib/travelEstimate";
import { speak } from "@/lib/speech";
import { colors, radius, space, type } from "@/theme";

const SECURITE_LABEL: Record<string, string> = {
  sur: "Trajet sûr",
  prudence: "Prudence conseillée",
  a_eviter: "À éviter",
  inconnu: "Sécurité inconnue",
};

const SECURITE_COLOR: Record<string, string> = {
  sur: colors.ok,
  prudence: colors.accent,
  a_eviter: colors.danger,
  inconnu: colors.muted,
};

type Props = {
  match: MarketMatch;
  recommended: boolean;
  width: number;
  onVoirTrajet: () => void;
};

export function MarketCard({ match, recommended, width, onVoirTrajet }: Props) {
  const { point_de_vente: pdv, itineraire, prix, deprioritise } = match;
  const securite = itineraire?.niveau_securite ?? "inconnu";

  const onOuvrirMaps = () => {
    const url = `https://www.google.com/maps/dir/?api=1&destination=${pdv.latitude},${pdv.longitude}`;
    void Linking.openURL(url);
  };

  const onEcouter = () => {
    const phrase = [
      `${pdv.nom}.`,
      `Prix indicatif ${Math.round(prix)} ariary.`,
      itineraire ? `${itineraire.distance} kilometres, ${SECURITE_LABEL[securite]}.` : "",
      deprioritise ? "Attention, trajet a eviter." : "",
    ]
      .filter(Boolean)
      .join(" ");
    speak(phrase);
  };

  return (
    <View style={[styles.card, { width }]}>
      <View style={styles.headerRow}>
        <View style={styles.headerText}>
          <Text style={styles.nom} numberOfLines={1}>
            {pdv.nom}
          </Text>
          <Text style={styles.type}>{pdv.type}</Text>
        </View>
        {recommended ? (
          <View style={styles.badge}>
            <Feather name="check" size={12} color="#F7F3EA" />
            <Text style={styles.badgeText}>Recommandé</Text>
          </View>
        ) : null}
      </View>

      <Text style={styles.prix}>{formatAr(prix)}</Text>

      {itineraire ? (
        <View style={styles.trajetRow}>
          <View style={[styles.dot, { backgroundColor: SECURITE_COLOR[securite] }]} />
          <Text style={styles.trajet}>
            {formatTrajet(itineraire.distance, itineraire.mode_deplacement)}
          </Text>
        </View>
      ) : null}

      {deprioritise ? (
        <Text style={styles.warn}>Déconseillé — trajet à éviter selon nos règles de sécurité.</Text>
      ) : null}

      <View style={styles.actions}>
        <Pressable onPress={onVoirTrajet} style={styles.primaryBtn}>
          <Feather name="map" size={16} color="#F7F3EA" />
          <Text style={styles.primaryLabel}>Voir le trajet</Text>
        </Pressable>
        <Pressable onPress={onOuvrirMaps} style={styles.secondaryBtn} hitSlop={8}>
          <Feather name="navigation" size={16} color={colors.brand} />
        </Pressable>
        <Pressable onPress={onEcouter} style={styles.secondaryBtn} hitSlop={8}>
          <Feather name="volume-2" size={16} color={colors.brand} />
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    padding: space.md,
    gap: 6,
    shadowColor: "#000",
    shadowOpacity: 0.12,
    shadowRadius: 14,
    shadowOffset: { width: 0, height: 6 },
    elevation: 8,
  },
  headerRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start" },
  headerText: { flex: 1, gap: 2 },
  nom: { fontSize: type.body, fontWeight: "700", color: colors.ink },
  type: { fontSize: type.small, color: colors.muted, textTransform: "capitalize" },
  badge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    backgroundColor: colors.brand,
    borderRadius: 999,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  badgeText: { color: "#F7F3EA", fontSize: 11, fontWeight: "700" },
  prix: { fontSize: 22, fontWeight: "800", color: colors.ink },
  trajetRow: { flexDirection: "row", alignItems: "center", gap: 6 },
  dot: { width: 8, height: 8, borderRadius: 4 },
  trajet: { fontSize: type.small, color: colors.muted, fontWeight: "600" },
  warn: { fontSize: type.small, color: colors.danger, fontWeight: "600" },
  actions: { flexDirection: "row", gap: space.sm, marginTop: space.xs },
  primaryBtn: {
    flex: 1,
    flexDirection: "row",
    gap: 6,
    minHeight: 44,
    borderRadius: 999,
    backgroundColor: colors.brand,
    alignItems: "center",
    justifyContent: "center",
  },
  primaryLabel: { color: "#F7F3EA", fontWeight: "700", fontSize: type.small },
  secondaryBtn: {
    width: 44,
    height: 44,
    borderRadius: 22,
    borderWidth: 1,
    borderColor: colors.line,
    backgroundColor: colors.surface,
    alignItems: "center",
    justifyContent: "center",
  },
});
