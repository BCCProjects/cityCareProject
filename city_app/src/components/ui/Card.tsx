import { PropsWithChildren } from "react";
import { StyleSheet, View } from "react-native";

type CardProps = PropsWithChildren<{
  elevation?: number;
}>;

export const Card = ({ children, elevation = 3 }: CardProps) => (
  <View style={[styles.container, { shadowOpacity: elevation * 0.08 }]}>{children}</View>
);

const styles = StyleSheet.create({
  container: {
    backgroundColor: "#ffffff",
    borderRadius: 16,
    padding: 18,
    marginBottom: 16,
    shadowColor: "#0f172a",
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 10,
    elevation: 3,
  },
});
