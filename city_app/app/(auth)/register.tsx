import { Link, useRouter } from "expo-router";
import { useEffect, useMemo, useState } from "react";
import { Alert, KeyboardAvoidingView, Platform, StyleSheet, Text, View } from "react-native";

import { ErrorMessage } from "@/components/form/ErrorMessage";
import { InputField } from "@/components/form/InputField";
import { SelectField } from "@/components/form/SelectField";
import { Button } from "@/components/ui/Button";
import { Screen } from "@/components/ui/Screen";
import { useAuth } from "@/features/auth/auth-context";
import { useCities, useStates } from "@/features/reference-data/hooks";

export default function RegisterScreen() {
  const router = useRouter();
  const { register } = useAuth();
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [stateId, setStateId] = useState<number | "">("");
  const [cityId, setCityId] = useState<number | "">("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const { data: statesData, isLoading: statesLoading, error: statesError } = useStates();
  const {
    data: citiesData,
    isLoading: citiesLoading,
    refetch: refetchCities,
  } = useCities(typeof stateId === "number" ? stateId : undefined);

  useEffect(() => {
    if (stateId === "") {
      return;
    }
    refetchCities();
  }, [stateId, refetchCities]);

  const stateItems = useMemo(
    () =>
      (statesData ?? []).map((state) => ({
        label: `${state.name} (${state.abbreviation})`,
        value: state.id,
      })),
    [statesData],
  );

  const cityItems = useMemo(
    () =>
      (citiesData ?? []).map((city) => ({
        label: `${city.name} - ${city.state.abbreviation}`,
        value: city.id,
      })),
    [citiesData],
  );

  const handleSubmit = async () => {
    if (!firstName || !email || !phone || !password || !stateId || !cityId) {
      setErrorMessage("Preencha todos os campos obrigatórios.");
      return;
    }
    if (password.length < 8) {
      setErrorMessage("A senha deve possuir pelo menos 8 caracteres.");
      return;
    }
    if (password !== confirmPassword) {
      setErrorMessage("As senhas não conferem.");
      return;
    }
    setErrorMessage(null);
    setLoading(true);
    try {
      await register({
        first_name: firstName,
        last_name: lastName,
        email,
        phone,
        password,
        city_id: cityId as number,
      });
      Alert.alert("Bem-vindo(a)!", "Conta criada com sucesso.");
      router.replace("/(app)/(tabs)/reports");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Falha ao criar conta. Tente novamente.";
      setErrorMessage(message);
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
          <Text style={styles.title}>Criar conta</Text>
          <Text style={styles.subtitle}>Cadastre-se para registrar ocorrências em sua cidade.</Text>
        </View>
        <ErrorMessage
          message={
            errorMessage ??
            (statesError instanceof Error ? `Falha ao carregar estados: ${statesError.message}` : null)
          }
        />
        <InputField label="Nome" value={firstName} onChangeText={setFirstName} placeholder="Maria" />
        <InputField label="Sobrenome (opcional)" value={lastName} onChangeText={setLastName} placeholder="Silva" />
        <InputField
          label="Email"
          keyboardType="email-address"
          autoCapitalize="none"
          value={email}
          onChangeText={setEmail}
          placeholder="seu@email.com"
        />
        <InputField
          label="Telefone"
          keyboardType="phone-pad"
          value={phone}
          onChangeText={setPhone}
          placeholder="(11) 99999-9999"
        />
        <SelectField
          label="Estado"
          items={stateItems}
          selectedValue={stateId}
          onValueChange={(value) => {
            const parsedValue = value === "" ? "" : Number(value);
            setStateId(parsedValue as number | "");
            setCityId("");
          }}
          error={statesData && statesData.length === 0 ? "Nenhum estado disponível." : undefined}
          placeholder={statesLoading ? "Carregando..." : "Selecione o estado"}
        />
        <SelectField
          label="Cidade"
          items={cityItems}
          selectedValue={cityId}
          onValueChange={(value) => {
            const parsedValue = value === "" ? "" : Number(value);
            setCityId(parsedValue as number | "");
          }}
          error={
            typeof stateId === "number" && citiesData && citiesData.length === 0
              ? "Nenhuma cidade encontrada para o estado."
              : undefined
          }
          placeholder={
            typeof stateId !== "number" ? "Selecione um estado primeiro" : citiesLoading ? "Carregando..." : "Cidade"
          }
        />
        <InputField
          label="Senha"
          secureTextEntry
          autoCapitalize="none"
          value={password}
          onChangeText={setPassword}
          placeholder="********"
        />
        <InputField
          label="Confirmar senha"
          secureTextEntry
          autoCapitalize="none"
          value={confirmPassword}
          onChangeText={setConfirmPassword}
          placeholder="********"
        />
        <Button title="Criar conta" onPress={handleSubmit} loading={loading} />
        <View style={styles.footer}>
          <Text style={styles.footerText}>Já possui conta? </Text>
          <Link href="/(auth)/login" style={styles.link}>
            Fazer login
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
    marginBottom: 24,
  },
  title: {
    fontSize: 28,
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
