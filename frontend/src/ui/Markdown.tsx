import { StyleSheet } from "react-native";
import Markdown from "react-native-markdown-display";

import { colors, radius, space, type } from "@/theme";

const markdownStyles = StyleSheet.create({
  body: { color: colors.ink, fontSize: type.body, lineHeight: 22 },
  paragraph: { marginTop: 0, marginBottom: 6 },
  heading1: {
    color: colors.ink,
    fontSize: type.title,
    fontWeight: "700",
    marginTop: 4,
    marginBottom: 6,
  },
  heading2: {
    color: colors.ink,
    fontSize: type.body + 4,
    fontWeight: "700",
    marginTop: 4,
    marginBottom: 6,
  },
  heading3: {
    color: colors.ink,
    fontSize: type.body + 2,
    fontWeight: "700",
    marginTop: 4,
    marginBottom: 4,
  },
  strong: { fontWeight: "700" },
  em: { fontStyle: "italic" },
  bullet_list: { marginVertical: 4 },
  ordered_list: { marginVertical: 4 },
  list_item: { marginVertical: 2, flexDirection: "row" },
  bullet_list_icon: { color: colors.ink, marginRight: 6 },
  ordered_list_icon: { color: colors.ink, marginRight: 6 },
  code_inline: {
    backgroundColor: colors.bg,
    color: colors.accent,
    borderRadius: 4,
    paddingHorizontal: 4,
    fontFamily: "monospace",
  },
  fence: {
    backgroundColor: colors.bg,
    borderColor: colors.line,
    borderRadius: radius.sm,
    padding: space.sm,
  },
  code_block: {
    backgroundColor: colors.bg,
    borderColor: colors.line,
    borderRadius: radius.sm,
    padding: space.sm,
  },
  link: { color: colors.brand, textDecorationLine: "underline" },
  hr: { backgroundColor: colors.line, height: 1, marginVertical: space.sm },
  blockquote: {
    backgroundColor: colors.bg,
    borderLeftColor: colors.brand,
    borderLeftWidth: 3,
    paddingHorizontal: space.sm,
    marginVertical: 4,
  },
  table: { borderColor: colors.line, borderWidth: 1, borderRadius: radius.sm },
  th: { padding: space.xs, backgroundColor: colors.bg },
  td: { padding: space.xs, borderColor: colors.line, borderWidth: 1 },
});

export function AiText({ content }: { content: string }) {
  return <Markdown style={markdownStyles}>{content}</Markdown>;
}
