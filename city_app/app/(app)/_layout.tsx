import { Stack } from "expo-router";

export default function AppLayout() {
  return (
    <Stack>
      <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
      <Stack.Screen
        name="reports/[id]"
        options={{
          title: "Detalhes da ocorrência",
        }}
      />
    </Stack>
  );
}
