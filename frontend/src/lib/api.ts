import type { AuditResponse } from "@/types/audit";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ??
  "http://127.0.0.1:8000";

const AUDIT_ENDPOINT = `${API_BASE_URL}/api/audit`;
const DEFAULT_TIMEOUT_MS = 30_000;

export interface ValidationErrorItem {
  loc: (string | number)[];
  msg: string;
  type?: string;
}

export interface ApiErrorResponse {
  detail?: string | ValidationErrorItem[];
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

/**
 * Format Pydantic V2 and FastAPI 422 validation errors into human-readable strings.
 */
function extractErrorMessage(
  errorData: ApiErrorResponse | unknown,
  fallback: string
): string {
  if (typeof errorData === "object" && errorData !== null) {
    const data = errorData as ApiErrorResponse;

    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail) && data.detail.length > 0) {
      return data.detail
        .map((err) => {
          const path = Array.isArray(err.loc)
            ? err.loc.filter((l) => String(l) !== "body").join(".")
            : "";
          return path ? `${path}: ${err.msg}` : err.msg;
        })
        .join(" | ");
    }
    if (typeof data.message === "string") return data.message;
    if (typeof data.error === "string") return data.error;
  }

  return fallback;
}

async function parseJsonSafely<T>(response: Response): Promise<T | null> {
  try {
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

/**
 * Combine multiple AbortSignals with compatibility fallback for older runtimes.
 */
function combineSignals(signals: (AbortSignal | undefined)[]): AbortSignal {
  const activeSignals = signals.filter(
    (s): s is AbortSignal => typeof s !== "undefined"
  );

  if (typeof AbortSignal.any === "function") {
    return AbortSignal.any(activeSignals);
  }

  const controller = new AbortController();
  for (const signal of activeSignals) {
    if (signal.aborted) {
      controller.abort(signal.reason);
      return controller.signal;
    }
    signal.addEventListener(
      "abort",
      () => controller.abort(signal.reason),
      { once: true }
    );
  }
  return controller.signal;
}

export interface AuditRequestOptions {
  signal?: AbortSignal;
  timeoutMs?: number;
}

export const performAudit = async (
  url: string,
  options?: AuditRequestOptions
): Promise<AuditResponse> => {
  const trimmedUrl = url.trim();

  if (!trimmedUrl) {
    throw new Error("آدرس سایت نمی‌تواند خالی باشد.");
  }

  const timeoutMs = options?.timeoutMs ?? DEFAULT_TIMEOUT_MS;
  const timeoutSignal = AbortSignal.timeout(timeoutMs);
  const combinedSignal = combineSignals([options?.signal, timeoutSignal]);

  try {
    const response = await fetch(AUDIT_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({ url: trimmedUrl }),
      signal: combinedSignal,
    });

    if (!response.ok) {
      const errorData = await parseJsonSafely<ApiErrorResponse>(response);
      const fallbackMessage = `خطای سرور: ${response.status} ${response.statusText}`;
      const errorMessage = extractErrorMessage(errorData, fallbackMessage);

      throw new ApiError({
        message: errorMessage,
        status: response.status,
        statusText: response.statusText,
        data: errorData,
      });
    }

    const data = await parseJsonSafely<AuditResponse>(response);

    if (!data) {
      throw new Error("پاسخ دریافتی از سرور معتبر یا در قالب JSON نیست.");
    }

    return data;
  } catch (error: unknown) {
    const isTimeout =
      (error instanceof DOMException && error.name === "TimeoutError") ||
      (combinedSignal.aborted &&
        (combinedSignal.reason?.name === "TimeoutError" ||
          timeoutSignal.aborted));

    if (isTimeout) {
      throw new Error(
        `مهلت پردازش به پایان رسید (بیش از ${timeoutMs / 1000} ثانیه). سرور یا دامنه مقصد پاسخگو نیست.`
      );
    }

    if (error instanceof DOMException && error.name === "AbortError") {
      throw error;
    }

    if (error instanceof TypeError) {
      throw new Error(
        "عدم برقراری ارتباط با سرور بک‌اند. وضعیت سرویس FastAPI و تنظیمات CORS را بررسی کنید."
      );
    }

    throw error;
  }
};
