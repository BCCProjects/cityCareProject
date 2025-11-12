import { StyleSheet, Text, View } from "react-native";

type ErrorMessageProps = {
  message?: string | null;
};

export const ErrorMessage = ({ message }: ErrorMessageProps) => {
  if (!message) {
    return null;
  }
  return (
    <View style={styles.container}>
      <Text style={styles.text}>{message}</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: "#fee2e2",
    borderRadius: 12,
    paddingVertical: 12,
    paddingHorizontal: 16,
    marginBottom: 16,
  },
  text: {
    color: "#b91c1c",
    fontSize: 14,
  },
});
