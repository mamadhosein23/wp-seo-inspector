export const CHECK_STATUSES = ["success", "warning", "error", "info"] as const;

export type CheckStatus = (typeof CHECK_STATUSES)[number];
export const CHECK_CATEGORIES = [
  "technical",
  "content",
  "indexing",
  "performance",
  "schema",
  "security",
] as const;
export type CheckCategory = (typeof CHECK_CATEGORIES)[number];

export type Nullable<T> = T | null;

/**
 * کلیدهای شناخته‌شده به همراه پشتیبانی از کلیدهای سفارشی بدون از بین رفتن Autocomplete
 */
export type KnownAuditCheckKey =
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
  | "ssl_status"
  | "mobile_friendly";

export type AuditCheckKey = KnownAuditCheckKey | (string & {});

export type SeoCheckValue =
  | string
  | number
  | boolean
  | null
  | Record<string, unknown>
  | unknown[];

/**
 * ساختار هر آیتم ممیزی در داشبورد
 */
export interface CheckItem {
  id?: string;
  key: AuditCheckKey;
  label: string;
  category?: CheckCategory;
  status: CheckStatus;
  value: SeoCheckValue;
  message: string;
  recommendation: Nullable<string>;
  score_impact?: number;
}

/**
 * جزئیات متاتگ‌های Open Graph
 */
export interface OpenGraphData {
  title?: Nullable<string>;
  description?: Nullable<string>;
  image?: Nullable<string>;
  url?: Nullable<string>;
  type?: Nullable<string>;
  site_name?: Nullable<string>;
}

/**
 * ساختار اصلی ریسپانس بازگشتی از FastAPI
 */
export interface AuditResponse {
  id?: string;
  url: string;
  final_url: string;
  audit_timestamp?: string;
  score: number; // بین 0 تا 100

  // مشخصات شبکه و سرور
  http_status_code: number;
  response_time_ms: number;
  content_type: string;
  server_header?: Nullable<string>;

  // سئو متاتگ‌ها و عناوین
  title: Nullable<string>;
  meta_description: Nullable<string>;
  canonical: Nullable<string>;
  robots_meta: Nullable<string>;

  // محتوا و تگ‌های ساختاری
  h1_count: number;
  h2_count: number;
  word_count: number;

  // مدیا و تصاویر
  total_images: number;
  images_without_alt: number;

  // لینک‌سازی داخلی و خارجی
  internal_links: number;
  external_links: number;

  // قابلیت‌ها و پرچم‌های تکنیکال
  has_open_graph: boolean;
  open_graph_data?: Nullable<OpenGraphData>;
  has_structured_data: boolean;
  structured_data_types?: string[];
  is_wordpress: boolean;
  wp_version?: Nullable<string>;

  // لیست کل تحلیل‌ها
  checks: CheckItem[];
}
