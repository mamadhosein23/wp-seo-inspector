"use client";

import React, { useState, useRef, useEffect, useCallback, memo } from "react";
import {
  Loader2,
  Zap,
  Globe,
  AlertCircle,
  History,
  X,
  Sparkles,
  CheckCircle2,
} from "lucide-react";
import { performAudit } from "@/lib/api";
import { AuditResponse } from "@/types/audit";
import { cn } from "@/lib/utils";

interface UrlFormProps {
  onAuditStart: () => void;
  onAuditComplete: (result: AuditResponse) => void;
  onError: (error: string) => void;
  defaultUrl?: string;
  className?: string;
}

// ----------------------------------------------------
// توابع کمکی اعتبارسنجی و نرمال‌سازی URL
// ----------------------------------------------------
function normalizeAndValidateUrl(rawInput: string): { isValid: boolean; normalizedUrl: string; errorMsg?: string } {
  let trimmed = rawInput.trim();
  if (!trimmed) {
    return { isValid: false, normalizedUrl: "", errorMsg: "آدرس وب‌سایت نمی‌تواند خالی باشد." };
  }

  // اضافه کردن خودکار https در صورت عدم تایپ پروتکل
  if (!/^https?:\/\//i.test(trimmed)) {
    trimmed = `https://${trimmed}`;
  }

  try {
    const parsed = new URL(trimmed);
    const hasValidHostname = parsed.hostname.includes(".") && parsed.hostname.split(".")[1]?.length >= 2;

    if (!hasValidHostname) {
      return { isValid: false, normalizedUrl: trimmed, errorMsg: "دامنه وارد شده ساختار معتبری ندارد (مثال: example.com)." };
    }

    return { isValid: true, normalizedUrl: parsed.toString() };
  } catch {
    return { isValid: false, normalizedUrl: trimmed, errorMsg: "فرمت آدرس URL نامعتبر است." };
  }
}

// ----------------------------------------------------
// کامپوننت اصلی فرم تحلیل
// ----------------------------------------------------
export function UrlForm({
  onAuditStart,
  onAuditComplete,
  onError,
  defaultUrl = "https://tamironlineesfahan.ir",
  className,
}: UrlFormProps) {
  const [url, setUrl] = useState<string>(defaultUrl);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [recentUrls, setRecentUrls] = useState<string[]>([]);
  const [showHistory, setShowHistory] = useState<boolean>(false);

  const abortControllerRef = useRef<AbortController | null>(null);
  const historyRef = useRef<HTMLDivElement>(null);

  // بارگذاری تاریخچه آدرس‌های تحلیل‌شده از LocalStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem("recent_audit_urls");
      if (stored) {
        setRecentUrls(JSON.parse(stored));
      }
    } catch {
      // نادیده‌گرفتن خطای localStorage در محیط‌های Private یا فاقد مجوز
    }
  }, []);

  // بستن منوی تاریخچه در صورت کلیک خارج از آن
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (historyRef.current && !historyRef.current.contains(e.target as Node)) {
        setShowHistory(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // ذخیره آدرس موفق در LocalStorage
  const saveToHistory = useCallback((savedUrl: string) => {
    setRecentUrls((prev) => {
      const filtered = prev.filter((item) => item !== savedUrl);
      const updated = [savedUrl, ...filtered].slice(0, 5);
      try {
        localStorage.setItem("recent_audit_urls", JSON.stringify(updated));
      } catch {}
      return updated;
    });
  }, []);

  const handleClearInput = () => {
    setUrl("");
    setValidationError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const { isValid, normalizedUrl, errorMsg } = normalizeAndValidateUrl(url);

    if (!isValid) {
      setValidationError(errorMsg || "آدرس وارد شده معتبر نیست.");
      return;
    }

    setValidationError(null);
    setUrl(normalizedUrl);
    onError("");
    setIsLoading(true);
    onAuditStart();

    // لغو ریکوئست قبلی در صورت فعال بودن
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    try {
      const result = await performAudit(normalizedUrl);
      saveToHistory(normalizedUrl);
      onAuditComplete(result);
    } catch (err: any) {
      if (err?.name === "AbortError") return;
      const message =
        err instanceof Error
          ? err.message
          : "خطای ناشناخته در ارتباط با سرور تحلیل‌گر رخ داد.";
      console.error("Audit Request Error:", err);
      onError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      dir="rtl"
      className={cn("w-full max-w-2xl mx-auto space-y-3 font-sans", className)}
    >
      <form onSubmit={handleSubmit} noValidate className="relative w-full">
        <div
          className={cn(
            "relative flex items-center rounded-2xl border transition-all duration-200 shadow-sm",
            "bg-white dark:bg-zinc-900",
            validationError
              ? "border-red-500 ring-2 ring-red-500/10"
              : "border-gray-200 dark:border-zinc-800 focus-within:border-indigo-500 focus-within:ring-4 focus-within:ring-indigo-500/10"
          )}
        >
          {/* آیکون وضعیت و ورودی */}
          <div className="ps-4 text-gray-400 dark:text-zinc-500 shrink-0">
            <Globe className="w-5 h-5" />
          </div>

          <input
            type="url"
            dir="ltr"
            placeholder="https://example.com/target-page"
            value={url}
            onChange={(e) => {
              setUrl(e.target.value);
              if (validationError) setValidationError(null);
            }}
            disabled={isLoading}
            className={cn(
              "w-full py-4 px-3 text-sm sm:text-base font-mono tracking-tight bg-transparent text-gray-900 dark:text-zinc-100",
              "placeholder:text-gray-400 dark:placeholder:text-zinc-600 focus:outline-none disabled:opacity-50"
            )}
            aria-invalid={Boolean(validationError)}
          />

          {/* دکمه پاک کردن سریع ورودی */}
          {url && !isLoading && (
            <button
              type="button"
              onClick={handleClearInput}
              className="p-1.5 me-1 text-gray-400 hover:text-gray-600 dark:hover:text-zinc-200 transition-colors rounded-full hover:bg-gray-100 dark:hover:bg-zinc-800"
              title="پاک‌کردن متن"
            >
              <X className="w-4 h-4" />
            </button>
          )}

          {/* دکمه باز کردن تاریخچه */}
          {recentUrls.length > 0 && !isLoading && (
            <button
              type="button"
              onClick={() => setShowHistory((prev) => !prev)}
              className="p-2 me-1 text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors rounded-lg hover:bg-gray-100 dark:hover:bg-zinc-800"
              title="آدرس‌های اخیر"
            >
              <History className="w-4 h-4" />
            </button>
          )}

          {/* دکمه سابمیت واکنش‌گرا و سازگار با RTL */}
          <div className="p-1.5">
            <button
              type="submit"
              disabled={isLoading || !url.trim()}
              className={cn(
                "inline-flex items-center justify-center gap-2 px-5 py-3 rounded-xl font-bold text-sm text-white",
                "bg-indigo-600 hover:bg-indigo-700 active:scale-[0.98] transition-all shadow-md shadow-indigo-500/20",
                "disabled:bg-indigo-400 dark:disabled:bg-indigo-600/40 disabled:cursor-not-allowed disabled:shadow-none disabled:scale-100"
              )}
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin shrink-0" />
                  <span className="hidden sm:inline">در حال تحلیل...</span>
                </>
              ) : (
                <>
                  <Zap className="w-4 h-4 fill-current shrink-0" />
                  <span>تحلیل سئو</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* منوی بازشونده تاریخچه جستجوهای اخیر */}
        {showHistory && (
          <div
            ref={historyRef}
            className="absolute z-20 top-full start-0 end-0 mt-2 p-2 rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-xl"
          >
            <div className="flex items-center justify-between px-3 py-1.5 border-b border-gray-100 dark:border-zinc-800 mb-1 text-xs text-gray-400">
              <span>آدرس‌های بررسی‌شده اخیر</span>
              <button
                type="button"
                onClick={() => {
                  setRecentUrls([]);
                  localStorage.removeItem("recent_audit_urls");
                  setShowHistory(false);
                }}
                className="hover:text-red-500 transition-colors"
              >
                پاک‌سازی تاریخچه
              </button>
            </div>
            {recentUrls.map((item) => (
              <button
                key={item}
                type="button"
                onClick={() => {
                  setUrl(item);
                  setShowHistory(false);
                }}
                className="w-full flex items-center justify-between p-2.5 rounded-lg text-start text-xs font-mono text-gray-700 dark:text-zinc-300 hover:bg-indigo-50/70 dark:hover:bg-indigo-950/30 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors"
              >
                <span className="truncate max-w-[450px]" dir="ltr">
                  {item}
                </span>
                <CheckCircle2 className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100" />
              </button>
            ))}
          </div>
        )}
      </form>

      {/* نمایش خطای اعتبارسنجی کلاینت */}
      {validationError && (
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900/50 text-xs text-red-600 dark:text-red-400 animate-in fade-in">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{validationError}</span>
        </div>
      )}

      {/* بخش توضیحات تکمیلی و راهنما */}
      <div className="flex items-center justify-center gap-1.5 text-xs text-gray-400 dark:text-zinc-500">
        <Sparkles className="w-3.5 h-3.5 text-amber-500" />
        <span>
          تحلیل ساختار تکنیکال، اسکیماها، پرفورمنس و بهینه‌سازی مخصوص وردپرس
        </span>
      </div>
    </div>
  );
}

export default memo(UrlForm);
