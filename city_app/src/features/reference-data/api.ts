import { AxiosError } from "axios";

import { apiClient } from "@/lib/api-client";

import { Category, City, Department, State, Tag } from "./types";

const formatError = (error: unknown) => {
  if (error instanceof AxiosError && error.response?.data) {
    const data = error.response.data as Record<string, unknown>;
    return data.detail && typeof data.detail === "string" ? data.detail : "Erro ao consultar dado de referência.";
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Erro inesperado. Tente novamente.";
};

export const referenceApi = {
  async getStates(): Promise<State[]> {
    try {
      const response = await apiClient.get<State[]>("/states/");
      return response.data;
    } catch (error) {
      throw new Error(formatError(error));
    }
  },
  async getCities(stateId?: number): Promise<City[]> {
    try {
      const response = await apiClient.get<City[]>("/cities/", {
        params: stateId ? { state: stateId } : undefined,
      });
      return response.data;
    } catch (error) {
      throw new Error(formatError(error));
    }
  },
  async getDepartments(): Promise<Department[]> {
    try {
      const response = await apiClient.get<Department[]>("/departments/");
      return response.data;
    } catch (error) {
      throw new Error(formatError(error));
    }
  },
  async getCategories(departmentId?: number): Promise<Category[]> {
    try {
      const response = await apiClient.get<Category[]>("/categories/", {
        params: departmentId ? { department: departmentId } : undefined,
      });
      return response.data;
    } catch (error) {
      throw new Error(formatError(error));
    }
  },
  async getTags(): Promise<Tag[]> {
    try {
      const response = await apiClient.get<Tag[]>("/tags/");
      return response.data;
    } catch (error) {
      throw new Error(formatError(error));
    }
  },
};
