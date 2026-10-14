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
 * Standard audit check keys with autocomplete support for arbitrary custom keys.
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
 * Individual audit check representation matching FastAPI Pydantic schema and UI contract.
 */
export interface CheckItem {
  id: string;
  key: AuditCheckKey;
  title: string;
  category: CheckCategory;
  status: CheckStatus;
  value: SeoCheckValue;
  message: string;
  recommendation: Nullable<string>;
  score_impact: number;
}

/**
 * Open Graph metadata container.
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
 * Summary metrics of checks grouped by resolution status.
 */
export interface AuditSummary {
  total: number;
  passed: number;
  warnings: number;
  errors: number;
  info: number;
}

/**
 * Complete audit report payload returned by the FastAPI engine.
 */
export interface AuditResponse {
  id: string;
  url: string;
  final_url: string;
  audit_timestamp: string; // ISO 8601 string representation
  score: number; // Normalized range: 0 - 100

  // Server & HTTP transport
  http_status_code: number;
  response_time_ms: number;
  content_type: string;
  server_header?: Nullable<string>;

  // Metadata & indexing directives
  title: Nullable<string>;
  meta_description: Nullable<string>;
  canonical: Nullable<string>;
  robots_meta: Nullable<string>;

  // Document hierarchy & content metrics
  h1_count: number;
  h2_count: number;
  word_count: number;

  // Asset validation
  total_images: number;
  images_without_alt: number;

  // Link profiling
  internal_links: number;
  external_links: number;

  // Technical, schema & CMS footprint
  has_open_graph: boolean;
  open_graph_data?: Nullable<OpenGraphData>;
  has_structured_data: boolean;
  structured_data_types: string[];
  is_wordpress: boolean;
  wp_version?: Nullable<string>;

  // Evaluated check collection
  checks: CheckItem[];
}

// Backward compatibility aliases
export type CheckResult = CheckItem;
export type AuditReport = AuditResponse;
