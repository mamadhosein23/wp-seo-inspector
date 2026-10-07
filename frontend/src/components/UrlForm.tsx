"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { Loader2, Search, History, AlertCircle, Globe } from "lucide-react";
import type { AuditResponse } from "@/types/audit";

interface UrlFormProps {
  onAuditStart: () => void;
  onAuditComplete: (result: AuditResponse) => void;
  onError: (message: string) => void;
}

const STORAGE_KEY = "recent_audit_urls";
const MAX_HISTORY = 5;

function isValidUrl(urlString: string): boolean {
  try {
    const parsed = new URL(urlString);
    return parsed.protocol === "http:" || parsed.protocol === "https:";
  } catch {
    return false;
  }
}

export default function UrlForm({
  onAuditStart,
  onAuditComplete,
  onError,
}: UrlFormProps) {
  const [url, setUrl] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [recentUrls, setRecentUrls] = useState<string[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);

  // لود تاریخچه از لوکال استوریج با حفاظت SSR
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed)) {
          setRecentUrls(
            parsed.filter((item): item is string => typeof item === "string")
          );
        }
      }
    } catch {
      // حالت‌های پرایوت یا دسترسی مسدود
    }
  }, []);

  // بستن لیست تاریخچه هنگام کلیک خارج از المان
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setShowHistory(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const saveToHistory = useCallback((newUrl: string) => {
    setRecentUrls((prev) => {
      const filtered = prev.filter((item) => item !== newUrl);
      const updated = [newUrl, ...filtered].slice(0, MAX_HISTORY);
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      } catch {
        // جلوگیری از کرش در پرایوت سافاری
      }
      return updated;
    });
  }, []);

  const runAudit = async (targetUrl: string) => {
    let cleanUrl = targetUrl.trim();
    if (!cleanUrl) return;

    if (!cleanUrl.startsWith("http://") && !cleanUrl.startsWith("https://")) {
      cleanUrl = `https://${cleanUrl}`;
    }

    if (!isValidUrl(cleanUrl)) {
      setLocalError("نشانی وارد شده معتبر نیست. لطفاً یک URL با ساختار صحیح وارد کنید.");
      return;
    }

    setLocalError(null);
    setIsLoading(true);
    setShowHistory(false);
    onAuditStart();

    try {
      // فراخوانی اندپوینت FastAPI
      const res = await fetch("/api/audit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: cleanUrl }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data?.detail || "خطا در واکشی اطلاعات از سرور.");
      }

      saveToHistory(cleanUrl);
      onAuditComplete(data);
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "خطای نامشخصی در اتصال رخ داد.";
      onError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    runAudit(url);
  };

  return (
    <div ref={containerRef} className="relative w-full max-w-3xl mx-auto">
      <form onSubmit={handleSubmit} className="relative flex items-center">
        <div className="relative w-full">
          <div className="pointer-events-none absolute inset-y-0 start-4 flex items-center text-muted-foreground">
            <Globe className="size-5" />
          </div>

          <input
            type="text"
            dir="ltr"
            value={url}
            disabled={isLoading}
            onFocus={() => recentUrls.length > 0 && setShowHistory(true)}
            onChange={(e) => {
              setUrl(e.target.value);
              if (localError) setLocalError(null);
            }}
            placeholder="https://example.com"
            className="w-full rounded-2xl border border-border bg-card/80 py-4 pe-32 ps-12 text-sm text-foreground shadow-sm backdrop-blur-md transition-all placeholder:text-muted-foreground/60 focus:border-primary focus:outline-none focus:ring-4 focus:ring-primary/10 disabled:opacity-50"
          />

          <button
            type="submit"
            disabled={isLoading || !url.trim()}
            className="absolute end-2 inset-y-2 flex items-center justify-center gap-2 rounded-xl bg-primary px-5 text-sm font-semibold text-primary-foreground shadow-sm transition-all hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 cursor-pointer"
          >
            {isLoading ? (
              <>
                <Loader2 className="size-4 animate-spin" />
                <span>در حال تحلیل...</span>
              </>
            ) : (
              <>
                <Search className="size-4" />
                <span>شروع ممیزی</span>
              </>
            )}
          </button>
        </div>
      </form>

      {/* خطای کلاینت‌ساید فرم */}
      {localError && (
        <div className="mt-2 flex items-center gap-2 text-xs text-destructive">
          <AlertCircle className="size-3.5 shrink-0" />
          <span>{localError}</span>
        </div>
      )}

      {/* منوی بازشوی تاریخچه */}
      {showHistory && recentUrls.length > 0 && (
        <div className="absolute z-50 mt-2 w-full overflow-hidden rounded-xl border border-border bg-card shadow-lg backdrop-blur-xl">
          <div className="flex items-center justify-between border-b border-border/60 px-4 py-2 text-xs font-semibold text-muted-foreground">
            <span className="flex items-center gap-1.5">
              <History className="size-3.5" />
              نشانی‌های اخیر
            </span>
            <button
              type="button"
              onClick={() => {
                setRecentUrls([]);
                localStorage.removeItem(STORAGE_KEY);
                setShowHistory(false);
              }}
              className="text-[11px] text-muted-foreground hover:text-destructive transition-colors cursor-pointer"
            >
              پاک کردن تاریخچه
            </button>
          </div>
          <ul className="divide-y divide-border/40">
            {recentUrls.map((item) => (
              <li key={item}>
                <button
                  type="button"
                  dir="ltr"
                  onClick={() => {
                    setUrl(item);
                    setShowHistory(false);
                    runAudit(item);
                  }}
                  className="w-full px-4 py-2.5 text-start font-mono text-xs text-foreground transition-colors hover:bg-muted/50 truncate cursor-pointer"
                >
                  {item}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
