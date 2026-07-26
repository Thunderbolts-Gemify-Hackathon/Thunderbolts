import { ReactNode } from "react";
import { StyleSheet, View, ViewStyle } from "react-native";
import Svg, { Path } from "react-native-svg";

const VIEWBOX_WIDTH = 393;
const VIEWBOX_HEIGHT = 513;
const CURVE_PATH =
  "M251.641 496.722C317.474 538.281 373.217 490.079 393 465.085V0H-1V418.528C1.9924 413.79 21.6268 443.55 74.6921 441.197C141.024 438.257 169.35 444.774 251.641 496.722Z";

type Props = {
  color: string;
  style?: ViewStyle;
  children?: ReactNode;
};

export function CurveBackdrop({ color, style, children }: Props) {
  return (
    <View style={[styles.wrap, style]}>
      <Svg
        style={StyleSheet.absoluteFillObject}
        viewBox={`0 0 ${VIEWBOX_WIDTH} ${VIEWBOX_HEIGHT}`}
        preserveAspectRatio="none"
      >
        <Path d={CURVE_PATH} fill={color} />
      </Svg>
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    width: "100%",
    aspectRatio: VIEWBOX_WIDTH / VIEWBOX_HEIGHT,
    alignItems: "center",
    justifyContent: "center",
  },
});
