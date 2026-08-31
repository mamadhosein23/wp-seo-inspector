export type CheckStatus = "pass" | "fail" | "warning" | "info";

export type CheckCategory =
  | "indexability"
  | "security"
  | "performance"
  | "content"
  | "structure";

export interface CheckResult {
  id: string;
  name: string;
  category: CheckCategory;
  status: CheckStatus;
  score_impact: number;
  message: string;
  recommendation: string | null;
  details?: Record<string, unknown>;
}

export interface SocialGraphInfo {
  og_title?: string | null;
  og_description?: string | null;
  og_image?: string | null;
  twitter_card?: string | null;
}

export interface TechnicalSignals {
  is_wordpress: boolean;
  generator?: string | null;
  detected_plugins: string[];
  theme?: string | null;
}

export interface AuditReport {
  url: string;
  status_code: number;
  final_score: number;
  execution_time_ms: number;
  checks: CheckResult[];
  social: SocialGraphInfo;
  technical: TechnicalSignals;
  timestamp: string;
}
