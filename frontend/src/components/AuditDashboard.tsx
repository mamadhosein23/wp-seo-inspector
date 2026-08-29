import React, { useState, useMemo, useId, memo } from "react";
import {
  BadgeCheck,
  XCircle,
  AlertTriangle,
  Info,
  Shuffle,
  ChevronDown,
  ChevronUp,
  Search,
  SlidersHorizontal,
  ArrowUpDown,
  Download,
  Copy,
  Check,
  BarChart3,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { cva } from "class-variance-authority";
import { cn } from "@/lib/utils";

// ----------------------------------------------------
// تعاریف تایپ‌ها (Types & Contracts)
// ----------------------------------------------------
export type CheckStatus = "success" | "warning" | "error" | "info";

export interface CheckItem {
  id?: string;
  label: string;
  category?: string;
  status: CheckStatus;
  value?: string | number | boolean | null;
  message: string;
  recommendation?: string;
  impactScore?: number;
}

export interface AuditResponse {
  score: number;
  checks: CheckItem[];
  meta?: {
    durationMs?: number;
    timestamp?: string;
    targetUrl?: string;
  };
}

interface AuditDashboardProps {
  result: AuditResponse;
  className?: string;
}

type StatusMeta = {
  icon: LucideIcon;
  label: string;
  hex: string;
  bgHex: string;
};

// ----------------------------------------------------
// ثابت‌ها و متادیتاها
// ----------------------------------------------------
const STATUS_META: Record<CheckStatus, StatusMeta> = {
  error: {
    icon: XCircle,
    label: "خطا",
    hex: "#ef4444",
    bgHex: "rgba(239, 68, 68, 0.1)",
  },
  warning: {
    icon: AlertTriangle,
    label: "هشدار",
    hex: "#f59e0b",
    bgHex: "rgba(245, 158, 11, 0.1)",
  },
  info: {
    icon: Info,
    label: "اطلاعات",
    hex: "#3b82f6",
    bgHex: "rgba(59, 130, 246, 0.1)",
  },
  success: {
    icon: BadgeCheck,
    label: "موفق",
    hex: "#10b981",
    bgHex: "rgba(16, 185, 129, 0.1)",
  },
};

const STATUS_SEVERITY_WEIGHT: Record<CheckStatus, number> = {
  error: 1,
  warning: 2,
  info: 3,
  success: 4,
};

const statusChipVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold tracking-wide transition-all select-none",
  {
    variants: {
      status: {
        error:
          "bg-red-500/10 text-red-600 border border-red-500/20 dark:text-red-400 dark:border-red-500/30",
        warning:
          "bg-amber-500/10 text-amber-600 border border-amber-500/20 dark:text-amber-400 dark:border-amber-500/30",
        info: "bg-sky-500/10 text-sky-600 border border-sky-500/20 dark:text-sky-400 dark:border-sky-500/30",
        success:
          "bg-emerald-500/10 text-emerald-600 border border-emerald-500/20 dark:text-emerald-400 dark:border-emerald-500/30",
      },
    },
    defaultVariants: { status: "info" },
  }
);

// ----------------------------------------------------
// کامپوننت گیج امتیاز حلقه‌ای (Score Ring)
// ----------------------------------------------------
const ScoreRing = memo(function ScoreRing({
  score,
  size = 140,
  stroke = 12,
}: {
  score: number;
  size?: number;
  stroke?: number;
}) {
  const gradientId = useId();
  const safeScore = Math.max(0, Math.min(100, Math.round(score)));
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - safeScore / 100);

  const color =
    safeScore >= 90 ? "#10b981" : safeScore >= 65 ? "#f59e0b" : "#ef4444";

  return (
    <div
      className="relative inline-flex items-center justify-center select-none"
      style={{ width: size, height: size }}
      role="progressbar"
      aria-valuenow={safeScore}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={`امتیاز کل: ${safeScore} از ۱۰۰`}
    >
      <svg className="-rotate-90" width={size} height={size} aria-hidden="true">
        <defs>
          <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={color} />
            <stop offset="100%" stopColor={color} stopOpacity={0.4} />
          </linearGradient>
        </defs>

        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={stroke}
          className="fill-none stroke-gray-200 dark:stroke-zinc-800"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={stroke}
          stroke={`url(#${gradientId})`}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          fill="none"
          className="transition-all duration-1000 ease-out"
        />
      </svg>

      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-4xl font-black tracking-tight tabular-nums" style={{ color }}>
          {safeScore}
        </span>
        <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
          از ۱۰۰
        </span>
      </div>
    </div>
  );
});

// ----------------------------------------------------
// کامپوننت کارت خلاصه آمار وضعیت‌ها (Checks Summary)
// ----------------------------------------------------
const ChecksSummary = memo(function ChecksSummary({
  counts,
  selectedFilter,
  onSelectFilter,
}: {
  counts: Record<CheckStatus, number>;
  selectedFilter: CheckStatus | "all";
  onSelectFilter: (status: CheckStatus | "all") => void;
}) {
  const order: CheckStatus[] = ["error", "warning", "info", "success"];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3.5">
      {order.map((key) => {
        const { icon: Icon, label, hex } = STATUS_META[key];
        const isActive = selectedFilter === key;

        return (
          <button
            type="button"
            key={key}
            onClick={() => onSelectFilter(isActive ? "all" : key)}
            className={cn(
              "relative text-start p-4 rounded-xl border transition-all duration-200 cursor-pointer overflow-hidden",
              "bg-white dark:bg-zinc-900",
              isActive
                ? "ring-2 shadow-md border-transparent"
                : "border-gray-200 dark:border-zinc-800 hover:border-gray-300 dark:hover:border-zinc-700"
            )}
            style={{
              ["--ring-color" as string]: hex,
              boxShadow: isActive ? `0 0 0 2px ${hex}` : undefined,
            }}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-gray-500 dark:text-gray-400">
                {label}
              </span>
              <Icon className="w-5 h-5" style={{ color: hex }} />
            </div>

            <div className="mt-3 flex items-baseline gap-1">
              <span className="text-2xl font-black tabular-nums text-gray-900 dark:text-zinc-100">
                {counts[key]}
              </span>
              <span className="text-[11px] text-gray-400">مورد</span>
            </div>

            <div
              className="absolute bottom-0 inset-x-0 h-1"
              style={{ backgroundColor: hex }}
            />
          </button>
        );
      })}
    </div>
  );
});

// ----------------------------------------------------
// کامپوننت تکی هر تست (Check Item Row)
// ----------------------------------------------------
const CheckItemComponent = memo(function CheckItemComponent({
  item,
}: {
  item: CheckItem;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const { icon: Icon, hex, label } = STATUS_META[item.status];

  const handleCopy = async () => {
    try {
      const payload = `[${label}] ${item.label}\nتوضیح: ${item.message}${
        item.recommendation ? `\nتوصیه: ${item.recommendation}` : ""
      }`;
      await navigator.clipboard.writeText(payload);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // نادیده‌گرفتن خطا در محیط‌های فاقد مجوز کلیپ‌بورد
    }
  };

  return (
    <article
      className={cn(
        "rounded-xl border bg-white dark:bg-zinc-900 transition-all duration-200",
        "border-gray-200 dark:border-zinc-800",
        "border-s-[5px]"
      )}
      style={{ borderInlineStartColor: hex }}
    >
      <div className="p-4 sm:p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            <div
              className="p-2 rounded-lg shrink-0"
              style={{ backgroundColor: `${hex}15` }}
            >
              <Icon className="w-5 h-5" style={{ color: hex }} />
            </div>

            <div className="min-w-0">
              <h3 className="font-bold text-gray-900 dark:text-zinc-100 text-sm sm:text-base truncate">
                {item.label}
              </h3>
              {item.category && (
                <span className="text-[11px] text-gray-400 dark:text-gray-500 font-mono">
                  دسته‌بندی: {item.category}
                </span>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2 self-end sm:self-auto shrink-0">
            {item.value !== undefined && item.value !== null && (
              <span className="px-2 py-0.5 rounded bg-gray-100 dark:bg-zinc-800 text-xs font-mono text-gray-600 dark:text-gray-300 max-w-[150px] truncate">
                {String(item.value)}
              </span>
            )}
            <span className={statusChipVariants({ status: item.status })}>
              {label}
            </span>
          </div>
        </div>

        <p className="mt-3 text-sm leading-relaxed text-gray-600 dark:text-zinc-400">
          {item.message}
        </p>

        {item.recommendation && (
          <div className="mt-3">
            <button
              type="button"
              onClick={() => setIsOpen((prev) => !prev)}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline cursor-pointer"
            >
              <span>{isOpen ? "بستن راهکار و جزئیات" : "نمایش راهکار رفع مشکل"}</span>
              {isOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>

            {isOpen && (
              <div className="mt-2.5 p-3.5 rounded-lg bg-indigo-50/60 dark:bg-indigo-950/20 border border-indigo-100 dark:border-indigo-900/40 text-xs leading-relaxed text-indigo-950 dark:text-indigo-200">
                <span className="font-bold block mb-1">اقدام پیشنهادی:</span>
                {item.recommendation}
              </div>
            )}
          </div>
        )}

        <div className="mt-4 pt-3 border-t border-gray-100 dark:border-zinc-800/80 flex items-center justify-between text-[11px] text-gray-400">
          <span className="font-mono">
            {item.id ? `ID: ${item.id}` : "بررسی سیستماتیک"}
          </span>

          <button
            type="button"
            onClick={handleCopy}
            className="inline-flex items-center gap-1 hover:text-gray-700 dark:hover:text-zinc-200 transition-colors cursor-pointer"
            title="کپی لاگ این مورد"
          >
            {copied ? (
              <>
                <Check className="w-3 h-3 text-emerald-500" />
                <span className="text-emerald-500">کپی شد</span>
              </>
            ) : (
              <>
                <Copy className="w-3 h-3" />
                <span>کپی گزارش</span>
              </>
            )}
          </button>
        </div>
      </div>
    </article>
  );
});

// ----------------------------------------------------
// کامپوننت اصلی داشبورد (Audit Dashboard)
// ----------------------------------------------------
export function AuditDashboard({ result, className }: AuditDashboardProps) {
  const [filterStatus, setFilterStatus] = useState<CheckStatus | "all">("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [sortOrder, setSortOrder] = useState<"severity" | "alphabet">("severity");

  // شمارش سریع دسته‌بندی‌ها با یک بار گردش
  const counts = useMemo(() => {
    const accumulator: Record<CheckStatus, number> = {
      error: 0,
      warning: 0,
      info: 0,
      success: 0,
    };

    for (const check of result.checks) {
      if (accumulator[check.status] !== undefined) {
        accumulator[check.status] += 1;
      }
    }

    return accumulator;
  }, [result.checks]);

  // اعمال فیلتر جستجو، فیلتر وضعیت و مرتب‌سازی
  const filteredChecks = useMemo(() => {
    return result.checks
      .filter((check) => {
        const matchesStatus =
          filterStatus === "all" || check.status === filterStatus;
        const matchesSearch =
          searchQuery.trim() === "" ||
          check.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
          check.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
          (check.recommendation &&
            check.recommendation.toLowerCase().includes(searchQuery.toLowerCase()));

        return matchesStatus && matchesSearch;
      })
      .sort((a, b) => {
        if (sortOrder === "severity") {
          return (
            STATUS_SEVERITY_WEIGHT[a.status] - STATUS_SEVERITY_WEIGHT[b.status]
          );
        }
        return a.label.localeCompare(b.label, "fa");
      });
  }, [result.checks, filterStatus, searchQuery, sortOrder]);

  const handleExportJSON = () => {
    const blob = new Blob([JSON.stringify(result, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `audit-report-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!result.checks || result.checks.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center rounded-2xl border border-dashed border-gray-300 dark:border-zinc-800 bg-white/50 dark:bg-zinc-900/50">
        <Shuffle className="w-12 h-12 text-gray-400 dark:text-zinc-600 mb-4 animate-pulse" />
        <h3 className="text-base font-bold text-gray-800 dark:text-zinc-200">
          داده‌ای برای نمایش وجود ندارد
        </h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 max-w-sm">
          هیچ تستی در گزارش دریافتی موجود نیست؛ ورودی ماژول ارزیابی را بررسی کنید.
        </p>
      </div>
    );
  }

  return (
    <section
      dir="rtl"
      className={cn("w-full max-w-5xl mx-auto space-y-6 text-right font-sans", className)}
    >
      {/* هدر بالایی و گیج امتیاز */}
      <div className="relative overflow-hidden p-6 sm:p-8 rounded-2xl border border-gray-200 dark:border-zinc-800 bg-gradient-to-b from-white to-gray-50 dark:from-zinc-900 dark:to-zinc-950 shadow-sm">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="space-y-2 text-center sm:text-right">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-semibold">
              <BarChart3 className="w-3.5 h-3.5" />
              <span>داشبورد جامع ممیزی</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-950 dark:text-white">
              نتایج آنالیز و ممیزی سیستم
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400 max-w-lg leading-relaxed">
              گزارش جامع وضعیت سلامت فنی، اعتبارسنجی مقادیر، و باگ‌های گزارش‌شده به
              تفکیک سطح اولویت.
            </p>
            {result.meta?.targetUrl && (
              <p className="text-xs font-mono text-gray-400 dark:text-zinc-500 pt-1">
                هدف: {result.meta.targetUrl}
              </p>
            )}
          </div>

          <div className="flex flex-col items-center gap-2">
            <ScoreRing score={result.score} />
          </div>
        </div>
      </div>

      {/* بخش کارت‌های آمار چهارگانه */}
      <ChecksSummary
        counts={counts}
        selectedFilter={filterStatus}
        onSelectFilter={setFilterStatus}
      />

      {/* نوار کنترل، جستجو و فیلتر */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 p-2 bg-white dark:bg-zinc-900 rounded-xl border border-gray-200 dark:border-zinc-800">
        <div className="relative flex-1">
          <Search className="absolute inset-y-0 start-3 my-auto w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="جستجو در عنوان، خطاها و توصیه‌ها..."
            className="w-full ps-9 pe-4 py-2 text-sm rounded-lg bg-transparent focus:outline-none focus:ring-1 focus:ring-primary text-gray-900 dark:text-zinc-100 placeholder-gray-400"
          />
        </div>

        <div className="flex items-center gap-2 border-t sm:border-t-0 pt-2 sm:pt-0 border-gray-100 dark:border-zinc-800">
          <div className="flex items-center gap-1.5 px-2 text-xs font-medium text-gray-500">
            <SlidersHorizontal className="w-3.5 h-3.5" />
            <span>مرتب‌سازی:</span>
          </div>

          <button
            type="button"
            onClick={() =>
              setSortOrder((prev) => (prev === "severity" ? "alphabet" : "severity"))
            }
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-200 dark:border-zinc-800 text-xs font-medium hover:bg-gray-50 dark:hover:bg-zinc-800 transition-colors"
          >
            <ArrowUpDown className="w-3.5 h-3.5" />
            <span>{sortOrder === "severity" ? "شدت خطا" : "الفبا"}</span>
          </button>

          <button
            type="button"
            onClick={handleExportJSON}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-900 text-white dark:bg-zinc-100 dark:text-zinc-900 text-xs font-medium hover:opacity-90 transition-opacity"
            title="دانلود کل خروجی JSON"
          >
            <Download className="w-3.5 h-3.5" />
            <span>خروجی</span>
          </button>
        </div>
      </div>

      {/* لیست آیتم‌های بررسی */}
      <div className="space-y-3">
        {filteredChecks.length > 0 ? (
          filteredChecks.map((item, index) => (
            <CheckItemComponent
              key={item.id ?? `${item.status}-${item.label}-${index}`}
              item={item}
            />
          ))
        ) : (
          <div className="p-8 text-center rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-sm text-gray-500">
            هیچ موردی مطابق با فیلتر یا عبارت جستجوی وارد شده پیدا نشد.
          </div>
        )}
      </div>
    </section>
  );
}

export default AuditDashboard;
