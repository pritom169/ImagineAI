export interface JobStep {
  id: string;
  step_name: string;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  duration_ms: number | null;
  error_message: string | null;
  result_data: Record<string, unknown>;
}

export interface ProcessingJob {
  id: string;
  user_id: string;
  job_type: string;
  status: string;
  total_images: number;
  processed_images: number;
  failed_images: number;
  celery_task_id: string | null;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  steps: JobStep[];
  created_at: string;
  updated_at: string;
}

export interface ProcessingUpdate {
  type: 'step_update' | 'job_complete' | 'job_failed';
  job_id: string;
  image_id?: string;
  step?: string;
  status: string;
  progress?: { completed: number; total: number };
  data?: Record<string, unknown>;
  timestamp: string;
}

export interface DashboardStats {
  total_products: number;
  total_images: number;
  completed_analyses: number;
  total_defects: number;
  active_jobs: number;
  avg_processing_time_ms: number | null;
}

export interface CategoryDistribution {
  category: string;
  count: number;
}
