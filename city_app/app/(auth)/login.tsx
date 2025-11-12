import { Link } from "expo-router";
import { useState } from "react";
import { Alert, KeyboardAvoidingView, Platform, StyleSheet, Text, View } from "react-native";

import { ErrorMessage } from "@/components/form/ErrorMessage";
import { InputField } from "@/components/form/InputField";
import { Button } from "@/components/ui/Button";
import { Screen } from "@/components/ui/Screen";
import { useAuth } from "@/features/auth/auth-context";

export default function LoginScreen() {
  const { signIn } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!email || !password) {
      setErrorMessage("Informe email e senha.");
      return;
    }
    setErrorMessage(null);
    setLoading(true);
    try {
      await signIn({ email, password });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Falha ao entrar. Tente novamente.";
      setErrorMessage(message);
      Alert.alert("Login", message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Screen>
      <KeyboardAvoidingView
        behavior={Platform.select({ ios: "padding", android: undefined })}
        style={styles.container}
      >
        <View style={styles.header}>
          <Text style={styles.title}>CityCare</Text>
          <Text style={styles.subtitle}>Acompanhe e abra solicitações para a sua cidade.</Text>
        </View>
        <ErrorMessage message={errorMessage} />
        <InputField
          label="Email"
          keyboardType="email-address"
          autoCapitalize="none"
          autoComplete="email"
          value={email}
          onChangeText={setEmail}
          placeholder="seu@email.com"
        />
        <InputField
          label="Senha"
          autoCapitalize="none"
          secureTextEntry
          value={password}
          onChangeText={setPassword}
          placeholder="********"
        />
        <Button title="Entrar" onPress={handleSubmit} loading={loading} />
        <View style={styles.footer}>
          <Text style={styles.footerText}>É novo por aqui? </Text>
          <Link href="/(auth)/register" style={styles.link}>
            Criar conta
          </Link>
        </View>
      </KeyboardAvoidingView>
    </Screen>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: "center",
  },
  header: {
    marginBottom: 32,
  },
  title: {
    fontSize: 32,
    fontWeight: "700",
    color: "#1e293b",
  },
  subtitle: {
    marginTop: 8,
    fontSize: 16,
    color: "#475569",
  },
  footer: {
    flexDirection: "row",
    justifyContent: "center",
    marginTop: 16,
  },
  footerText: {
    color: "#475569",
  },
  link: {
    color: "#2563eb",
    fontWeight: "600",
  },
});
