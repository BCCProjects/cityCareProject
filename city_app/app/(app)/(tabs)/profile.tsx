import { Alert, StyleSheet, Text, View } from "react-native";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Screen } from "@/components/ui/Screen";
import { useAuth } from "@/features/auth/auth-context";

export default function ProfileScreen() {
  const { user, signOut } = useAuth();
  const fallbackValue = "N/D";
  const fullName = `${user?.firstName ?? "} ${user?.lastName ?? "}`.trim() || fallbackValue;
  const phoneValue = user?.phone || fallbackValue;
  const cityValue =
    user?.cityName && user?.stateAbbreviation ? `${user.cityName} - ${user.stateAbbreviation}` : fallbackValue;

  const handleSignOut = async () => {
    try {
      await signOut();
    } catch (error) {
      console.error("Failed to sign out", error);
      Alert.alert("Sair", "NÃ£o foi possÃ­vel encerrar a sessÃ£o. Tente novamente.");
    }
  };

  return (
    <Screen>
      <Text style={styles.title}>Meu perfil</Text>
      <Text style={styles.subtitle}>Dados bÃ¡sicos utilizados nas solicitaÃ§Ãµes.</Text>
      <Card>
        <InfoRow label="Email" value={user?.email ?? fallbackValue} />
        <InfoRow label="Nome" value={fullName} />
        <InfoRow label="Telefone" value={phoneValue} />
        <InfoRow label="Cidade" value={cityValue} />
      </Card>
      <Button title="Sair" variant="secondary" onPress={handleSignOut} />
    </Screen>
  );
}

type InfoRowProps = {
  label: string;
  value: string;
};

const InfoRow = ({ label, value }: InfoRowProps) => (
  <View style={styles.infoRow}>
    <Text style={styles.infoLabel}>{label}</Text>
    <Text style={styles.infoValue}>{value}</Text>
  </View>
);

const styles = StyleSheet.create({
  title: {
    fontSize: 24,
    fontWeight: "700",
    color: "#1e293b",
  },
  subtitle: {
    marginTop: 6,
    marginBottom: 18,
    fontSize: 15,
    color: "#475569",
  },
  infoRow: {
    marginBottom: 12,
  },
  infoLabel: {
    fontSize: 13,
    color: "#64748b",
    marginBottom: 2,
  },
  infoValue: {
    fontSize: 16,
    color: "#1e293b",
    fontWeight: "600",
  },
});


