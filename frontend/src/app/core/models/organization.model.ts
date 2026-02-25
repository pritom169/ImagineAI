export interface Organization {
  id: string;
  name: string;
  slug: string;
  is_active: boolean;
  plan: string;
  settings: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface OrganizationMember {
  id: string;
  organization_id: string;
  user_id: string;
  role: string;
  user_email?: string;
  user_name?: string;
  created_at: string;
}

export interface OrganizationCreate {
  name: string;
  slug: string;
}

export interface InviteMemberRequest {
  email: string;
  role?: string;
}
