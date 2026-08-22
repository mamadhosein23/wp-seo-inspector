"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, Zap } from "lucide-react";
import { performAudit } from "@/lib/api";
import { AuditResponse } from "@/types/audit";

interface UrlFormProps {
  onAuditStart: () => void;
  onAuditComplete: (result: AuditResponse) => void;
  onError: (error: string) => void;
}

export default function UrlForm({ onAuditStart, onAuditComplete, onError }: UrlFormProps) {
  const [url, setUrl] = useState<string>("https://tamironlineesfahan.ir");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;

    onAuditStart();
    setIsLoading(true);
    onError(""); // Clear previous errors

    try {
      const result = await performAudit(url);
      
      // به‌جای redirect، نتیجه را به کامپوننت والد برمی‌گردانیم
      onAuditComplete(result); 
      
      // اگر می‌خواستی redirect کنی:
      // router.push(`/audit?url=${encodeURIComponent(url)}`);

    } catch (error) {
      console.error("Audit failed:", error);
      onError(error instanceof Error ? error.message : "خطای ناشناخته در تحلیل صفحه.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-2xl mx-auto space-y-4">
      <div className="flex w-full">
        <input
          type="url"
          placeholder="آدرس صفحه وردپرس (مثال: https://yoursite.com/page)"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          required
          className="flex-grow p-4 text-base rounded-r-none rounded-lg border border-gray-300 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
        />
        <button
          type="submit"
          disabled={isLoading}
          className="flex items-center justify-center px-6 py-4 text-white bg-indigo-600 rounded-l-lg hover:bg-indigo-700 transition-colors disabled:bg-indigo-400 disabled:cursor-not-allowed text-base font-medium"
        >
          {isLoading ? (
            <Loader2 className="w-5 h-5 mr-2 animate-spin" />
          ) : (
            <Zap className="w-5 h-5 mr-2" />
          )}
          تحلیل سئو
        </button>
      </div>
      <p className="text-sm text-gray-500 dark:text-gray-400 text-center">
        تست برای سایت وردپرسی، مطمئن شوید بک‌اند در حال اجرا باشد.
      </p>
    </form>
  );
}
