import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { reportsApi, ListReportsParams } from "./api";
import { CreateReportPayload, ReportDetail } from "./types";

export const reportKeys = {
  lists: (params?: ListReportsParams) => ["reports", "list", params ?? "all"] as const,
  detail: (id: number) => ["reports", "detail", id] as const,
};

export const useReports = (params?: ListReportsParams) =>
  useQuery({
    queryKey: reportKeys.lists(params),
    queryFn: () => reportsApi.listReports(params),
  });

export const useReportDetail = (id: number | null) =>
  useQuery({
    queryKey: reportKeys.detail(id ?? 0),
    queryFn: () => reportsApi.getReport(id ?? 0),
    enabled: id !== null,
  });

export const useCreateReport = () => {
  const queryClient = useQueryClient();

  return useMutation<ReportDetail, Error, CreateReportPayload>({
    mutationFn: reportsApi.createReport,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reports"] });
    },
  });
};
