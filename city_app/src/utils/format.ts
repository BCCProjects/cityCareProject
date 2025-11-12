import { format, parseISO } from "date-fns";

export const formatDate = (value: string | Date) => {
  try {
    const date = typeof value === "string" ? parseISO(value) : value;
    return format(date, "dd/MM/yyyy HH:mm");
  } catch {
    return value?.toString() ?? "";
  }
};
