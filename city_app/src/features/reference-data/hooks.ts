import { useQuery } from "@tanstack/react-query";

import { referenceApi } from "./api";

export const referenceKeys = {
  states: ["reference", "states"] as const,
  cities: (stateId?: number) => ["reference", "cities", stateId ?? "all"] as const,
  categories: (departmentId?: number) => ["reference", "categories", departmentId ?? "all"] as const,
  departments: ["reference", "departments"] as const,
  tags: ["reference", "tags"] as const,
};

export const useStates = () =>
  useQuery({
    queryKey: referenceKeys.states,
    queryFn: referenceApi.getStates,
  });

export const useCities = (stateId?: number) =>
  useQuery({
    queryKey: referenceKeys.cities(stateId),
    queryFn: () => referenceApi.getCities(stateId),
    enabled: stateId !== undefined && stateId !== null,
  });

export const useCategories = (departmentId?: number) =>
  useQuery({
    queryKey: referenceKeys.categories(departmentId),
    queryFn: () => referenceApi.getCategories(departmentId),
  });

export const useDepartments = () =>
  useQuery({
    queryKey: referenceKeys.departments,
    queryFn: referenceApi.getDepartments,
  });

export const useTags = () =>
  useQuery({
    queryKey: referenceKeys.tags,
    queryFn: referenceApi.getTags,
  });
