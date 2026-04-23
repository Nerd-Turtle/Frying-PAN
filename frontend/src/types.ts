export type HealthResponse = {
  status: string;
  service: string;
};

export type UserRecord = {
  id: string;
  username: string;
  email?: string | null;
  display_name: string;
  role: string;
  status: string;
  must_change_password: boolean;
  created_at: string;
  updated_at: string;
};

export type UserDirectoryEntry = {
  id: string;
  username: string;
  display_name: string;
};

export type OrganizationRecord = {
  id: string;
  name: string;
  slug: string;
  created_at: string;
  updated_at: string;
};

export type AuthSession = {
  user: UserRecord;
  organizations: OrganizationRecord[];
  session_expires_at: string;
  password_change_required: boolean;
};

export type ProfileUpdate = {
  display_name?: string;
  email?: string;
};

export type AdminUserCreate = {
  username: string;
  display_name: string;
  password: string;
  email?: string;
  role?: string;
  must_change_password?: boolean;
};

export type Source = {
  id: string;
  label: string;
  filename: string;
  storage_path: string;
  file_sha256: string;
  source_type: string;
  parse_status: string;
  imported_by_user_id?: string | null;
  imported_at: string;
};

export type EventRecord = {
  id: string;
  actor_user_id?: string | null;
  event_type: string;
  payload?: string | null;
  created_at: string;
};

export type NotificationSettings = {
  notification_timeout_seconds: number;
};

export type NotificationHistoryEntry = {
  id: string;
  event_type: string;
  payload?: string | null;
  actor_display_name?: string | null;
  project_name?: string | null;
  created_at: string;
};

export type AuditLogEntry = {
  id: string;
  source: string;
  event_type: string;
  payload?: string | null;
  actor_display_name?: string | null;
  project_name?: string | null;
  created_at: string;
};

export type ProjectSummary = {
  id: string;
  organization_id?: string | null;
  name: string;
  description?: string | null;
  status: string;
  visibility: "public" | "private";
  created_by_user_id?: string | null;
  created_by_display_name?: string | null;
  owner_user_id?: string | null;
  owner_display_name?: string | null;
  collaborators?: ProjectCollaborator[];
  created_at: string;
  updated_at: string;
};

export type ProjectUpdate = {
  name?: string;
  description?: string | null;
  visibility?: "public" | "private";
  contributor_usernames?: string[];
};

export type ProjectDetail = ProjectSummary & {
  sources: Source[];
  events: EventRecord[];
};

export type ProjectCollaborator = {
  user_id: string;
  username?: string | null;
  display_name?: string | null;
  role: string;
};

export type AnalysisFilters = {
  source_id?: string;
  object_type?: string;
  scope_path?: string;
};

export type AnalysisObjectRef = {
  id: string;
  source_id: string;
  scope_path: string;
  object_type: string;
  object_name: string;
  normalized_hash?: string | null;
  raw_payload: Record<string, unknown>;
  normalized_payload: Record<string, unknown>;
};

export type DuplicateFinding = {
  finding_kind: string;
  object_type: string;
  key: string;
  normalized_payload?: Record<string, unknown> | null;
  items: AnalysisObjectRef[];
};

export type NormalizationSuggestion = {
  object_id: string;
  source_id: string;
  scope_path: string;
  object_type: string;
  object_name: string;
  kind: string;
  original_value: string;
  suggested_value: string;
};

export type PromotionAssessment = {
  object_id: string;
  source_id: string;
  scope_path: string;
  object_type: string;
  object_name: string;
  status: string;
  blockers: string[];
  dependency_targets: string[];
  mixed_scope_dependencies: boolean;
  notes: string[];
};

export type ProjectAnalysisReport = {
  generated_at: string;
  filters: AnalysisFilters;
  duplicate_name_findings: DuplicateFinding[];
  duplicate_value_findings: DuplicateFinding[];
  normalization_suggestions: NormalizationSuggestion[];
  promotion_candidates: PromotionAssessment[];
  promotion_blockers: PromotionAssessment[];
};

export type AnalysisRunResponse = {
  status: string;
  message: string;
  report: ProjectAnalysisReport;
};

export type ChangeSetRead = {
  id: string;
  project_id: string;
  name: string;
  description?: string | null;
  status: string;
  created_at: string;
  applied_at?: string | null;
  preview_summary: Record<string, unknown>;
  operations_payload: {
    object_operations?: Record<string, unknown>[];
    reference_rewrites?: Record<string, unknown>[];
    normalization_operations?: Record<string, unknown>[];
    blocked_objects?: Record<string, unknown>[];
    [key: string]: unknown;
  };
};

export type ExportRead = {
  id: string;
  project_id: string;
  change_set_id?: string | null;
  filename: string;
  storage_path: string;
  file_sha256: string;
  export_status: string;
  metadata_json: Record<string, unknown>;
  created_at: string;
};
