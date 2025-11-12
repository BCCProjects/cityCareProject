import { Category, Department, Tag } from "@/features/reference-data/types";

export type ReportStatus =
  | "ABERTO"
  | "ANALISANDO"
  | "DEFERIDO"
  | "INDEFERIDO"
  | "EM_ANDAMENTO"
  | "CONCLUIDO"
  | "IGNORADO";

export type ReportPriority = "BAIXO" | "MODERADO" | "ALTO";

export type ReportListItem = {
  id: number;
  title: string;
  status: ReportStatus;
  priority: ReportPriority;
  created_at: string;
  category: Category;
  tags: Tag[];
};

export type ReportDetail = {
  id: number;
  title: string;
  description: string;
  priority: ReportPriority;
  status: ReportStatus;
  denied_reason: string | null;
  address: string;
  neighborhood: string;
  latitude: string;
  longitude: string;
  created_at: string;
  last_status_at: string;
  category: Category;
  department: Department;
  organization: string;
  tags: Tag[];
  attachments: {
    id: number;
    file: string;
    description: string;
  }[];
};

export type CreateReportPayload = {
  category_id: number;
  title: string;
  description: string;
  priority: ReportPriority;
  address: string;
  neighborhood: string;
  latitude: string;
  longitude: string;
  tag_ids?: number[];
  attachments?: {
    uri: string;
    name: string;
    type: string;
  }[];
};

export const REPORT_STATUS_OPTIONS: { value: ReportStatus; label: string }[] = [
  { value: "ABERTO", label: "Aberto" },
  { value: "ANALISANDO", label: "Analisando" },
  { value: "DEFERIDO", label: "Deferido" },
  { value: "INDEFERIDO", label: "Indeferido" },
  { value: "EM_ANDAMENTO", label: "Em andamento" },
  { value: "CONCLUIDO", label: "Concluido" },
  { value: "IGNORADO", label: "Ignorado" },
];

export const REPORT_PRIORITY_OPTIONS: { value: ReportPriority; label: string }[] = [
  { value: "BAIXO", label: "Baixa" },
  { value: "MODERADO", label: "Moderada" },
  { value: "ALTO", label: "Alta" },
];
