export interface ABVariant {
  id: string;
  model_version: string;
  weight: number;
  is_control: boolean;
}

export interface ABExperiment {
  id: string;
  name: string;
  model_type: string;
  is_active: boolean;
  start_date: string | null;
  end_date: string | null;
  variants: ABVariant[];
  created_at: string;
  updated_at: string;
}

export interface ABExperimentCreate {
  name: string;
  model_type: string;
  variants: { model_version: string; weight: number; is_control: boolean }[];
}

export interface ABVariantStats {
  variant_id: string;
  model_version: string;
  sample_count: number;
  avg_confidence: number | null;
  avg_processing_time_ms: number | null;
}
