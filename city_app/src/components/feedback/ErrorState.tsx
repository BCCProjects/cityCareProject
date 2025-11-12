import { StyleSheet, Text, View } from "react-native";

type ErrorStateProps = {
  message?: string;
  onRetry?: () => void;
};

export const ErrorState = ({ message, onRetry }: ErrorStateProps) => (
  <View style={styles.container}>
    <Text style={styles.title}>Algo deu errado</Text>
    {message ? <Text style={styles.message}>{message}</Text> : null}
    {onRetry ? (
      <Text style={styles.retry} onPress={onRetry}>
        Tentar novamente
      </Text>
    ) : null}
  </View>
);

const styles = StyleSheet.create({
  container: {
    paddingVertical: 32,
    alignItems: "center",
    justifyContent: "center",
  },
  title: {
    fontSize: 18,
    fontWeight: "600",
    color: "#1e293b",
    marginBottom: 6,
  },
  message: {
    fontSize: 14,
    color: "#64748b",
    textAlign: "center",
    marginBottom: 12,
  },
  retry: {
    color: "#2563eb",
    fontWeight: "500",
  },
});
