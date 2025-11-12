import { Redirect } from "expo-router";

import { LoadingState } from "@/components/feedback/LoadingState";
import { useAuth } from "@/features/auth/auth-context";

export default function IndexScreen() {
  const { status } = useAuth();

  if (status === "loading") {
    return <LoadingState message="Carregando..." />;
  }

  if (status === "authenticated") {
    return <Redirect href="/(app)/(tabs)/reports" />;
  }

  return <Redirect href="/(auth)/login" />;
}
