import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef } from "react";

import { env } from "@/config/env";
import { useAuth } from "@/features/auth/auth-context";
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

type ReportEventPayload = {
  type?: string;
  report?: {
    id?: number;
  };
};

const RECONNECT_INTERVAL_MS = 5000;

export const useReportRealtimeUpdates = () => {
  const { tokens, status } = useAuth();
  const queryClient = useQueryClient();
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (status !== "authenticated" || !tokens?.access) {
      return () => {
        if (socketRef.current) {
          socketRef.current.close();
          socketRef.current = null;
        }
      };
    }

    let shouldReconnect = true;

    const scheduleReconnect = () => {
      if (!shouldReconnect) {
        return;
      }
      if (reconnectRef.current) {
        clearTimeout(reconnectRef.current);
      }
      reconnectRef.current = setTimeout(connect, RECONNECT_INTERVAL_MS);
    };

    const handleMessage = (event: { data: string }) => {
      try {
        const payload = JSON.parse(event.data) as ReportEventPayload;
        if (!payload?.type) {
          return;
        }
        if (payload.type === "report.created" || payload.type === "report.status_changed") {
          queryClient.invalidateQueries({ queryKey: ["reports"] });
          const reportId = payload.report?.id;
          if (typeof reportId === "number") {
            queryClient.invalidateQueries({ queryKey: reportKeys.detail(reportId) });
          }
        }
      } catch {
        // ignore malformed messages
      }
    };

    const connect = () => {
      const baseUrl = env.wsBaseUrl.replace(/\/$/, "");
      const wsUrl = `${baseUrl}/reports/?token=${encodeURIComponent(tokens.access)}`;
      const socket = new WebSocket(wsUrl);
      socketRef.current = socket;

      socket.onmessage = handleMessage;
      socket.onopen = () => {
        if (reconnectRef.current) {
          clearTimeout(reconnectRef.current);
          reconnectRef.current = null;
        }
      };
      socket.onclose = () => {
        socketRef.current = null;
        scheduleReconnect();
      };
      socket.onerror = () => {
        socket.close();
      };
    };

    connect();

    return () => {
      shouldReconnect = false;
      if (reconnectRef.current) {
        clearTimeout(reconnectRef.current);
        reconnectRef.current = null;
      }
      if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
      }
    };
  }, [tokens?.access, status, queryClient]);
};
