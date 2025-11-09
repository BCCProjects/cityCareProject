import { AxiosError } from "axios";

import { apiClient } from "@/lib/api-client";

import { AuthTokens, CitizenPayload, CitizenResponse, LoginPayload } from "./types";

const CITIZEN_REGISTER_URL = "/auth/citizens/register/";
const CITIZEN_LOGIN_URL = "/auth/citizens/token/";

const formatError = (error: unknown) => {
  if ((error as AxiosError)?.response?.data) {
    const data = (error as AxiosError).response?.data as Record<string, unknown>;
    if (typeof data.detail === "string") {
      return data.detail;
    }
    const errors = Object.entries(data)
      .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(", ") : value}`)
      .join("\n");
    return errors || "Erro ao comunicar com o servidor.";
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Erro inesperado. Tente novamente.";
};

export const authApi = {
  async registerCitizen(payload: CitizenPayload): Promise<CitizenResponse> {
    try {
      const response = await apiClient.post<CitizenResponse>(CITIZEN_REGISTER_URL, payload);
      return response.data;
    } catch (error) {
      throw new Error(formatError(error));
    }
  },
  async loginCitizen(payload: LoginPayload): Promise<AuthTokens> {
    try {
      const response = await apiClient.post<AuthTokens>(CITIZEN_LOGIN_URL, payload);
      return response.data;
    } catch (error) {
      throw new Error(formatError(error));
    }
  },
};
