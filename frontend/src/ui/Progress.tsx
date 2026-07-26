import { StyleSheet, Text, View } from "react-native";

import { colors, radius, space, type } from "@/theme";

type Props = { index: number; total: number };

export function Progress({ index, total }: Props) {
  const ratio = (index + 1) / total;
  return (
    <View style={styles.wrap}>
      <Text style={styles.meta}>
        Étape {index + 1} / {total}
      </Text>
      <View style={styles.track}>
        <View style={[styles.fill, { width: `${ratio * 100}%` }]} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { gap: space.xs },
  meta: { fontSize: type.small, color: colors.muted, fontWeight: "600" },
  track: {
    height: 6,
    borderRadius: radius.sm,
    backgroundColor: colors.brandSoft,
    overflow: "hidden",
  },
  fill: { height: "100%", backgroundColor: colors.brand },
});
