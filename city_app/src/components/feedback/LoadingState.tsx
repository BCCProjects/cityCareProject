import { ActivityIndicator, StyleSheet, Text, View } from "react-native";

type LoadingStateProps = {
  message?: string;
};

export const LoadingState = ({ message }: LoadingStateProps) => (
  <View style={styles.container}>
    <ActivityIndicator size="large" color="#2563eb" />
    {message ? <Text style={styles.message}>{message}</Text> : null}
  </View>
);

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 24,
  },
  message: {
    marginTop: 12,
    color: "#1e293b",
    fontSize: 16,
    textAlign: "center",
  },
});
