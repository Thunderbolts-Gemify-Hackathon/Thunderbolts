import { Feather } from "@expo/vector-icons";
import DateTimePicker, { DateTimePickerAndroid } from "@react-native-community/datetimepicker";
import { useState } from "react";
import { Modal, Platform, Pressable, StyleSheet, Text, View } from "react-native";

import { Button } from "@/ui/Button";
import { colors, radius, space, type } from "@/theme";

type Props = {
  value: string; // "AAAA-MM-JJ" ou ""
  onChange: (v: string) => void;
  placeholder?: string;
  error?: string;
  onBlur?: () => void;
};

const AGE_PAR_DEFAUT = 20;

function defaultDate(): Date {
  const d = new Date();
  d.setFullYear(d.getFullYear() - AGE_PAR_DEFAUT);
  return d;
}

function parseIso(value: string): Date | null {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return null;
  const d = new Date(`${value}T00:00:00`);
  return Number.isNaN(d.getTime()) ? null : d;
}

function toIso(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function formatFr(value: string): string {
  const d = parseIso(value);
  if (!d) return "";
  return `${String(d.getDate()).padStart(2, "0")}/${String(d.getMonth() + 1).padStart(2, "0")}/${d.getFullYear()}`;
}

export function DateField({ value, onChange, placeholder, error, onBlur }: Props) {
  const [iosPickerOpen, setIosPickerOpen] = useState(false);
  const [draft, setDraft] = useState<Date>(parseIso(value) ?? defaultDate());
  const showError = !!error;

  const openPicker = () => {
    const initial = parseIso(value) ?? defaultDate();
    if (Platform.OS === "android") {
      DateTimePickerAndroid.open({
        value: initial,
        mode: "date",
        maximumDate: new Date(),
        onChange: (_, selected) => {
          onBlur?.();
          if (selected) onChange(toIso(selected));
        },
      });
      return;
    }
    setDraft(initial);
    setIosPickerOpen(true);
  };

  return (
    <View>
      <Pressable
        style={[styles.wrap, showError && styles.wrapError]}
        onPress={openPicker}
        accessibilityRole="button"
      >
        <Feather name="calendar" size={18} color={showError ? colors.danger : colors.muted} />
        <Text style={[styles.text, !value && styles.placeholder]}>
          {value ? formatFr(value) : placeholder}
        </Text>
      </Pressable>
      {showError ? <Text style={styles.errorText}>{error}</Text> : null}

      {Platform.OS === "ios" ? (
        <Modal
          visible={iosPickerOpen}
          transparent
          animationType="fade"
          onRequestClose={() => setIosPickerOpen(false)}
        >
          <View style={styles.overlay}>
            <View style={styles.card}>
              <Text style={styles.cardTitle}>Date de naissance</Text>
              <DateTimePicker
                value={draft}
                mode="date"
                display="inline"
                maximumDate={new Date()}
                onChange={(_, selected) => {
                  if (selected) setDraft(selected);
                }}
              />
              <Button
                label="Valider"
                rounded
                onPress={() => {
                  onChange(toIso(draft));
                  onBlur?.();
                  setIosPickerOpen(false);
                }}
              />
            </View>
          </View>
        </Modal>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    flexDirection: "row",
    alignItems: "center",
    minHeight: 56,
    borderWidth: 1.5,
    borderColor: colors.line,
    backgroundColor: colors.surface,
    borderRadius: 999,
    paddingHorizontal: space.lg,
    gap: space.sm,
  },
  wrapError: { borderColor: colors.danger },
  text: { flex: 1, fontSize: type.body, color: colors.ink, paddingVertical: space.sm },
  placeholder: { color: colors.muted },
  errorText: {
    color: colors.danger,
    fontSize: type.small,
    fontWeight: "600",
    marginTop: 4,
    marginLeft: space.lg,
  },
  overlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.4)",
    alignItems: "center",
    justifyContent: "center",
    padding: space.lg,
  },
  card: {
    width: "100%",
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    padding: space.lg,
    gap: space.md,
  },
  cardTitle: { fontSize: type.label, fontWeight: "700", color: colors.ink },
});
