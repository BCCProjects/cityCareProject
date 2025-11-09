import { StyleSheet, Text, View } from "react-native";
import { TouchableOpacity } from "react-native-gesture-handler";

type ChipItem = {
  id: number;
  label: string;
};

type ChipSelectorProps = {
  label: string;
  items: ChipItem[];
  selectedIds: number[];
  onToggle: (id: number) => void;
  helperText?: string;
};

export const ChipSelector = ({ label, items, selectedIds, onToggle, helperText }: ChipSelectorProps) => (
  <View style={styles.container}>
    <Text style={styles.label}>{label}</Text>
    <View style={styles.chipRow}>
      {items.map((item) => {
        const active = selectedIds.includes(item.id);
        return (
          <TouchableOpacity
            key={item.id}
            onPress={() => onToggle(item.id)}
            style={[styles.chip, active ? styles.chipActive : styles.chipInactive]}
          >
            <Text style={[styles.chipText, active ? styles.chipTextActive : styles.chipTextInactive]}>
              {item.label}
            </Text>
          </TouchableOpacity>
        );
      })}
    </View>
    {helperText ? <Text style={styles.helper}>{helperText}</Text> : null}
  </View>
);

const styles = StyleSheet.create({
  container: {
    marginBottom: 16,
  },
  label: {
    fontWeight: "600",
    marginBottom: 8,
    color: "#1e293b",
  },
  chipRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  chip: {
    borderRadius: 999,
    paddingVertical: 8,
    paddingHorizontal: 14,
  },
  chipInactive: {
    backgroundColor: "#e2e8f0",
  },
  chipActive: {
    backgroundColor: "#2563eb",
  },
  chipText: {
    fontSize: 14,
  },
  chipTextInactive: {
    color: "#1f2937",
  },
  chipTextActive: {
    color: "#ffffff",
  },
  helper: {
    marginTop: 6,
    fontSize: 12,
    color: "#64748b",
  },
});
