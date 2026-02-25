export interface WebhookEndpoint {
  id: string;
  organization_id: string;
  url: string;
  secret: string;
  is_active: boolean;
  events: string[];
  description: string | null;
  failure_count: number;
  last_triggered_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface WebhookDelivery {
  id: string;
  webhook_id: string;
  event_type: string;
  payload: Record<string, unknown>;
  response_status: number | null;
  success: boolean;
  attempt: number;
  error_message: string | null;
  created_at: string;
}

export interface WebhookCreate {
  url: string;
  events: string[];
  description?: string;
}

export interface WebhookUpdate {
  url?: string;
  events?: string[];
  description?: string;
  is_active?: boolean;
}
