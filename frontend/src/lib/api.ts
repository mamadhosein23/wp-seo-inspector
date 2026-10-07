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
 * فرمت‌بندی خطاهای اعتبارسنجی 422 در Pydantic/FastAPI
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
        .map((err) => `${err.loc.filter((l) => l !== "body").join(".")}: ${err.msg}`)
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

  // ترکیب سیگنال ابورت کاربر با سیگنال تایم‌اوت به روش مدرن
  const combinedSignal = options?.signal
    ? AbortSignal.any([options.signal, timeoutSignal])
    : timeoutSignal;

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
    if (error instanceof DOMException && error.name === "TimeoutError") {
      throw new Error(
        `مهلت پردازش به پایان رسید (بیش از ${timeoutMs / 1000} ثانیه). سرور یا دامنه مقصد پاسخگو نیست.`
      );
    }

    if (error instanceof DOMException && error.name === "AbortError") {
      throw error; // لغو دستی توسط کاربر
    }

    if (error instanceof TypeError) {
      throw new Error(
        "عدم برقراری ارتباط با سرور بک‌اند. وضعیت سرویس FastAPI و تنظیمات CORS را بررسی کنید."
      );
    }

    throw error;
  }
};
