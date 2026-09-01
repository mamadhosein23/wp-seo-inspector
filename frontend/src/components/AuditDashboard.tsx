"use client";
import React, { useState, useMemo, useId, memo, useEffect, useRef } from "react";
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Info,
  Layers,
  ChevronDown,
  ChevronUp,
  Search,
  SlidersHorizontal,
  ArrowUpDown,
  Download,
  Copy,
  Check,
  BarChart3,
  Clock,
  ExternalLink,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { cva } from "class-variance-authority";
import { cn } from "@/lib/utils";
import type { AuditReport, CheckResult, CheckStatus, CheckCategory } from "@/types/audit";

interface AuditDashboardProps {
  result: AuditReport;
  className?: string;
}

interface StatusMeta {
  icon: LucideIcon;
  label: string;
  badgeClass: string;
  borderClass: string;
  textClass: string;
}

const STATUS_CONFIG: Record<CheckStatus, StatusMeta> = {
  fail: {
    icon: XCircle,
    label: "بحرانی",
    badgeClass: "bg-destructive/10 text-destructive border-destructive/20",
    borderClass: "border-s-destructive",
    textClass: "text-destructive",
  },
  warning: {
    icon: AlertTriangle,
    label: "هشدار",
    badgeClass: "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20",
    borderClass: "border-s-amber-500",
    textClass: "text-amber-500",
  },
  info: {
    icon: Info,
    label: "سیگنال",
    badgeClass: "bg-sky-500/10 text-sky-600 dark:text-sky-400 border-sky-500/20",
    borderClass: "border-s-sky-500",
    textClass: "text-sky-500",
  },
  pass: {
    icon: CheckCircle2,
    label: "پاس‌شده",
    badgeClass: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20",
    borderClass: "border-s-emerald-500",
    textClass: "text-emerald-500",
  },
};

const CATEGORY_LABELS: Record<CheckCategory, string> = {
  indexability: "قابلیت ایندکس",
  security: "امنیت فنی",
  performance: "عملکرد",
  content: "ساختار محتوا",
  structure: "داده‌های ساختاریافته",
};

const STATUS_SEVERITY_ORDER: Record<CheckStatus, number> = {
  fail: 1,
  warning: 2,
  info: 3,
  pass: 4,
};

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold select-none border transition-colors",
  {
    variants: {
      status: {
        fail: "bg-destructive/10 text-destructive border-destructive/20",
        warning: "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20",
        info: "bg-sky-500/10 text-sky-600 dark:text-sky-400 border-sky-500/20",
        pass: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20",
      },
    },
    defaultVariants: { status: "info" },
  }
);

// گیج امتیاز حلقه‌ای داینامیک
const ScoreGauge = memo(function ScoreGauge({ score }: { score: number }) {
  const gradientId = useId();
  const safeScore = useMemo(() => Math.max(0, Math.min(100, Math.round(score))), [score]);
  const size = 130;
  const strokeWidth = 10;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - safeScore / 100);

  const strokeColor = useMemo(() => {
    if (safeScore >= 85) return "hsl(var(--success, 142 71% 45%))";
    if (safeScore >= 50) return "hsl(var(--warning, 38 92% 50%))";
    return "hsl(var(--destructive, 0 84% 60%))";
  }, [safeScore]);

  return (
    <div
      className="relative inline-flex items-center justify-center select-none"
      role="progressbar"
      aria-valuenow={safeScore}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={`امتیاز کل سلامت سئو: ${safeScore} از ۱۰۰`}
    >
      <svg className="-rotate-90" width={size} height={size} aria-hidden="true">
        <defs>
          <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={strokeColor} />
            <stop offset="100%" stopColor={strokeColor} stopOpacity={0.6} />
          </linearGradient>
        </defs>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={strokeWidth}
          className="fill-none stroke-muted"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={strokeWidth}
          stroke={`url(#${gradientId})`}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          fill="none"
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-black tracking-tight tabular-nums text-foreground">
          {safeScore}
        </span>
        <span className="text-[11px] font-medium text-muted-foreground">از ۱۰۰</span>
      </div>
    </div>
  );
});

// کامپوننت کارت‌های خلاصه وضعیت
const SummaryMetrics = memo(function SummaryMetrics({
  counts,
  activeFilter,
  onSelectFilter,
}: {
  counts: Record<CheckStatus, number>;
  activeFilter: CheckStatus | "all";
  onSelectFilter: (status: CheckStatus | "all") => void;
}) {
  const order: CheckStatus[] = ["fail", "warning", "info", "pass"];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {order.map((status) => {
        const { icon: Icon, label, textClass } = STATUS_CONFIG[status];
        const isActive = activeFilter === status;

        return (
          <button
            type="button"
            key={status}
            onClick={() => onSelectFilter(isActive ? "all" : status)}
            className={cn(
              "p-4 rounded-xl border transition-all duration-200 text-start bg-card shadow-sm cursor-pointer",
              isActive
                ? "ring-2 ring-primary border-transparent shadow-md"
                : "border-border hover:border-border/80"
            )}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-muted-foreground">{label}</span>
              <Icon className={cn("size-4", textClass)} />
            </div>
            <div className="mt-2 flex items-baseline gap-1">
              <span className="text-2xl font-black tabular-nums text-foreground">
                {counts[status]}
              </span>
              <span className="text-[11px] text-muted-foreground">مورد</span>
            </div>
          </button>
        );
      })}
    </div>
  );
});

// کامپوننت سطر ممیزی
const CheckRow = memo(function CheckRow({ check }: { check: CheckResult }) {
  const [isOpen, setIsOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const contentId = useId();

  const meta = STATUS_CONFIG[check.status];
  const Icon = meta.icon;

  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  const handleCopy = async () => {
    try {
      const content = `[${meta.label}] ${check.name}\nدسته: ${
        CATEGORY_LABELS[check.category] || check.category
      }\nپیام: ${check.message}${
        check.recommendation ? `\nتوصیه فنی: ${check.recommendation}` : ""
      }`;
      await navigator.clipboard.writeText(content);
      setCopied(true);
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      timeoutRef.current = setTimeout(() => setCopied(false), 2000);
    } catch {
      // نادیده‌گرفتن خطای فاقد دسترسی کلیپ‌بورد
    }
  };

  return (
    <article
      className={cn(
        "rounded-xl border bg-card text-card-foreground shadow-sm transition-all duration-200 border-s-[5px]",
        meta.borderClass
      )}
    >
      <div className="p-4 sm:p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            <div className="p-2 rounded-lg bg-muted/60 shrink-0">
              <Icon className={cn("size-5", meta.textClass)} />
            </div>
            <div className="min-w-0">
              <h3 className="font-bold text-sm sm:text-base text-foreground truncate">
                {check.name}
              </h3>
              <span className="text-xs text-muted-foreground">
                دسته: {CATEGORY_LABELS[check.category] || check.category}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2 self-end sm:self-auto shrink-0">
            {check.score_impact > 0 && (
              <span className="px-2 py-0.5 rounded bg-muted text-xs font-mono font-medium text-foreground">
                -{check.score_impact} نمره
              </span>
            )}
            <span className={badgeVariants({ status: check.status })}>
              {meta.label}
            </span>
          </div>
        </div>

        <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
          {check.message}
        </p>

        {check.recommendation && (
          <div className="mt-3">
            <button
              type="button"
              aria-expanded={isOpen}
              aria-controls={contentId}
              onClick={() => setIsOpen((prev) => !prev)}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-primary hover:underline cursor-pointer"
            >
              <span>{isOpen ? "بستن راهکار" : "نمایش دستورالعمل بهینه‌سازی"}</span>
              {isOpen ? <ChevronUp className="size-3.5" /> : <ChevronDown className="size-3.5" />}
            </button>

            {isOpen && (
              <div
                id={contentId}
                className="mt-2.5 p-3.5 rounded-lg bg-secondary/50 border border-border text-xs leading-relaxed text-foreground"
              >
                <span className="font-bold block mb-1">اقدام پیشنهادی:</span>
                {check.recommendation}
              </div>
            )}
          </div>
        )}

        <div className="mt-4 pt-3 border-t border-border flex items-center justify-between text-[11px] text-muted-foreground">
          <span className="font-mono text-muted-foreground/80">شناسه: {check.id}</span>
          <button
            type="button"
            onClick={handleCopy}
            className="inline-flex items-center gap-1 hover:text-foreground transition-colors cursor-pointer"
          >
            {copied ? (
              <>
                <Check className="size-3 text-emerald-500" />
                <span className="text-emerald-500">کپی شد</span>
              </>
            ) : (
              <>
                <Copy className="size-3" />
                <span>کپی گزارش</span>
              </>
            )}
          </button>
        </div>
      </div>
    </article>
  );
});

export function AuditDashboard({ result, className }: AuditDashboardProps) {
  const [filterStatus, setFilterStatus] = useState<CheckStatus | "all">("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [sortOrder, setSortOrder] = useState<"severity" | "alphabet">("severity");

  const counts = useMemo(() => {
    const acc: Record<CheckStatus, number> = { fail: 0, warning: 0, info: 0, pass: 0 };
    if (!result?.checks) return acc;
    for (const c of result.checks) {
      if (acc[c.status] !== undefined) acc[c.status] += 1;
    }
    return acc;
  }, [result?.checks]);

  const filteredChecks = useMemo(() => {
    if (!result?.checks) return [];
    return result.checks
      .filter((check) => {
        const matchesStatus = filterStatus === "all" || check.status === filterStatus;
        const query = searchQuery.trim().toLowerCase();
        const matchesSearch =
          query === "" ||
          check.name.toLowerCase().includes(query) ||
          check.message.toLowerCase().includes(query) ||
          Boolean(check.recommendation && check.recommendation.toLowerCase().includes(query));

        return matchesStatus && matchesSearch;
      })
      .sort((a, b) => {
        if (sortOrder === "severity") {
          return STATUS_SEVERITY_ORDER[a.status] - STATUS_SEVERITY_ORDER[b.status];
        }
        return a.name.localeCompare(b.name, "fa");
      });
  }, [result?.checks, filterStatus, searchQuery, sortOrder]);

  const handleExportJSON = () => {
    const blob = new Blob([JSON.stringify(result, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `audit-report-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  if (!result?.checks || result.checks.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center rounded-2xl border border-dashed border-border bg-card">
        <Layers className="size-12 text-muted-foreground/50 mb-4 animate-pulse" />
        <h3 className="text-base font-bold text-foreground">داده‌ای برای نمایش وجود ندارد</h3>
        <p className="text-sm text-muted-foreground mt-1">هیچ آزمونی در خروجی پاسخ یافت نشد.</p>
      </div>
    );
  }

  return (
    <section dir="rtl" className={cn("w-full max-w-5xl mx-auto space-y-6 text-start", className)}>
      {/* هدر بالایی و متادیتاها */}
      <div className="p-6 sm:p-8 rounded-2xl border border-border bg-card text-card-foreground shadow-sm">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="space-y-3 w-full sm:w-auto">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-semibold">
              <BarChart3 className="size-3.5" />
              <span>نتیجه ارزیابی سلامت تکنیکال</span>
            </div>

            <div className="space-y-1">
              <h1 className="text-2xl font-black text-foreground">گزارش ممیزی سورس</h1>
              <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground pt-1">
                <span className="flex items-center gap-1 font-mono" dir="ltr">
                  <ExternalLink className="size-3" />
                  {result.url}
                </span>
                <span>•</span>
                <span className="flex items-center gap-1">
                  <Clock className="size-3" />
                  {result.execution_time_ms} میلی‌ثانیه
                </span>
                <span>•</span>
                <span>کد وضعیت HTTP: {result.status_code}</span>
              </div>
            </div>
          </div>

          <div className="shrink-0">
            <ScoreGauge score={result.final_score} />
          </div>
        </div>
      </div>

      {/* خلاصه وضعیت */}
      <SummaryMetrics
        counts={counts}
        activeFilter={filterStatus}
        onSelectFilter={setFilterStatus}
      />

      {/* ابزارهای فیلتر و جستجو */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 p-2 bg-card rounded-xl border border-border">
        <div className="relative flex-1">
          <Search className="absolute inset-y-0 start-3 my-auto size-4 text-muted-foreground" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="جستجو در آزمون‌ها، خطاها و توصیه‌ها..."
            className="w-full ps-9 pe-4 py-2 text-sm rounded-lg bg-transparent border-0 focus:outline-none focus:ring-1 focus:ring-ring text-foreground placeholder:text-muted-foreground"
          />
        </div>

        <div className="flex items-center gap-2 border-t sm:border-t-0 pt-2 sm:pt-0 border-border">
          <div className="flex items-center gap-1.5 px-2 text-xs font-medium text-muted-foreground">
            <SlidersHorizontal className="size-3.5" />
            <span>مرتب‌سازی:</span>
          </div>

          <button
            type="button"
            onClick={() =>
              setSortOrder((prev) => (prev === "severity" ? "alphabet" : "severity"))
            }
            className="inline-flex items-center justify-center gap-1.5 py-1.5 px-3 text-xs font-medium rounded-lg border border-input bg-background hover:bg-accent hover:text-accent-foreground transition-colors cursor-pointer"
          >
            <ArrowUpDown className="size-3.5" />
            <span>{sortOrder === "severity" ? "شدت خطا" : "الفبا"}</span>
          </button>

          <button
            type="button"
            onClick={handleExportJSON}
            className="inline-flex items-center justify-center gap-1.5 py-1.5 px-3 text-xs font-medium rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors shadow-xs cursor-pointer"
            title="دانلود کل خروجی JSON"
          >
            <Download className="size-3.5" />
            <span>خروجی</span>
          </button>
        </div>
      </div>

      {/* لیست تست‌ها */}
      <div className="space-y-3">
        {filteredChecks.length > 0 ? (
          filteredChecks.map((check) => <CheckRow key={check.id} check={check} />)
        ) : (
          <div className="p-8 text-center rounded-xl border border-border bg-card text-sm text-muted-foreground">
            هیچ آزمونی مطابق با فیلتر یا عبارت جستجوی وارد شده پیدا نشد.
          </div>
        )}
      </div>
    </section>
  );
}

export default AuditDashboard;
