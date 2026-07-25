import { View } from "react-native";

import { ChoiceGroup } from "@/ui/ChoiceGroup";
import { Field } from "@/ui/Field";

import type { FieldDef, OnboardingData, StepId } from "./types";

type Props = {
  stepId: StepId;
  fields: FieldDef[];
  values: OnboardingData[StepId];
  onChange: (key: string, value: string | string[]) => void;
};

function keyboardFor(kind: FieldDef["kind"]) {
  if (kind === "email") return "email-address" as const;
  if (kind === "number") return "numeric" as const;
  return "default" as const;
}

export function StepForm({ stepId, fields, values, onChange }: Props) {
  return (
    <View style={{ gap: 16 }}>
      {fields.map((field) => {
        const current = (values as Record<string, unknown>)[field.key];

        if (field.kind === "select" || field.kind === "chips") {
          return (
            <ChoiceGroup
              key={`${stepId}-${field.key}`}
              label={field.label}
              options={field.options ?? []}
              multi={field.kind === "chips" || field.multi}
              value={(current as string | string[]) ?? (field.multi ? [] : "")}
              onChange={(v) => onChange(field.key, v)}
            />
          );
        }

        return (
          <Field
            key={`${stepId}-${field.key}`}
            label={field.label}
            value={String(current ?? "")}
            placeholder={field.placeholder}
            keyboard={keyboardFor(field.kind)}
            onChange={(v) => onChange(field.key, v)}
          />
        );
      })}
    </View>
  );
}
