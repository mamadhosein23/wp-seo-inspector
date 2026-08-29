// frontend/src/app/page.tsx
"use client";

import { useState } from "react";
import UrlForm from "@/components/UrlForm";
import AuditDashboard from "@/components/AuditDashboard";
import { AuditResponse } from "@/types/audit";
import { AlertCircle, Terminal, Layers, Sparkles, RefreshCcw } from "lucide-react";

export default function Home() {
  const [auditResult, setAuditResult] = useState<AuditResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>("");

  const handleAuditStart = () => {
    setAuditResult(null);
    setIsLoading(true);
    setError("");
  };

  const handleAuditComplete = (result: AuditResponse) => {
    setAuditResult(result);
    setIsLoading(false);
  };

  const handleError = (errorMessage: string) => {
    setError(errorMessage);
    setIsLoading(false);
  };

  return (
    <main className="min-h-screen bg-gradient-to-b from-background via-background to-secondary/20 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-5xl mx-auto space-y-10">
        
        {/* Header & Hero Section */}
        <header className="text-center space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-primary/10 text-primary border border-primary/20">
            <Sparkles className="w-3.5 h-3.5" />
            <span>FastAPI + Next.js Technical Audit Engine</span>
          </div>

          <h1 className="text-4xl sm:text-5xl font-black tracking-tight text-foreground">
            WP SEO <span className="text-primary">Inspector</span>
          </h1>

          <p className="text-lg sm:text-xl text-muted-foreground font-medium max-w-2xl mx-auto">
            تحلیلگر عمیق سئو تکنیکال، ساختار داده و اسکیماهای استاندارد وردپرس
          </p>
        </header>

        {/* Input Form */}
        <section className="relative z-10">
          <UrlForm
            onAuditStart={handleAuditStart}
            onAuditComplete={handleAuditComplete}
            onError={handleError}
          />
        </section>

        {/* Loading Skeleton */}
        {isLoading && (
          <section
            aria-live="polite"
            className="p-8 rounded-2xl border bg-card text-card-foreground shadow-sm max-w-2xl mx-auto text-center space-y-4 animate-pulse"
          >
            <div className="flex justify-center">
              <div className="p-3 bg-primary/10 rounded-full text-primary animate-spin">
                <RefreshCcw className="w-6 h-6" />
              </div>
            </div>
            <div className="space-y-2">
              <p className="text-base font-bold text-foreground">
                در حال اجرای تحلیل جامع و واکشی سورس وردپرس...
              </p>
              <p className="text-xs text-muted-foreground">
                بررسی ربات‌ها، تگ‌های کنونیکال، ریسپانس هدرها، متاتگ‌ها و گراف اسکیما (معمولاً ۵ تا ۱۵ ثانیه)
              </p>
            </div>
            <div className="grid grid-cols-3 gap-3 pt-2">
              <div className="h-10 bg-muted rounded-lg"></div>
              <div className="h-10 bg-muted rounded-lg"></div>
              <div className="h-10 bg-muted rounded-lg"></div>
            </div>
          </section>
        )}

        {/* Error Alert Box */}
        {error && !isLoading && (
          <section
            role="alert"
            className="p-5 rounded-2xl bg-destructive/10 border border-destructive/30 text-destructive max-w-3xl mx-auto shadow-sm"
          >
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
              <div className="space-y-1 text-sm text-start">
                <p className="font-bold">خطا در پردازش و ارتباط با سرور تحلیل:</p>
                <p className="text-muted-foreground whitespace-pre-wrap leading-relaxed">
                  {error}
                </p>
              </div>
            </div>
          </section>
        )}

        {/* Audit Dashboard Output */}
        {auditResult && !isLoading && (
          <section className="pt-4">
            <AuditDashboard result={auditResult} />
          </section>
        )}

        {/* Empty State / Feature Grid */}
        {!auditResult && !isLoading && !error && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-10 border-t border-border/50">
            <div className="p-4 rounded-xl border bg-card/50 text-start space-y-2">
              <div className="p-2 w-fit rounded-lg bg-blue-500/10 text-blue-500">
                <Terminal className="w-4 h-4" />
              </div>
              <h3 className="text-sm font-bold text-foreground">تحلیل سئو تکنیکال</h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                ارزیابی کامل وضعیت کدهای پاسخ، ریدایرکت‌ها، متاتگ‌های ایندکس و تگ‌های کنونیکال.
              </p>
            </div>

            <div className="p-4 rounded-xl border bg-card/50 text-start space-y-2">
              <div className="p-2 w-fit rounded-lg bg-emerald-500/10 text-emerald-500">
                <Layers className="w-4 h-4" />
              </div>
              <h3 className="text-sm font-bold text-foreground">اعتبارسنجی اسکیما (JSON-LD)</h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                بررسی گراف موجودیت‌ها شامل Organization ،Article و BreadcrumbList.
              </p>
            </div>

            <div className="p-4 rounded-xl border bg-card/50 text-start space-y-2">
              <div className="p-2 w-fit rounded-lg bg-amber-500/10 text-amber-500">
                <Sparkles className="w-4 h-4" />
              </div>
              <h3 className="text-sm font-bold text-foreground">بهینه‌سازی اختصاصی WP</h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                شناسایی باگ‌های افزونه‌های Yoast، RankMath و فایل‌های استاتیک بدون کش.
              </p>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
