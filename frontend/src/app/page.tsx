"use client";

import { useState } from "react";
import {
  AlertCircle,
  Layers,
  RefreshCcw,
  Sparkles,
  Terminal,
} from "lucide-react";
"use client";

import { useState, useCallback } from "react";
import {
  AlertCircle,
  Layers,
  RefreshCcw,
  Sparkles,
  Terminal,
} from "lucide-react";

import AuditDashboard from "@/components/AuditDashboard";
import UrlForm from "@/components/UrlForm";
import type { AuditResponse } from "@/types/audit";

interface AuditState {
  status: "idle" | "loading" | "success" | "error";
  data: AuditResponse | null;
  error: string | null;
}

export default function Home() {
  const [state, setState] = useState<AuditState>({
    status: "idle",
    data: null,
    error: null,
  });

  const handleAuditStart = useCallback(() => {
    setState({ status: "loading", data: null, error: null });
  }, []);

  const handleAuditComplete = useCallback((result: AuditResponse) => {
    setState({ status: "success", data: result, error: null });
  }, []);

  const handleError = useCallback((message: string) => {
    setState({ status: "error", data: null, error: message });
  }, []);

  const isLoading = state.status === "loading";
  const isError = state.status === "error";
  const isSuccess = state.status === "success" && state.data !== null;
  const isIdle = state.status === "idle";

  return (
    <main
      dir="rtl"
      className="min-h-screen bg-gradient-to-b from-background via-background to-secondary/20 px-4 py-12 sm:px-6 lg:px-8"
    >
      <div className="mx-auto max-w-5xl space-y-10">
        {/* Header */}
        <header className="space-y-4 text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
            <Sparkles aria-hidden="true" className="size-3.5" />
            <span dir="ltr">FastAPI + Next.js Technical Audit Engine</span>
          </div>

          <h1 className="text-4xl font-black tracking-tight text-foreground sm:text-5xl">
            <span dir="ltr">
              WP SEO <span className="text-primary">Inspector</span>
            </span>
          </h1>

          <p className="mx-auto max-w-2xl text-lg font-medium text-muted-foreground sm:text-xl">
            تحلیل عمیق سئوی تکنیکال، ساختار داده و اسکیماهای استاندارد وردپرس
          </p>
        </header>

        {/* Input Form */}
        <section aria-label="فرم شروع تحلیل" className="relative z-10">
          <UrlForm
            onAuditStart={handleAuditStart}
            onAuditComplete={handleAuditComplete}
            onError={handleError}
          />
        </section>

        {/* Dynamic Status / Alerts */}
        <div aria-atomic="true" aria-live="polite">
          {isLoading && (
            <section
              aria-busy="true"
              aria-label="تحلیل در حال اجرا"
              className="mx-auto max-w-2xl space-y-4 rounded-2xl border bg-card p-8 text-center text-card-foreground shadow-sm"
            >
              <div className="flex justify-center">
                <div className="rounded-full bg-primary/10 p-3 text-primary">
                  <RefreshCcw
                    aria-hidden="true"
                    className="size-6 animate-spin motion-reduce:animate-none"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <p className="text-base font-bold text-foreground">
                  در حال واکشی صفحه و اجرای تحلیل جامع...
                </p>
                <p className="text-xs leading-relaxed text-muted-foreground">
                  بررسی وضعیت HTTP، متاتگ‌ها، هدینگ‌ها، کنونیکال، تصاویر،
                  لینک‌ها و داده‌های ساختاریافته؛ معمولاً ۵ تا ۱۵ ثانیه
                </p>
              </div>

              <div
                aria-hidden="true"
                className="grid grid-cols-3 gap-3 pt-2"
              >
                <div className="h-10 animate-pulse rounded-lg bg-muted motion-reduce:animate-none" />
                <div className="h-10 animate-pulse rounded-lg bg-muted motion-reduce:animate-none" />
                <div className="h-10 animate-pulse rounded-lg bg-muted motion-reduce:animate-none" />
              </div>
            </section>
          )}

          {isError && (
            <section
              role="alert"
              className="mx-auto max-w-3xl rounded-2xl border border-destructive/30 bg-destructive/10 p-5 shadow-sm"
            >
              <div className="flex items-start gap-3">
                <AlertCircle
                  aria-hidden="true"
                  className="mt-0.5 size-5 shrink-0 text-destructive"
                />

                <div className="space-y-1 text-start text-sm">
                  <p className="font-bold text-destructive">
                    خطا در اجرای تحلیل
                  </p>
                  <p className="whitespace-pre-wrap break-words leading-relaxed text-foreground">
                    {state.error}
                  </p>
                </div>
              </div>
            </section>
          )}
        </div>

        {/* Results */}
        {isSuccess && state.data && (
          <section aria-label="نتیجه تحلیل سئو" className="pt-4">
            <AuditDashboard result={state.data} />
          </section>
        )}

        {/* Feature Cards (Only on Idle) */}
        {isIdle && (
          <section
            aria-label="قابلیت‌های سامانه"
            className="grid grid-cols-1 gap-4 border-t border-border/50 pt-10 md:grid-cols-3"
          >
            <article className="space-y-2 rounded-xl border bg-card/50 p-4 text-start">
              <div className="w-fit rounded-lg bg-info/10 p-2 text-info">
                <Terminal aria-hidden="true" className="size-4" />
              </div>
              <h2 className="text-sm font-bold text-foreground">
                تحلیل سئوی تکنیکال
              </h2>
              <p className="text-xs leading-relaxed text-muted-foreground">
                ارزیابی وضعیت HTTP، ریدایرکت‌ها، متاتگ‌های ایندکس و تگ
                کنونیکال.
              </p>
            </article>

            <article className="space-y-2 rounded-xl border bg-card/50 p-4 text-start">
              <div className="w-fit rounded-lg bg-success/10 p-2 text-success">
                <Layers aria-hidden="true" className="size-4" />
              </div>
              <h2 className="text-sm font-bold text-foreground">
                بررسی داده‌های ساختاریافته
              </h2>
              <p className="text-xs leading-relaxed text-muted-foreground">
                شناسایی JSON-LD و انواعی مانند Organization، Article و
                BreadcrumbList.
              </p>
            </article>

            <article className="space-y-2 rounded-xl border bg-card/50 p-4 text-start">
              <div className="w-fit rounded-lg bg-warning/10 p-2 text-warning">
                <Sparkles aria-hidden="true" className="size-4" />
              </div>
              <h2 className="text-sm font-bold text-foreground">
                تشخیص وردپرس
              </h2>
              <p className="text-xs leading-relaxed text-muted-foreground">
                تشخیص نشانه‌های وردپرس و گزارش سیگنال‌های فنی قابل استخراج از
                صفحه.
              </p>
            </article>
          </section>
        )}
      </div>
    </main>
  );
}

import AuditDashboard from "@/components/AuditDashboard";
import UrlForm from "@/components/UrlForm";
import type { AuditResponse } from "@/types/audit";

export default function Home() {
  const [auditResult, setAuditResult] = useState<AuditResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAuditStart = () => {
    setAuditResult(null);
    setError(null);
    setIsLoading(true);
  };

  const handleAuditComplete = (result: AuditResponse) => {
    setAuditResult(result);
    setError(null);
    setIsLoading(false);
  };

  const handleError = (message: string) => {
    setAuditResult(null);
    setError(message);
    setIsLoading(false);
  };

  return (
    <main
      dir="rtl"
      className="min-h-screen bg-gradient-to-b from-background via-background to-secondary/20 px-4 py-12 sm:px-6 lg:px-8"
    >
      <div className="mx-auto max-w-5xl space-y-10">
        <header className="space-y-4 text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
            <Sparkles aria-hidden="true" className="size-3.5" />
            <span dir="ltr">FastAPI + Next.js Technical Audit Engine</span>
          </div>

          <h1 className="text-4xl font-black tracking-tight text-foreground sm:text-5xl">
            <span dir="ltr">
              WP SEO <span className="text-primary">Inspector</span>
            </span>
          </h1>

          <p className="mx-auto max-w-2xl text-lg font-medium text-muted-foreground sm:text-xl">
            تحلیل عمیق سئوی تکنیکال، ساختار داده و اسکیماهای استاندارد وردپرس
          </p>
        </header>

        <section aria-label="فرم شروع تحلیل" className="relative z-10">
          <UrlForm
            onAuditStart={handleAuditStart}
            onAuditComplete={handleAuditComplete}
            onError={handleError}
          />
        </section>

        <div aria-atomic="true" aria-live="polite">
          {isLoading && (
            <section
              aria-busy="true"
              aria-label="تحلیل در حال اجرا"
              className="mx-auto max-w-2xl space-y-4 rounded-2xl border bg-card p-8 text-center text-card-foreground shadow-sm"
            >
              <div className="flex justify-center">
                <div className="rounded-full bg-primary/10 p-3 text-primary">
                  <RefreshCcw
                    aria-hidden="true"
                    className="size-6 animate-spin motion-reduce:animate-none"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <p className="text-base font-bold text-foreground">
                  در حال واکشی صفحه و اجرای تحلیل جامع...
                </p>
                <p className="text-xs leading-relaxed text-muted-foreground">
                  بررسی وضعیت HTTP، متاتگ‌ها، هدینگ‌ها، کنونیکال، تصاویر،
                  لینک‌ها و داده‌های ساختاریافته؛ معمولاً ۵ تا ۱۵ ثانیه
                </p>
              </div>

              <div
                aria-hidden="true"
                className="grid grid-cols-3 gap-3 pt-2"
              >
                <div className="h-10 animate-pulse rounded-lg bg-muted motion-reduce:animate-none" />
                <div className="h-10 animate-pulse rounded-lg bg-muted motion-reduce:animate-none" />
                <div className="h-10 animate-pulse rounded-lg bg-muted motion-reduce:animate-none" />
              </div>
            </section>
          )}

          {error && !isLoading && (
            <section
              role="alert"
              className="mx-auto max-w-3xl rounded-2xl border border-destructive/30 bg-destructive/10 p-5 shadow-sm"
            >
              <div className="flex items-start gap-3">
                <AlertCircle
                  aria-hidden="true"
                  className="mt-0.5 size-5 shrink-0 text-destructive"
                />

                <div className="space-y-1 text-start text-sm">
                  <p className="font-bold text-destructive">
                    خطا در اجرای تحلیل
                  </p>
                  <p className="whitespace-pre-wrap break-words leading-relaxed text-foreground">
                    {error}
                  </p>
                </div>
              </div>
            </section>
          )}
        </div>

        {auditResult && !isLoading && (
          <section aria-label="نتیجه تحلیل سئو" className="pt-4">
            <AuditDashboard result={auditResult} />
          </section>
        )}

        {!auditResult && !isLoading && !error && (
          <section
            aria-label="قابلیت‌های سامانه"
            className="grid grid-cols-1 gap-4 border-t border-border/50 pt-10 md:grid-cols-3"
          >
            <article className="space-y-2 rounded-xl border bg-card/50 p-4 text-start">
              <div className="w-fit rounded-lg bg-blue-500/10 p-2 text-blue-500">
                <Terminal aria-hidden="true" className="size-4" />
              </div>
              <h2 className="text-sm font-bold text-foreground">
                تحلیل سئوی تکنیکال
              </h2>
              <p className="text-xs leading-relaxed text-muted-foreground">
                ارزیابی وضعیت HTTP، ریدایرکت‌ها، متاتگ‌های ایندکس و تگ
                کنونیکال.
              </p>
            </article>

            <article className="space-y-2 rounded-xl border bg-card/50 p-4 text-start">
              <div className="w-fit rounded-lg bg-emerald-500/10 p-2 text-emerald-500">
                <Layers aria-hidden="true" className="size-4" />
              </div>
              <h2 className="text-sm font-bold text-foreground">
                بررسی داده‌های ساختاریافته
              </h2>
              <p className="text-xs leading-relaxed text-muted-foreground">
                شناسایی JSON-LD و انواعی مانند Organization، Article و
                BreadcrumbList.
              </p>
            </article>

            <article className="space-y-2 rounded-xl border bg-card/50 p-4 text-start">
              <div className="w-fit rounded-lg bg-amber-500/10 p-2 text-amber-500">
                <Sparkles aria-hidden="true" className="size-4" />
              </div>
              <h2 className="text-sm font-bold text-foreground">
                تشخیص وردپرس
              </h2>
              <p className="text-xs leading-relaxed text-muted-foreground">
                تشخیص نشانه‌های وردپرس و گزارش سیگنال‌های فنی قابل استخراج از
                صفحه.
              </p>
            </article>
          </section>
        )}
      </div>
    </main>
  );
}
