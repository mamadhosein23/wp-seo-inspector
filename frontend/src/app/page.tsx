// frontend/src/app/page.tsx
"use client";

import { useState } from "react";
import UrlForm from "@/components/UrlForm";
import AuditDashboard from "@/components/AuditDashboard";
import { AuditResponse } from "@/types/audit";
import { AlertCircle } from "lucide-react";

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
    <main className="container mx-auto px-4 py-12">
      <div className="text-center mb-12">
        <h1 className="text-5xl font-extrabold text-gray-900 dark:text-white mb-3">
          WP SEO Inspector
        </h1>
        <p className="text-xl text-indigo-600 dark:text-indigo-400 font-medium">
          تحلیلگر جامع سئو فنی برای صفحات وردپرسی
        </p>
        <p className="mt-4 text-gray-600 dark:text-gray-400 max-w-xl mx-auto">
          پروژه‌ای رزومه‌ای با معماری Next.js + FastAPI
        </p>
      </div>

      <UrlForm
        onAuditStart={handleAuditStart}
        onAuditComplete={handleAuditComplete}
        onError={handleError}
      />

      {/* Loading State */}
      {isLoading && (
        <div className="mt-10 text-center p-8 card max-w-2xl mx-auto">
          <p className="text-indigo-500 font-semibold text-lg">
            در حال تحلیل صفحه...
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
            لطفاً چند لحظه صبر کنید. عملیات تحلیل تا 15 ثانیه طول می‌کشد.
          </p>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mt-10 card bg-red-50 dark:bg-red-900/20 border-red-400 max-w-3xl mx-auto">
          <div className="flex items-center text-red-700 dark:text-red-400">
            <AlertCircle className="w-6 h-6 ml-3" />
            <span className="font-semibold text-lg">خطا در اجرای تحلیل:</span>
          </div>
          <p className="mt-3 text-red-600 dark:text-red-300 whitespace-pre-wrap">{error}</p>
        </div>
      )}

      {/* Result Dashboard */}
      {auditResult && (
        <div className="mt-10">
          <AuditDashboard result={auditResult} />
        </div>
      )}
    </main>
  );
}
