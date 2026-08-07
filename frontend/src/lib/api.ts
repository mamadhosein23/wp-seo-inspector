// frontend/src/services/auditApi.ts

import type { AuditResponse } from "@/types/audit";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

const AUDIT_ENDPOINT = `${API_BASE_URL}/api/audit`;

const DEFAULT_TIMEOUT_MS = 30_000;

interface ApiErrorResponse {
  detail?: string;
  message?: string;
  error?: string;
}

export class ApiError extends Error {
  status: number;
  statusText: string;
  data: unknown;

  constructor({
    message,
    status,
    statusText,
    data,
  }: {
    message: string;
    status: number;
    statusText: string;
    data: unknown;
  }) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.statusText = statusText;
    this.data = data;
  }
}

const getErrorMessage = (
  errorData: ApiErrorResponse | unknown,
  fallback: string
): string => {
  if (
    typeof errorData === "object" &&
    errorData !== null
  ) {
    const data = errorData as ApiErrorResponse;

    if (typeof data.detail === "string") return data.detail;
    if (typeof data.message === "string") return data.message;
    if (typeof data.error === "string") return data.error;
  }

  return fallback;
};

const parseJsonSafely = async <T>(response: Response): Promise<T | null> => {
  try {
    return (await response.json()) as T;
  } catch {
    return null;
  }
};

export const performAudit = async (
  url: string,
  options?: {
    signal?: AbortSignal;
    timeoutMs?: number;
  }
): Promise<AuditResponse> => {
  const trimmedUrl = url.trim();

  if (!trimmedUrl) {
    throw new Error("آدرس سایت نمی‌تواند خالی باشد.");
  }

  const controller = new AbortController();
  const timeoutMs = options?.timeoutMs ?? DEFAULT_TIMEOUT_MS;

  const timeoutId = window.setTimeout(() => {
    controller.abort();
  }, timeoutMs);

  const signal = options?.signal ?? controller.signal;

  try {
    const response = await fetch(AUDIT_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({ url: trimmedUrl }),
      signal,
    });

    if (!response.ok) {
      const errorData = await parseJsonSafely<ApiErrorResponse>(response);

      const fallbackMessage = `HTTP Error: ${response.status} ${response.statusText}`;

      const errorMessage = getErrorMessage(errorData, fallbackMessage);

      throw new ApiError({
        message: errorMessage,
        status: response.status,
        statusText: response.statusText,
        data: errorData,
      });
    }

    const data = await parseJsonSafely<AuditResponse>(response);

    if (!data) {
      throw new Error("پاسخ سرور معتبر نیست یا JSON قابل خواندن نیست.");
    }

    return data;
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error("درخواست بیش از حد طول کشید. لطفاً دوباره تلاش کن.");
    }

    if (error instanceof TypeError) {
      throw new Error(
        "ارتباط با سرور برقرار نشد. بک‌اند، CORS یا اتصال شبکه را بررسی کن."
      );
    }

    throw error;d
  } finally {
    window.clearTimeout(timeoutId);
  }
};
