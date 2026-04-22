import type {
  AuditLogEntry,
  AdminUserCreate,
  AnalysisFilters,
  AnalysisRunResponse,
  AuthSession,
  ChangeSetRead,
  ExportRead,
  HealthResponse,
  NotificationHistoryEntry,
  NotificationSettings,
  ProfileUpdate,
  ProjectDetail,
  ProjectSummary,
  ProjectUpdate,
} from "@/src/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

type ValidationIssue = {
  type?: string;
  loc?: Array<string | number>;
  msg?: string;
  ctx?: Record<string, unknown>;
};

async function parseErrorResponse(response: Response): Promise<string> {
  const contentType = response.headers.get("content-type") ?? "";
  const rawText = await response.text();

  if (!rawText) {
    return response.statusText || "Request failed.";
  }

  if (!contentType.includes("application/json")) {
    return rawText;
  }

  try {
    const parsed = JSON.parse(rawText) as {
      detail?: string | ValidationIssue[] | Record<string, unknown>;
    };

    if (typeof parsed.detail === "string") {
      return parsed.detail;
    }

    if (Array.isArray(parsed.detail)) {
      return parsed.detail
        .slice(0, 3)
        .map(formatValidationIssue)
        .join(" ");
    }

    return rawText;
  } catch {
    return rawText;
  }
}

function formatValidationIssue(issue: ValidationIssue): string {
  const field = issue.loc
    ?.filter((item) => typeof item === "string" && item !== "body")
    .map((item) => String(item))
    .at(-1);
  const label = field
    ? `${field.replaceAll("_", " ").replace(/^\w/, (char) => char.toUpperCase())}`
    : "Field";

  if (issue.type === "string_too_short" && typeof issue.ctx?.min_length === "number") {
    return `${label} must be at least ${issue.ctx.min_length} characters.`;
  }

  if (issue.type === "string_too_long" && typeof issue.ctx?.max_length === "number") {
    return `${label} must be at most ${issue.ctx.max_length} characters.`;
  }

  if (issue.type === "missing") {
    return `${label} is required.`;
  }

  if (issue.msg) {
    if (!field) {
      return issue.msg;
    }
    if (issue.msg.toLowerCase().startsWith(label.toLowerCase())) {
      return issue.msg;
    }
    return `${label}: ${issue.msg}.`.replace(/\.\./g, ".");
  }

  return "Request data is invalid.";
}

async function throwApiError(response: Response): Promise<never> {
  const detail = await parseErrorResponse(response);
  throw new Error(`${response.status} ${detail}`);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      credentials: "include",
      headers: {
        ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
        ...init?.headers,
      },
      cache: "no-store",
    });
  } catch (error) {
    throw new Error(
      "Unable to reach the Frying-PAN API from this browser. Check that the backend is running and reachable.",
    );
  }

  if (!response.ok) {
    await throwApiError(response);
  }

  return (await response.json()) as T;
}

async function requestOptional<T>(path: string, init?: RequestInit): Promise<T | null> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      credentials: "include",
      headers: {
        ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
        ...init?.headers,
      },
      cache: "no-store",
    });
  } catch (error) {
    throw new Error(
      "Unable to reach the Frying-PAN API from this browser. Check that the backend is running and reachable.",
    );
  }

  if (response.status === 401) {
    return null;
  }

  if (!response.ok) {
    await throwApiError(response);
  }

  return (await response.json()) as T;
}

async function requestVoid(path: string, init?: RequestInit): Promise<void> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      credentials: "include",
      headers: {
        ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
        ...init?.headers,
      },
      cache: "no-store",
    });
  } catch {
    throw new Error(
      "Unable to reach the Frying-PAN API from this browser. Check that the backend is running and reachable.",
    );
  }

  if (!response.ok) {
    await throwApiError(response);
  }
}

export function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/api/health");
}

export function getSession(): Promise<AuthSession | null> {
  return requestOptional<AuthSession>("/api/auth/session");
}

export function loginAccount(payload: {
  username: string;
  password: string;
}): Promise<AuthSession> {
  return request<AuthSession>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function changePassword(payload: {
  current_password: string;
  new_password: string;
}): Promise<AuthSession> {
  return request<AuthSession>("/api/auth/change-password", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateProfile(payload: ProfileUpdate): Promise<AuthSession["user"]> {
  return request<AuthSession["user"]>("/api/auth/profile", {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function logoutAccount(): Promise<void> {
  await requestVoid("/api/auth/logout", {
    method: "POST",
  });
}

export function listProjects(): Promise<ProjectSummary[]> {
  return request<ProjectSummary[]>("/api/projects");
}

export function getProject(projectId: string): Promise<ProjectDetail> {
  return request<ProjectDetail>(`/api/projects/${projectId}`);
}

export function createProject(payload: {
  name: string;
  description?: string;
  organization_id?: string;
}): Promise<ProjectSummary> {
  return request<ProjectSummary>("/api/projects", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateProject(projectId: string, payload: ProjectUpdate): Promise<ProjectSummary> {
  return request<ProjectSummary>(`/api/projects/${projectId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function deleteProject(projectId: string): Promise<void> {
  await requestVoid(`/api/projects/${projectId}`, {
    method: "DELETE",
  });
}

export function uploadSource(projectId: string, file: File): Promise<unknown> {
  const body = new FormData();
  body.append("file", file);

  return request(`/api/projects/${projectId}/sources/upload`, {
    method: "POST",
    body,
  });
}

export function runAnalysis(
  projectId: string,
  filters?: AnalysisFilters,
): Promise<AnalysisRunResponse> {
  const params = new URLSearchParams();
  if (filters?.source_id) {
    params.set("source_id", filters.source_id);
  }
  if (filters?.object_type) {
    params.set("object_type", filters.object_type);
  }
  if (filters?.scope_path) {
    params.set("scope_path", filters.scope_path);
  }

  return request<AnalysisRunResponse>(
    `/api/projects/${projectId}/analysis/run${params.size > 0 ? `?${params.toString()}` : ""}`,
    { method: "POST" },
  );
}

export function previewMerge(
  projectId: string,
  payload: {
    name: string;
    description?: string;
    selected_object_ids: string[];
    selected_normalizations: Array<{ object_id: string; kind: string }>;
  },
): Promise<ChangeSetRead> {
  return request<ChangeSetRead>(`/api/projects/${projectId}/merge/preview`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function applyChangeSet(projectId: string, changeSetId: string): Promise<ChangeSetRead> {
  return request<ChangeSetRead>(`/api/projects/${projectId}/change-sets/${changeSetId}/apply`, {
    method: "POST",
  });
}

export function exportProject(
  projectId: string,
  payload?: { change_set_id?: string },
): Promise<ExportRead> {
  return request<ExportRead>(`/api/projects/${projectId}/exports`, {
    method: "POST",
    body: JSON.stringify(payload ?? {}),
  });
}

export function listUsers(): Promise<Array<AuthSession["user"]>> {
  return request<Array<AuthSession["user"]>>("/api/admin/users");
}

export function createLocalUser(payload: AdminUserCreate): Promise<AuthSession["user"]> {
  return request<AuthSession["user"]>("/api/admin/users", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateLocalUser(
  userId: string,
  payload: {
    display_name?: string;
    email?: string;
    role?: string;
    status?: string;
    reset_password?: string;
    must_change_password?: boolean;
  },
): Promise<AuthSession["user"]> {
  return request<AuthSession["user"]>(`/api/admin/users/${userId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function listAuditLog(limit = 100): Promise<AuditLogEntry[]> {
  return request<AuditLogEntry[]>(`/api/admin/audit-log?limit=${limit}`);
}

export function getNotificationSettings(): Promise<NotificationSettings> {
  return request<NotificationSettings>("/api/notifications/settings");
}

export function updateNotificationSettings(
  payload: NotificationSettings,
): Promise<NotificationSettings> {
  return request<NotificationSettings>("/api/notifications/settings", {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function listNotificationHistory(limit = 20): Promise<NotificationHistoryEntry[]> {
  return request<NotificationHistoryEntry[]>(`/api/notifications/history?limit=${limit}`);
}
