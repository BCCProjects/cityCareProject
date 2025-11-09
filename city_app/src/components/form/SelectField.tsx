import { Picker } from "@react-native-picker/picker";
import { StyleSheet, Text, View } from "react-native";

type SelectItem<T> = {
  label: string;
  value: T | "";
};

type SelectFieldProps<T> = {
  label: string;
  items: SelectItem<T>[];
  selectedValue: T | "" | undefined;
  onValueChange: (value: T | "") => void;
  error?: string;
  placeholder?: string;
};

export const SelectField = <T,>({
  label,
  items,
  selectedValue,
  onValueChange,
  error,
  placeholder,
}: SelectFieldProps<T>) => (
  <View style={styles.container}>
    <Text style={styles.label}>{label}</Text>
    <View style={[styles.pickerContainer, error ? styles.pickerError : null]}>
      <Picker
        selectedValue={selectedValue ?? ""}
        onValueChange={(value) => onValueChange(value as T | "")}
        style={styles.picker}
        dropdownIconColor="#1f2937"
      >
        <Picker.Item label={placeholder ?? "Selecione"} value="" />
        {items.map((item) => (
          <Picker.Item key={String(item.value)} label={item.label} value={item.value} />
        ))}
      </Picker>
    </View>
    {error ? <Text style={styles.error}>{error}</Text> : null}
  </View>
);

const styles = StyleSheet.create({
  container: {
    marginBottom: 14,
  },
  label: {
    fontWeight: "600",
    marginBottom: 6,
    color: "#1e293b",
  },
  pickerContainer: {
    borderWidth: 1,
    borderColor: "#cbd5f5",
    borderRadius: 12,
    overflow: "hidden",
    backgroundColor: "#ffffff",
  },
  picker: {
    color: "#0f172a",
  },
  pickerError: {
    borderColor: "#dc2626",
  },
  error: {
    marginTop: 4,
    color: "#dc2626",
    fontSize: 13,
  },
});
