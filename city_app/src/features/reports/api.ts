import { AxiosError } from "axios";
import { Platform } from "react-native";

import { apiClient } from "@/lib/api-client";

import { CreateReportPayload, ReportDetail, ReportListItem, ReportPriority, ReportStatus } from "./types";

const formatError = (error: unknown) => {
  if (error instanceof AxiosError && error.response?.data) {
    const data = error.response.data as Record<string, unknown>;
    if (typeof data.detail === "string") {
      return data.detail;
    }
    if (Array.isArray(data.non_field_errors)) {
      return data.non_field_errors.join(", ");
    }
    const firstError = Object.values(data)[0];
    if (Array.isArray(firstError)) {
      return firstError.join(", ");
    }
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Não foi possível concluir a operação.";
};

export type ListReportsParams = Partial<{
  status: ReportStatus;
  category: number;
  department: number;
  priority: ReportPriority;
  tag: number;
}>;

type PreparedAttachment =
  | { target: "web"; blob: Blob; name: string }
  | { target: "native"; file: Blob };

const prepareAttachment = async (attachment: { uri: string; name: string; type: string }): Promise<PreparedAttachment> => {
  if (Platform.OS === "web") {
    const response = await fetch(attachment.uri);
    const blob = await response.blob();
    return { target: "web", blob, name: attachment.name };
  }
  return {
    target: "native",
    file: {
      uri: attachment.uri,
      name: attachment.name,
      type: attachment.type,
    } as unknown as Blob,
  };
};

export const reportsApi = {
  async listReports(params?: ListReportsParams): Promise<{ results: ReportListItem[] }> {
    try {
      const response = await apiClient.get<ReportListItem[]>("/reports/", { params });
      return { results: response.data };
    } catch (error) {
      throw new Error(formatError(error));
    }
  },
  async getReport(id: number): Promise<ReportDetail> {
    try {
      const response = await apiClient.get<ReportDetail>(`/reports/${id}/`);
      return response.data;
    } catch (error) {
      throw new Error(formatError(error));
    }
  },
  async createReport(payload: CreateReportPayload): Promise<ReportDetail> {
    const formData = new FormData();
    formData.append("category_id", String(payload.category_id));
    formData.append("title", payload.title);
    formData.append("description", payload.description);
    formData.append("priority", payload.priority);
    formData.append("address", payload.address);
    formData.append("neighborhood", payload.neighborhood);
    formData.append("latitude", payload.latitude);
    formData.append("longitude", payload.longitude);

    payload.tag_ids?.forEach((tagId) => {
      formData.append("tags", String(tagId));
    });

    if (payload.attachments?.length) {
      for (const attachment of payload.attachments) {
        const prepared = await prepareAttachment(attachment);
        if (prepared.target === "web") {
          formData.append("attachments", prepared.blob, prepared.name);
        } else {
          formData.append("attachments", prepared.file);
        }
      }
    }

    try {
      const response = await apiClient.post<ReportDetail>("/reports/", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      return response.data;
    } catch (error) {
      throw new Error(formatError(error));
    }
  },
};
