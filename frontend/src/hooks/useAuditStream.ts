import { useState, useCallback } from "react";

export interface AuditEvent {
  step: "INIT" | "FETCHED" | "RULE_EVALUATED" | "COMPLETE";
  message?: string;
  score?: number;
  data?: any;
  results?: any[];
}

export function useAuditStream() {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [finalScore, setFinalScore] = useState<number | null>(null);

  const startAudit = useCallback((targetUrl: string) => {
    setIsRunning(true);
    setEvents([]);
    setFinalScore(null);

    const es = new EventSource(`/api/v1/audit/stream?url=${encodeURIComponent(targetUrl)}`);

    es.onmessage = (event) => {
      const payload: AuditEvent = JSON.parse(event.data);
      setEvents((prev) => [...prev, payload]);

      if (payload.step === "COMPLETE") {
        setFinalScore(payload.score ?? 0);
        es.close();
        setIsRunning(false);
      }
    };

    es.onerror = () => {
      es.close();
      setIsRunning(false);
    };
  }, []);

  return { startAudit, events, isRunning, finalScore };
}
