// frontend/src/lib/api.ts
import type { AuditResponse } from "@/types/audit";

// پشتیبانی استاندارد از Next.js با fallback به Vite و لوکال
const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  (typeof import.meta !== "undefined" && import.meta.env?.VITE_API_BASE_URL) ??
  "http://127.0.0.1:8000";

const AUDIT_ENDPOINT = `${API_BASE_URL}/api/audit`;
const DEFAULT_TIMEOUT_MS = 30_000;

export interface ApiErrorResponse {
  detail?: string | { msg: string; loc: string[] }[];
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
 * استخراج و فرمت‌بندی خطاهای سرور (به‌ویژه خطاهای ولیدیشن Pydantic/FastAPI)
 */
function extractErrorMessage(
  errorData: ApiErrorResponse | unknown,
  fallback: string
): string {
  if (typeof errorData === "object" && errorData !== null) {
    const data = errorData as ApiErrorResponse;

    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail) && data.detail.length > 0) {
      // فرمت ارورهای اعتبارسنجی 422 در FastAPI
      return data.detail.map((err) => `${err.loc.join(".")}: ${err.msg}`).join(" | ");
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
  const internalController = new AbortController();
  let isTimedOut = false;

  const timeoutId = setTimeout(() => {
    isTimedOut = true;
    internalController.abort();
  }, timeoutMs);

  // لیسنر برای لغو دستی کاربر از بیرون
  const handleExternalAbort = () => {
    internalController.abort();
  };

  if (options?.signal) {
    if (options.signal.aborted) {
      clearTimeout(timeoutId);
      throw new DOMException("Aborted", "AbortError");
    }
    options.signal.addEventListener("abort", handleExternalAbort, { once: true });
  }

  try {
    const response = await fetch(AUDIT_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({ url: trimmedUrl }),
      signal: internalController.signal,
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
      throw new Error("دیتای بازگشتی از سرور نامعتبر است و قابل پارس نیست.");
    }

    return data;
  } catch (error: unknown) {
    if (error instanceof DOMException && error.name === "AbortError") {
      if (isTimedOut) {
        throw new Error(`زمان پردازش به پایان رسید (بیش از ${timeoutMs / 1000} ثانیه). سرور یا دامنه مقصد پاسخگو نیست.`);
      }
      throw error; // خطای لغو دستی برای کامپوننت فرستاده شود تا UI الکی پیام ارور ندهد
    }

    if (error instanceof TypeError) {
      throw new Error(
        "عدم برقراری ارتباط با سرور بک‌اند. وضعیت اجرای سرویس FastAPI و تنظیمات CORS را بررسی کنید."
      );
    }

    throw error;
  } finally {
    clearTimeout(timeoutId);
    if (options?.signal) {
      options.signal.removeEventListener("abort", handleExternalAbort);
    }
  }
};
