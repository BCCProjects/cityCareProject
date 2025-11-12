import { forwardRef } from "react";
import { StyleSheet, Text, TextInput, TextInputProps, View } from "react-native";

type InputFieldProps = TextInputProps & {
  label: string;
  error?: string;
};

export const InputField = forwardRef<TextInput, InputFieldProps>(({ label, error, style, ...rest }, ref) => (
  <View style={styles.container}>
    <Text style={styles.label}>{label}</Text>
    <TextInput
      ref={ref}
      style={[styles.input, style, error ? styles.inputError : null]}
      placeholderTextColor="#94a3b8"
      {...rest}
    />
    {error ? <Text style={styles.error}>{error}</Text> : null}
  </View>
));

const styles = StyleSheet.create({
  container: {
    marginBottom: 14,
  },
  label: {
    fontWeight: "600",
    marginBottom: 6,
    color: "#1e293b",
  },
  input: {
    borderWidth: 1,
    borderColor: "#cbd5f5",
    borderRadius: 12,
    paddingVertical: 12,
    paddingHorizontal: 14,
    fontSize: 16,
    color: "#0f172a",
    backgroundColor: "#ffffff",
  },
  inputError: {
    borderColor: "#dc2626",
  },
  error: {
    marginTop: 4,
    color: "#dc2626",
    fontSize: 13,
  },
});

InputField.displayName = "InputField";
