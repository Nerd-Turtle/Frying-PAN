import type {
  AdminUserCreate,
  AnalysisFilters,
  AnalysisRunResponse,
  AuthSession,
  ChangeSetRead,
  ExportRead,
  HealthResponse,
  ProjectDetail,
  ProjectSummary,
} from "@/src/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...init?.headers,
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`${response.status} ${response.statusText}: ${detail}`);
  }

  return (await response.json()) as T;
}

async function requestOptional<T>(path: string, init?: RequestInit): Promise<T | null> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...init?.headers,
    },
    cache: "no-store",
  });

  if (response.status === 401) {
    return null;
  }

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`${response.status} ${response.statusText}: ${detail}`);
  }

  return (await response.json()) as T;
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

export async function logoutAccount(): Promise<void> {
  await fetch(`${API_BASE_URL}/api/auth/logout`, {
    method: "POST",
    credentials: "include",
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
