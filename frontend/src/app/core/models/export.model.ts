export interface ExportJob {
  id: string;
  organization_id: string;
  user_id: string;
  export_type: string;
  status: string;
  filters: Record<string, unknown>;
  file_size_bytes: number | null;
  row_count: number | null;
  error_message: string | null;
  expires_at: string | null;
  download_url?: string;
  created_at: string;
  updated_at: string;
}

export interface ExportRequest {
  export_type: string;
  filters: ExportFilter;
}

export interface ExportFilter {
  date_from?: string;
  date_to?: string;
  status?: string;
  category?: string;
}
