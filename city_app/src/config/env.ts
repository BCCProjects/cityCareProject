const requiredEnv = [
  "EXPO_PUBLIC_API_BASE_URL",
  "EXPO_PUBLIC_X_APP",
  "EXPO_PUBLIC_X_USER",
  "EXPO_PUBLIC_X_SIGNATURE",
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

const resolveApiBaseUrl = (rawUrl: string) => {
  if (typeof window === "undefined") {
    return rawUrl;
  }

  try {
    const parsed = new URL(rawUrl);
    const hostname = parsed.hostname.trim().toLowerCase();
    const shouldRewriteHost =
      hostname === "backend" ||
      hostname.endsWith(".docker") ||
      (hostname !== "localhost" && !hostname.includes("."));

    if (shouldRewriteHost) {
      const browserHost = window.location.hostname || "localhost";
      parsed.hostname = browserHost;
      if (!parsed.port) {
        const fallbackPort = parsed.protocol === "https:" ? "443" : "8000";
        parsed.port = fallbackPort;
      }
      return parsed.toString();
    }

    if (hostname === "localhost" && window.location.hostname && window.location.hostname !== "localhost") {
      parsed.hostname = window.location.hostname;
      return parsed.toString();
    }

    return rawUrl;
  } catch {
    return rawUrl;
  }
};

const maxAttachments = Number(process.env.EXPO_PUBLIC_MAX_ATTACHMENTS ?? "5");
const apiBaseUrl = resolveApiBaseUrl(process.env.EXPO_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api");
const googleMapsApiKey =
  process.env.EXPO_PUBLIC_GOOGLE_MAPS_SECRET_KEY ?? process.env.GOOGLE_MAPS_SECRET_KEY ?? "";

export const env = {
  apiBaseUrl,
  headers: {
    xApp: process.env.EXPO_PUBLIC_X_APP ?? "",
    xUser: process.env.EXPO_PUBLIC_X_USER ?? "",
    xSignature: process.env.EXPO_PUBLIC_X_SIGNATURE ?? "",
  },
  maxAttachments: Number.isFinite(maxAttachments) && maxAttachments > 0 ? maxAttachments : 5,
  googleMapsApiKey,
};
