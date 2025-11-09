import axios, { AxiosError, isAxiosError } from "axios";

import { env } from "@/config/env";

let authToken: string | null = null;
let unauthorizedHandler: (() => void) | null = null;

export const setAuthToken = (token: string | null) => {
  authToken = token;
};

export const setUnauthorizedHandler = (handler: (() => void) | null) => {
  unauthorizedHandler = handler;
};

export const apiClient = axios.create({
  baseURL: env.apiBaseUrl.replace(/\/$/, ""),
  timeout: 15000,
});

apiClient.interceptors.request.use((config) => {
  const headers = config.headers ?? {};
  headers["X-APP"] = env.headers.xApp;
  headers["X-USER"] = env.headers.xUser;
  headers["X-SIGNATURE"] = env.headers.xSignature;
  if (authToken) {
    headers.Authorization = `Bearer ${authToken}`;
  }
  config.headers = headers;
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (isAxiosError(error) && error.response?.status === 401) {
      unauthorizedHandler?.();
    }
    return Promise.reject(error);
  },
);
