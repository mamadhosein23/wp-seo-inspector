// frontend/src/types/audit.ts

export type CheckStatus = "success" | "warning" | "error" | "info";

export interface CheckItem {
  key: string;
  label: string;
  status: CheckStatus;
  value?: string | number | boolean | null;
  message: string;
  recommendation?: string;
}

export interface AuditResponse {
  url: string;
  final_url: string;
  score: number;
  title: string | null;
  meta_description: string | null;
  h1_count: number;
  h2_count: number;
  word_count: number;
  total_images: number;
  images_without_alt: number;
  internal_links: number;
  external_links: number;
  has_canonical: boolean;
  has_robots_meta: boolean;
  has_open_graph: boolean;
  has_structured_data: boolean;
  checks: CheckItem[];
}
