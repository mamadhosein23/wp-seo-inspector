import React, { memo, useId, useMemo } from
import { AuditResponse, CheckItem, CheckStatus } from "@/types/audit";
import {
  BadgeCheck,
  XCircle,
  AlertTriangle,
  Info,
  Shuffle,
  ChevronDown,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { cva } from "class-variance-authority";
import { cn } from "@/lib/utils";

interface AuditDashboardProps {
  result: AuditResponse;
}

// ----------------------------------------------------
// تایپ‌ها و نگاشت وضعیت
// ----------------------------------------------------
type StatusMeta = { icon: LucideIcon; label: string; hex: string };

const STATUS_META: Record<CheckStatus, StatusMeta> = {
  success: { icon: BadgeCheck, label: "موفق", hex: "#10b981" },
  warning: { icon: AlertTriangle, label: "هشدار", hex: "#f59e0b" },
  error: { icon: XCircle, label: "خطا", hex: "#ef4444" },
  info: { icon: Info, label: "اطلاعات", hex: "#3b82f6" },
};

const STATUS_ORDER: Record<CheckStatus, number> = {
  error: 1,
  warning: 2,
  info: 3,
  success: 4,
};

// ----------------------------------------------------
// Badge وضعیت
// ----------------------------------------------------
const statusChip = cva(
  "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium transition-colors",
  {
    variants: {
      status: {
        error: "bg-red-50 text-red-700 dark:bg-red-500/15 dark:text-red-400",
        warning: "bg-amber-50 text-amber-700 dark:bg-amber-500/15 dark:text-amber-400",
        success:
          "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-400",
        info: "bg-sky-50 text-sky-700 dark:bg-sky-500/15 dark:text-sky-400",
      },
    },
    defaultVariants: { status: "info" },
  }
);

// ----------------------------------------------------
// رینگ امتیاز
// ----------------------------------------------------
const ScoreRing: React.FC<{ score: number; size?: number; stroke?: number }> = ({
  score,
  size = 140,
  stroke = 12,
}) => {
  const gradientId = useId();

  const safeScore = Math.max(0, Math.min(100, score));
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - safeScore / 100);

  const color =
    safeScore >= 90 ? "#10b981" : safeScore >= 70 ? "#f59e0b" : "#ef4444";

  return (
    <div
      className="relative inline-flex items-center justify-center"
      style={{ width: size, height: size }}
    >
      <svg className="-rotate-90" width={size} height={size} aria-hidden="true">
        <defs>
          <linearGradient id={gradientId}>
            <stop offset="0%" stopColor={color} />
            <stop offset="100%" stopColor={color} stopOpacity={0.55} />
          </linearGradient>
        </defs>

        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={stroke}
          className="fill-none stroke-white/10 dark:stroke-white/10"
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
          style={{ transition: "stroke-dashoffset 700ms ease" }}
        />
      </svg>

      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-4xl font-extrabold tabular-nums" style={{ color }}>
          {safeScore}
        </span>
        <span className="text-xs text-gray-500 dark:text-gray-400">از ۱۰۰</span>
      </div>
    </div>
  );
};

// ----------------------------------------------------
// خلاصه بررسی‌ها
// ----------------------------------------------------
const ChecksSummary: React.FC<{ checks: CheckItem[] }> = ({ checks }) => {
  const counts = useMemo(() => {
    const initial = {
      error: 0,
      warning: 0,
      info: 0,
      success: 0,
   [check Record<CheckStatus, number>;

    for (const check of checks) {
      initial[check.status] += 1;
    }

    return initial;
  }, [checks]);

  return (
    <div className="cv-grid grid grid-cols-2 lg:grid-cols-4 gap-4">
      {(Object.keys(STATUS_ORDER) as CheckStatus[]).map((key) => {
        const { icon: Icon, label, hex } = STATUS_META[key];

        return (
          <div
            key={key}
            className="card-base p-4 text-center border-l-4 transition-transform hover:-translate-y-0.5"
            style={{ borderLeftColor: hex }}
          >
            <Icon className="w-6 h-6 mx-auto mb-1.5" style={{ color: hex }} />
            <div className="text-3xl font-bold tabular-nums">{counts[key]}</div>
            <div className="text-sm text-gray-500 dark:text-gray-400">{label}</div>
          </div>
        );
      })}
    </div>
  );
};

// ----------------------------------------------------
// آیتم بررسی
// ----------------------------------------------------
const CheckItemComponent = memo(function CheckItemComponent({
  item,
}: {
  item: CheckItem;
}) {
  const { icon: Icon, hex, label } = STATUS_META[item.status];

  return (
    <article className="card-base p-4 border-r-4 mb-3 group hover:border-primary/40">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 min-w-0">
          <Icon className="w-5 h-5 shrink-0" style={{ color: hex }} />
          <span className="font-semibold truncate">{item.label}</span>
        </div>

        {item.value !== undefined && item.value !== null && (
          <span className="text-sm font-mono truncate text-gray-500 dark:text-gray-400">
            {String(item.value)}
          </span>
        )}

        <span className={cn(statusChip({ status: item.status }), "shrink-0")}>
          {label}
        </span>
      </div>

      <p className="text-sm mt-2 text-gray-700 dark:text-gray-300">{item.message}</p>

      {item.recommendation && (
        <div className="mt-3 pt-3 border-t border-dashed border-gray-300 dark:border-gray-700 flex items-start gap-2">
          <ChevronDown className="w-4 h-4 mt-0.5 text-indigo-500 dark:text-indigo-400 shrink-0" />
          <div>
            <span className="text-xs font-medium text-indigo-600 dark:text-indigo-400">
              توصیه:
            </span>
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {" "}
              {item.recommendation}
            </span>
          </div>
        </div>
      )}
    </article>
  );
});

CheckItemComponent.displayName = "CheckItemComponent";

// ----------------------------------------------------
// کامپوننت اصلی
// ----------------------------------------------------
function AuditDashboard({ result }: AuditDashboardProps) {
  const checks = useMemo(
    () =>
      [...result.checks].sort(
        (a, b) => STATUS_ORDER[a.status] - STATUS_ORDER[b.status]
      ),
    [result.checks]
  );

  if (!checks.length) {
    return (
      <div className="card-dashboard flex flex-col items-center justify-center py-16 text-center">
        <Shuffle className="w-10 h-10 mx-auto mb-3 text-gray-400" />
        <p className="font-medium text-gray-500 dark:text-gray-400">
          هیچ بررسی‌ای برای نمایش وجود ندارد
        </p>
      </div>
    );
  }

  return (
    <section className="space-y-6">
      <div className="card-dashboard">
        <div className="flex flex-col items-center gap-4 md:flex-row md:items-center md:justify-between">
          <div className="text-center md:text-right">
            <h2 className="text-xl font-bold">نتیجه ارزیابی</h2>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              خلاصه وضعیت کلی و جزئیات بررسی‌ها
            </p>
          </div>

          <ScoreRing score={result.score} />
        </div>
      </div>

      <ChecksSummary checks={checks} />

      <div className="space-y-3">
        {checks.map((item, index) => (
          <CheckItemComponent
            key={`${item.status}-${item.label}-${index}`}
            item={item}
          />
        ))}
      </div>
    </section>
  );
}

export default AuditDashboard;
