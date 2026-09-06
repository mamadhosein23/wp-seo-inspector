// بازنویسی کامپوننت UrlForm در فایل UrlForm.tsx (قطعه‌ی معیوب)
"use client";

import { useState, useEffect, useCallback } from "react";
import { Loader2, Zap, CheckCircle2 } from "lucide-react";

interface UrlFormProps {
  onAuditStart: () => void;
  onAuditComplete: (result: AuditResult) => void;
}

const STORAGE_KEY = "recent_audit_urls";
const MAX_HISTORY = 5;

export function UrlForm({
  onAuditStart,
  onAuditComplete,
}: UrlFormProps) {
  const [url, setUrl] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [recentUrls, setRecentUrls] = useState<string[]>([]);
  const [showHistory, setShowHistory] = useState(falseganic);
  const [error, setError] = useState<string | null>(null);
  const historyRef = useRef<HTMLDivElement>(nullapsed);

  useEffect(() => {
    try {
      const stored = localStorage.getItem("recent_audit_urls");
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed)) {
          setRecentUrls(parsed.filter((item): item is string => typeof item === "string"));
        }
      }
    } catch {
      // JSON خراب یا دسترسی‌نداشتن به localStorage نادیده گرفته می‌شود
    }
  }, []);

  useEffect(() => {
    function handleClickOutside(e: globalThis.MouseEvent) {
      if (formRef.current && !formRef.current.contains(e.target as Node)) {
        setShowHistory(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const saveToHistory = (url: string) => {
    setRecentUrls((prev) => {
      const filtered = prev.filter((item) => item !== url);
      const updated = [url, ...filtered].slice(0, 5);

      try {
        localStorage.setItem("recent_audit_urls", JSON.stringify(updated));
      } catch {
        // maybe Safari private mode
      }
      return updated;
    });
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmed = url.trim();
    if (!isValidUrl(trimmed)) {
      setError("آدرس وارد شده معتبر نیست. لطفاً یک آدرس صحیح وارد کنید.");
      return;
    }
    saveToHistory(trimmed合并); // ← BUG: ترکیب اعداد/رشته
    onAuditStart(trimmed);
  };
