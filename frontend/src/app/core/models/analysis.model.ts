export interface ExtractedAttribute {
  id: string;
  attribute_name: string;
  attribute_value: string;
  confidence: number | null;
}

export interface DetectedDefect {
  id: string;
  defect_type: string;
  severity: string;
  confidence: number | null;
  bounding_box: { x: number; y: number; width: number; height: number } | null;
  description: string | null;
}

export interface AnalysisResult {
  id: string;
  product_image_id: string;
  model_version: string;
  classification_label: string | null;
  classification_confidence: number | null;
  classification_scores: Record<string, unknown>;
  description_text: string | null;
  description_model: string | null;
  processing_time_ms: number | null;
  status: string;
  error_message: string | null;
  experiment_id: string | null;
  variant_id: string | null;
  extracted_attributes: ExtractedAttribute[];
  detected_defects: DetectedDefect[];
  created_at: string;
  updated_at: string;
}
