import { AuditResponse } from "@/types/audit";

// آدرس لوکال بک‌اند (FastAPI)
const API_BASE_URL = "http://127.0.0.1:8000";

export const performAudit = async (url: string): Promise<AuditResponse> => {
  const response = await fetch(`${API_BASE_URL}/api/audit`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ url }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: "Unknown error" }));
    
    // اگر از سمت بک‌اند خطا داشته باشیم
    const errorMessage = errorData.detail || `HTTP Error: ${response.status} ${response.statusText}`;
    throw new Error(errorMessage);
  }

  const data: AuditResponse = await response.json();
  return data;
};
