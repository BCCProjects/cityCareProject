import { PropsWithChildren, createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { Alert } from "react-native";
import { jwtDecode } from "jwt-decode";

import { queryClient } from "@/lib/query-client";
import { setAuthToken, setUnauthorizedHandler } from "@/lib/api-client";

import { authApi } from "./api";
import { authStorage } from "./token-storage";
import { AuthTokens, AuthUser, CitizenPayload, LoginPayload } from "./types";

type AuthStatus = "loading" | "authenticated" | "unauthenticated";

type AuthContextValue = {
  status: AuthStatus;
  user: AuthUser | null;
  tokens: AuthTokens | null;
  signIn: (payload: LoginPayload) => Promise<void>;
  register: (payload: CitizenPayload) => Promise<void>;
  signOut: () => Promise<void>;
};

type TokenPayload = {
  email?: string;
  sub?: string;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const buildUserFromToken = (token: string): AuthUser => {
  try {
    const decoded = jwtDecode<TokenPayload>(token);
    return {
      email: decoded.email ?? "",
    };
  } catch {
    return {
      email: "",
    };
  }
};

export const AuthProvider = ({ children }: PropsWithChildren) => {
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [tokens, setTokens] = useState<AuthTokens | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    let mounted = true;

    const bootstrap = async () => {
      try {
        const [storedTokens, storedUser] = await Promise.all([authStorage.getTokens(), authStorage.getUser()]);
        if (!mounted) {
          return;
        }
        if (storedTokens?.access && storedTokens?.refresh) {
          setAuthToken(storedTokens.access);
          setTokens(storedTokens);
          setUser(storedUser ?? buildUserFromToken(storedTokens.access));
          setStatus("authenticated");
        } else {
          setStatus("unauthenticated");
        }
      } catch (error) {
        console.error("Failed to restore auth session", error);
        Alert.alert("Sessão", "Não foi possível restaurar a sessão. Faça login novamente.");
        await authStorage.clearAll();
        if (mounted) {
          setStatus("unauthenticated");
        }
      }
    };

    bootstrap();

    return () => {
      mounted = false;
    };
  }, []);

  const signOut = useCallback(async () => {
    await authStorage.clearAll();
    queryClient.clear();
    setAuthToken(null);
    setTokens(null);
    setUser(null);
    setStatus("unauthenticated");
  }, []);

  useEffect(() => {
    setUnauthorizedHandler(() => {
      signOut().catch((error) => {
        console.error("Failed to sign out after unauthorized response", error);
      });
    });
    return () => {
      setUnauthorizedHandler(null);
    };
  }, [signOut]);

  const persistSession = useCallback(async (newTokens: AuthTokens, newUser: AuthUser | null) => {
    await authStorage.saveTokens(newTokens);
    if (newUser) {
      await authStorage.saveUser(newUser);
    }
    setAuthToken(newTokens.access);
    setTokens(newTokens);
    setUser(newUser ?? buildUserFromToken(newTokens.access));
    setStatus("authenticated");
  }, []);

  const signIn = useCallback(
    async (payload: LoginPayload) => {
      const newTokens = await authApi.loginCitizen(payload);
      const inferredUser = buildUserFromToken(newTokens.access);
      const mergedUser: AuthUser = {
        ...inferredUser,
        email: inferredUser.email || payload.email,
      };
      await persistSession(newTokens, mergedUser);
    },
    [persistSession],
  );

  const register = useCallback(
    async (payload: CitizenPayload) => {
      const citizen = await authApi.registerCitizen(payload);
      const newTokens = await authApi.loginCitizen({ email: payload.email, password: payload.password });
      const registeredUser: AuthUser = {
        id: citizen.id,
        email: citizen.email,
        firstName: citizen.first_name,
        lastName: citizen.last_name,
        phone: citizen.phone,
        cityName: citizen.city?.name,
        stateAbbreviation: citizen.city?.state?.abbreviation,
      };
      await persistSession(newTokens, registeredUser);
    },
    [persistSession],
  );

  const value = useMemo<AuthContextValue>(
    () => ({
      status,
      user,
      tokens,
      signIn,
      register,
      signOut,
    }),
    [status, user, tokens, signIn, register, signOut],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
