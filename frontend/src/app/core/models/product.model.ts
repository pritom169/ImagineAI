export interface ProductImage {
  id: string;
  s3_key: string;
  original_filename: string | null;
  content_type: string | null;
  file_size_bytes: number | null;
  width: number | null;
  height: number | null;
  is_primary: boolean;
  upload_status: string;
  created_at: string;
}

export interface Product {
  id: string;
  user_id: string;
  organization_id: string;
  title: string | null;
  description: string | null;
  category: string | null;
  subcategory: string | null;
  ai_description: string | null;
  status: string;
  metadata_: Record<string, unknown>;
  images: ProductImage[];
  created_at: string;
  updated_at: string;
}

export interface ProductListResponse {
  items: Product[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface ProductCreate {
  title: string;
  description?: string;
  category?: string;
}
