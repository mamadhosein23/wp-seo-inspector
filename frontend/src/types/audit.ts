

export const CHECK_STATUSES = [
  "success",
  "warning",
  "error",
  "info",
] as const;

export type CheckStatus = (typeof CHECK_STATUSES)[number];

export type Nullable<T> = T | null;

export type AuditScore = number;

export type HttpStatusCode = number;

export type Milliseconds = number;

export type SeoCheckValue = string | number | boolean | null;

export type AuditCheckKey =
  | "http_status"
  | "response_time"
  | "title"
  | "meta_description"
  | "canonical"
  | "robots_meta"
  | "h1"
  | "h2"
  | "word_count"
  | "images_alt"
  | "internal_links"
  | "external_links"
  | "open_graph"
  | "structured_data"
  | "wordpress"
  | "content_type"
  | string;

/**
 * Represents a single SEO/audit check result.
 */
export interface CheckItem {
  key: AuditCheckKey;
  label: string;
  status: CheckStatus;
  value: SeoCheckValue;
  message: string;
  recommendation: Nullable<string>;
}

/**
 * Main audit response returned from backend.
 */
export interface AuditResponse {
  url: string;
  final_url: string;
  score: AuditScore;

  http_status_code: HttpStatusCode;
  response_time_ms: Milliseconds;
  content_type: string;

  title: Nullable<string>;
  meta_description: Nullable<string>;
  canonical: Nullable<string>;
  robots_meta: Nullable<string>;

  h1_count: number;
  h2_count: number;
  word_count: number;

  total_images: number;
  images_without_alt: number;

  internal_links: number;
  external_links: number;

  has_open_graph: boolean;
  has_structured_data: boolean;
  is_wordpress: boolean;

  checks: CheckItem[];
}
