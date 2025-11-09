import { PropsWithChildren } from "react";
import { SafeAreaView, ScrollView, StyleProp, StyleSheet, View, ViewStyle } from "react-native";

type ScreenProps = PropsWithChildren<{
  scrollable?: boolean;
  contentPadding?: number;
  style?: StyleProp<ViewStyle>;
  contentStyle?: StyleProp<ViewStyle>;
}>;

export const Screen = ({
  children,
  scrollable = true,
  contentPadding = 20,
  style,
  contentStyle,
}: ScreenProps) => {
  if (scrollable) {
    return (
      <SafeAreaView style={[styles.safe, style]}>
        <ScrollView
          keyboardShouldPersistTaps="handled"
          contentContainerStyle={[styles.contentGrow, { padding: contentPadding }, contentStyle]}
        >
          {children}
        </ScrollView>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.safe, style]}>
      <View style={[styles.fill, { padding: contentPadding }, contentStyle]}>{children}</View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: "#f8fafc",
  },
  contentGrow: {
    flexGrow: 1,
    width: "100%",
  },
  fill: {
    flex: 1,
    width: "100%",
  },
});
