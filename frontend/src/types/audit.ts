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
 * کلیدهای ممیزی به همراه پشتیبانی اتوکامپلیت برای کلیدهای کاستوم
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
 * ساختار هر چک آیتم (همگام با نیازهای UI و Pydantic)
 */
export interface CheckItem {
  id?: string;
  key: AuditCheckKey;
  label: string; // نام نمایشی چک
  title?: string; // سازگاری با داشبورد قبلی
  category: CheckCategory;
  status: CheckStatus;
  value: SeoCheckValue;
  message: string;
  recommendation: Nullable<string>;
  score_impact?: number;
}

/**
 * متاتگ‌های Open Graph
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
 * ریسپانس کلی موتور ممیزی سئو (FastAPI Response Schema)
 */
export interface AuditResponse {
  id?: string;
  url: string;
  final_url: string;
  audit_timestamp?: string | number;
  score: number; // 0 - 100

  // سرور و وضعیت HTTP
  http_status_code: number;
  response_time_ms: number;
  content_type: string;
  server_header?: Nullable<string>;

  // متاتگ‌ها و ایندکس‌پذیری
  title: Nullable<string>;
  meta_description: Nullable<string>;
  canonical: Nullable<string>;
  robots_meta: Nullable<string>;

  // ساختار محتوا
  h1_count: number;
  h2_count: number;
  word_count: number;

  // تصاویر
  total_images: number;
  images_without_alt: number;

  // لینک‌ها
  internal_links: number;
  external_links: number;

  // تکنیکال و اسکیما
  has_open_graph: boolean;
  open_graph_data?: Nullable<OpenGraphData>;
  has_structured_data: boolean;
  structured_data_types?: string[];
  is_wordpress: boolean;
  wp_version?: Nullable<string>;

  // لیست چک‌ها
  checks: CheckItem[];
}

// الیاس‌ها جهت جلوگیری از شکستن بیلد در کامپوننت‌های قبلی
export type CheckResult = CheckItem;
export type AuditReport = AuditResponse;
