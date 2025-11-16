const requiredEnv = [
  "EXPO_PUBLIC_API_BASE_URL",  
  "EXPO_PUBLIC_GOOGLE_MAPS_SECRET_KEY",
] as const;

const missingKeys = requiredEnv.filter((key) => !process.env[key]);

if (missingKeys.length > 0) {
  console.warn(
    `Missing environment variables: ${missingKeys.join(
      ", ",
    )}. Please ensure they are defined in city_app/.env`,
  );
}

const shouldRewriteHost = (hostname: string) => {
  const normalized = hostname.trim().toLowerCase();
  return (
    normalized === "backend" ||
    normalized.endsWith(".docker") ||
    (normalized !== "localhost" && !normalized.includes("."))
  );
};

const rewriteHostForBrowser = (parsed: URL) => {
  if (typeof window === "undefined") {
    return parsed;
  }

  const hostname = parsed.hostname.trim().toLowerCase();
  if (shouldRewriteHost(hostname)) {
    const browserHost = window.location.hostname || "localhost";
    parsed.hostname = browserHost;
    if (!parsed.port) {
      parsed.port = parsed.protocol === "https:" ? "443" : "8000";
    }
    return parsed;
  }

  if (hostname === "localhost" && window.location.hostname && window.location.hostname !== "localhost") {
    parsed.hostname = window.location.hostname;
  }
  return parsed;
};

const resolveApiBaseUrl = (rawUrl: string) => {
  if (typeof window === "undefined") {
    return rawUrl;
  }

  try {
    const parsed = new URL(rawUrl);
    return rewriteHostForBrowser(parsed).toString();
  } catch {
    return rawUrl;
  }
};

const deriveWsBaseFromApi = (httpBaseUrl: string) => {
  try {
    const parsed = new URL(httpBaseUrl);
    parsed.protocol = parsed.protocol === "https:" ? "wss:" : "ws:";
    const sanitizedPath = parsed.pathname.replace(/\/api\/?$/, "");
    parsed.pathname = `${sanitizedPath}/ws`;
    parsed.search = "";
    parsed.hash = "";
    return rewriteHostForBrowser(parsed).toString().replace(/\/$/, "");
  } catch {
    return "ws://localhost:8000/ws";
  }
};

const resolveWsBaseUrl = (rawUrl: string | undefined, httpBaseUrl: string) => {
  const fallback = deriveWsBaseFromApi(httpBaseUrl);
  if (!rawUrl) {
    return fallback;
  }
  try {
    const parsed = new URL(rawUrl);
    return rewriteHostForBrowser(parsed).toString().replace(/\/$/, "");
  } catch {
    return fallback;
  }
};

const maxAttachments = Number(process.env.EXPO_PUBLIC_MAX_ATTACHMENTS ?? "5");
const apiBaseUrl = resolveApiBaseUrl(process.env.EXPO_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api");
const googleMapsApiKey =
  process.env.EXPO_PUBLIC_GOOGLE_MAPS_SECRET_KEY ?? process.env.GOOGLE_MAPS_SECRET_KEY ?? "";
const wsBaseUrl = resolveWsBaseUrl(process.env.EXPO_PUBLIC_WS_BASE_URL, apiBaseUrl);

export const env = {
  apiBaseUrl,
  wsBaseUrl,
  headers: {
    xApp: process.env.EXPO_PUBLIC_X_APP ?? "",
    xUser: process.env.EXPO_PUBLIC_X_USER ?? "",
    xSignature: process.env.EXPO_PUBLIC_X_SIGNATURE ?? "",
  },
  maxAttachments: Number.isFinite(maxAttachments) && maxAttachments > 0 ? maxAttachments : 5,
  googleMapsApiKey,
};
