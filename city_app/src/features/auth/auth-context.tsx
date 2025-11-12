import { PropsWithChildren, createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { Alert } from "react-native";
import { jwtDecode } from "jwt-decode";

import { queryClient } from "@/lib/query-client";
import { setAuthToken, setUnauthorizedHandler } from "@/lib/api-client";

import { authApi } from "./api";
import { authStorage } from "./token-storage";
import { AuthTokens, AuthUser, CitizenPayload, CitizenResponse, LoginPayload } from "./types";

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
  exp?: number;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const TOKEN_EXPIRATION_GRACE_SECONDS = 30;

const getTokenExpiration = (token: string): number | null => {
  try {
    const decoded = jwtDecode<TokenPayload>(token);
    return typeof decoded.exp === "number" ? decoded.exp : null;
  } catch {
    return null;
  }
};

const isTokenExpired = (token: string, toleranceSeconds = TOKEN_EXPIRATION_GRACE_SECONDS) => {
  const expiration = getTokenExpiration(token);
  if (!expiration) {
    return false;
  }
  const nowInSeconds = Date.now() / 1000;
  return expiration - toleranceSeconds <= nowInSeconds;
};

const mapCitizenToAuthUser = (citizen: CitizenResponse): AuthUser => ({
  id: citizen.id,
  email: citizen.email,
  firstName: citizen.first_name,
  lastName: citizen.last_name,
  phone: citizen.phone,
  cityName: citizen.city?.name,
  stateAbbreviation: citizen.city?.state?.abbreviation,
});

const buildUserFromToken = (token: string): AuthUser => {
  try {
    const decoded = jwtDecode<TokenPayload>(token);
    const inferredId = decoded.sub ? Number(decoded.sub) : undefined;
    return {
      id: typeof inferredId === "number" && Number.isFinite(inferredId) ? inferredId : undefined,
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
  const sessionTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    let mounted = true;

    const bootstrap = async () => {
      try {
        const [storedTokens, storedUser] = await Promise.all([authStorage.getTokens(), authStorage.getUser()]);
        if (!mounted) {
          return;
        }
        if (!storedTokens?.access || !storedTokens?.refresh) {
          setStatus("unauthenticated");
          return;
        }
        if (isTokenExpired(storedTokens.access)) {
          await authStorage.clearAll();
          if (mounted) {
            setStatus("unauthenticated");
          }
          return;
        }
        setAuthToken(storedTokens.access);
        setTokens(storedTokens);
        setUser(storedUser ?? buildUserFromToken(storedTokens.access));
        setStatus("authenticated");
        try {
          const profile = await authApi.getCitizenProfile();
          const normalizedUser = mapCitizenToAuthUser(profile);
          await authStorage.saveUser(normalizedUser);
          if (mounted) {
            setUser(normalizedUser);
          }
        } catch (profileError) {
          console.warn("Failed to refresh citizen profile", profileError);
        }
      } catch (error) {
        console.error("Failed to restore auth session", error);
        Alert.alert("SessÃ£o", "NÃ£o foi possÃ­vel restaurar a sessÃ£o. FaÃ§a login novamente.");
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

  useEffect(() => {
    if (sessionTimeoutRef.current) {
      clearTimeout(sessionTimeoutRef.current);
      sessionTimeoutRef.current = null;
    }
    const accessToken = tokens?.access;
    if (!accessToken) {
      return;
    }
    const expiration = getTokenExpiration(accessToken);
    if (!expiration) {
      return;
    }
    const timeoutDuration = expiration * 1000 - Date.now() - TOKEN_EXPIRATION_GRACE_SECONDS * 1000;
    if (timeoutDuration <= 0) {
      signOut().catch((error) => {
        console.error("Failed to auto sign out after token expiration", error);
      });
      return;
    }
    sessionTimeoutRef.current = setTimeout(() => {
      Alert.alert("Sessão expirada", "Sua sessão expirou. Faça login novamente.");
      signOut().catch((error) => {
        console.error("Failed to auto sign out after token expiration", error);
      });
    }, timeoutDuration);
    return () => {
      if (sessionTimeoutRef.current) {
        clearTimeout(sessionTimeoutRef.current);
        sessionTimeoutRef.current = null;
      }
    };
  }, [tokens?.access, signOut]);

  const persistSession = useCallback(async (newTokens: AuthTokens, newUser: AuthUser | null) => {
    await authStorage.saveTokens(newTokens);
    await authStorage.saveUser(newUser ?? null);
    setAuthToken(newTokens.access);
    setTokens(newTokens);
    setUser(newUser ?? buildUserFromToken(newTokens.access));
    setStatus("authenticated");
  }, []);

  const signIn = useCallback(
    async (payload: LoginPayload) => {
      const newTokens = await authApi.loginCitizen(payload);
      setAuthToken(newTokens.access);
      let profile: AuthUser | null = null;
      try {
        const citizenProfile = await authApi.getCitizenProfile();
        profile = mapCitizenToAuthUser(citizenProfile);
      } catch (error) {
        console.error("Failed to fetch citizen profile after login", error);
      }
      await persistSession(newTokens, profile);
    },
    [persistSession],
  );

  const register = useCallback(
    async (payload: CitizenPayload) => {
      const citizen = await authApi.registerCitizen(payload);
      const newTokens = await authApi.loginCitizen({ email: payload.email, password: payload.password });
      const registeredUser = mapCitizenToAuthUser(citizen);
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

