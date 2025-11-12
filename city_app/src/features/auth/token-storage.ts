import AsyncStorage from "@react-native-async-storage/async-storage";
import * as SecureStore from "expo-secure-store";

import { AuthTokens, AuthUser } from "./types";

const ACCESS_KEY = "citycare_access_token";
const REFRESH_KEY = "citycare_refresh_token";
const USER_KEY = "citycare_auth_user";

let secureStoreAvailable: boolean | null = null;

const ensureSecureStoreAvailability = async () => {
  if (secureStoreAvailable === null) {
    secureStoreAvailable = await SecureStore.isAvailableAsync();
  }
  return secureStoreAvailable;
};

const setItem = async (key: string, value: string) => {
  if (await ensureSecureStoreAvailability()) {
    await SecureStore.setItemAsync(key, value);
    return;
  }
  await AsyncStorage.setItem(key, value);
};

const getItem = async (key: string) => {
  if (await ensureSecureStoreAvailability()) {
    return SecureStore.getItemAsync(key);
  }
  return AsyncStorage.getItem(key);
};

const deleteItem = async (key: string) => {
  if (await ensureSecureStoreAvailability()) {
    await SecureStore.deleteItemAsync(key);
    return;
  }
  await AsyncStorage.removeItem(key);
};

export const authStorage = {
  async saveTokens(tokens: AuthTokens) {
    await Promise.all([setItem(ACCESS_KEY, tokens.access), setItem(REFRESH_KEY, tokens.refresh)]);
  },
  async getTokens(): Promise<AuthTokens | null> {
    const [access, refresh] = await Promise.all([getItem(ACCESS_KEY), getItem(REFRESH_KEY)]);
    if (!access || !refresh) {
      return null;
    }
    return { access, refresh };
  },
  async clearTokens() {
    await Promise.all([deleteItem(ACCESS_KEY), deleteItem(REFRESH_KEY)]);
  },
  async saveUser(user: AuthUser | null) {
    if (!user) {
      await deleteItem(USER_KEY);
      return;
    }
    await setItem(USER_KEY, JSON.stringify(user));
  },
  async getUser(): Promise<AuthUser | null> {
    const raw = await getItem(USER_KEY);
    if (!raw) {
      return null;
    }
    try {
      return JSON.parse(raw) as AuthUser;
    } catch {
      await deleteItem(USER_KEY);
      return null;
    }
  },
  async clearAll() {
    await Promise.all([authStorage.clearTokens(), deleteItem(USER_KEY)]);
  },
};
