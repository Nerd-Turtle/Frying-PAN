"use client";

import { useEffect, useState } from "react";

import { AdminUserPanel } from "@/components/admin-user-panel";
import { AuthPanel } from "@/components/auth-panel";
import { CreateProjectForm } from "@/components/create-project-form";
import { PasswordChangePanel } from "@/components/password-change-panel";
import { UploadSourceForm } from "@/components/upload-source-form";
import {
  applyChangeSet,
  changePassword,
  createLocalUser,
  createProject,
  exportProject,
  getProject,
  getSession,
  listUsers,
  listProjects,
  loginAccount,
  logoutAccount,
  previewMerge,
  runAnalysis,
  uploadSource,
  updateLocalUser,
} from "@/lib/api";
import type {
  AnalysisFilters,
  AnalysisRunResponse,
  AuthSession,
  ChangeSetRead,
  ExportRead,
  NormalizationSuggestion,
  ProjectDetail,
  ProjectSummary,
  UserRecord,
} from "@/src/types";

type WorkbenchMessage = {
  tone: "info" | "success" | "error";
  text: string;
};

const objectTypeOptions = [
  { value: "", label: "All supported types" },
  { value: "address", label: "Address" },
  { value: "address_group", label: "Address group" },
  { value: "service", label: "Service" },
  { value: "service_group", label: "Service group" },
  { value: "tag", label: "Tag" },
];

export function WorkbenchShell() {
  const [session, setSession] = useState<AuthSession | null>(null);
  const [users, setUsers] = useState<UserRecord[]>([]);
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [selectedProject, setSelectedProject] = useState<ProjectDetail | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisRunResponse | null>(null);
  const [previewChangeSet, setPreviewChangeSet] = useState<ChangeSetRead | null>(null);
  const [latestExport, setLatestExport] = useState<ExportRead | null>(null);
  const [selectedObjectIds, setSelectedObjectIds] = useState<string[]>([]);
  const [selectedNormalizationKeys, setSelectedNormalizationKeys] = useState<string[]>([]);
  const [analysisFilters, setAnalysisFilters] = useState({
    source_id: "",
    object_type: "",
    scope_path: "",
  });
  const [previewName, setPreviewName] = useState("Shared promotion preview");
  const [previewDescription, setPreviewDescription] = useState(
    "Backend-generated preview of selected promotions and normalization updates.",
  );
  const [initialBusy, setInitialBusy] = useState(true);
  const [authBusy, setAuthBusy] = useState(false);
  const [projectBusy, setProjectBusy] = useState(false);
  const [analysisBusy, setAnalysisBusy] = useState(false);
  const [previewBusy, setPreviewBusy] = useState(false);
  const [applyBusy, setApplyBusy] = useState(false);
  const [exportBusy, setExportBusy] = useState(false);
  const [message, setMessage] = useState<WorkbenchMessage | null>(null);

  useEffect(() => {
    void initializeShell();
  }, []);

  useEffect(() => {
    if (!selectedProjectId || !session || session.password_change_required) {
      setSelectedProject(null);
      return;
    }

    void loadProject(selectedProjectId);
  }, [selectedProjectId, session]);

  async function initializeShell(preferredProjectId?: string) {
    setInitialBusy(true);

    try {
      const currentSession = await getSession();
      setSession(currentSession);

      if (!currentSession) {
        resetWorkbenchState();
        setMessage(null);
        return;
      }

      await loadAuthenticatedShell(currentSession, preferredProjectId);
      setMessage(null);
    } catch (caught) {
      setMessage({
        tone: "error",
        text:
          caught instanceof Error
            ? caught.message
            : "Unknown error while loading the Frying-PAN workbench.",
      });
    } finally {
      setInitialBusy(false);
    }
  }

  async function loadAuthenticatedShell(
    currentSession: AuthSession,
    preferredProjectId?: string,
  ) {
    if (currentSession.password_change_required) {
      setProjects([]);
      setUsers([]);
      setSelectedProjectId(null);
      setSelectedProject(null);
      clearActionState();
      return;
    }

    const [projectResponse, userResponse] = await Promise.all([
      listProjects(),
      currentSession.user.role === "admin" ? listUsers() : Promise.resolve([]),
    ]);

    setProjects(projectResponse);
    setUsers(userResponse);

    const nextSelectedProjectId =
      preferredProjectId ?? selectedProjectId ?? projectResponse[0]?.id ?? null;

    setSelectedProjectId(nextSelectedProjectId);
  }

  async function loadProject(projectId: string) {
    setProjectBusy(true);

    try {
      const detail = await getProject(projectId);
      setSelectedProject(detail);
      setMessage(null);
    } catch (caught) {
      if (handlePotentialUnauthorized(caught)) {
        return;
      }
      resetProjectView();
      setMessage({
        tone: "error",
        text:
          caught instanceof Error
            ? caught.message
            : "Unknown error while loading the selected project.",
      });
    } finally {
      setProjectBusy(false);
    }
  }

  async function refreshProject(projectId: string) {
      const [projectResponse, detail, userResponse] = await Promise.all([
        listProjects(),
        getProject(projectId),
        session?.user.role === "admin" ? listUsers() : Promise.resolve([]),
      ]);
      setProjects(projectResponse);
      setUsers(userResponse);
      setSelectedProject(detail);
  }

  async function handleLogin(payload: { username: string; password: string }) {
    setAuthBusy(true);
    try {
      const currentSession = await loginAccount(payload);
      setSession(currentSession);
      await loadAuthenticatedShell(currentSession);
      setMessage({
        tone: "success",
        text: currentSession.password_change_required
          ? "Temporary password accepted. Set a new password to continue."
          : `Signed in as ${currentSession.user.display_name}.`,
      });
    } catch (caught) {
      setMessage({
        tone: "error",
        text:
          caught instanceof Error ? caught.message : "Unknown error while signing in.",
      });
    } finally {
      setAuthBusy(false);
    }
  }

  async function handleChangePassword(payload: {
    current_password: string;
    new_password: string;
  }) {
    setAuthBusy(true);
    try {
      const currentSession = await changePassword(payload);
      setSession(currentSession);
      await loadAuthenticatedShell(currentSession);
      setMessage({
        tone: "success",
        text: "Password updated. The workbench is now unlocked.",
      });
    } catch (caught) {
      setMessage({
        tone: "error",
        text: caught instanceof Error ? caught.message : "Unknown error while updating password.",
      });
    } finally {
      setAuthBusy(false);
    }
  }

  async function handleLogout() {
    setAuthBusy(true);
    try {
      await logoutAccount();
      setSession(null);
      resetWorkbenchState();
      setMessage({
        tone: "info",
        text: "Signed out.",
      });
    } catch (caught) {
      setMessage({
        tone: "error",
        text:
          caught instanceof Error ? caught.message : "Unknown error while signing out.",
      });
    } finally {
      setAuthBusy(false);
    }
  }

  async function handleCreate(payload: {
    name: string;
    description?: string;
    organization_id?: string;
  }) {
    try {
      const created = await createProject(payload);
      await initializeShell(created.id);
      clearActionState();
      setMessage({
        tone: "success",
        text: `Created project "${created.name}".`,
      });
    } catch (caught) {
      if (handlePotentialUnauthorized(caught)) {
        return;
      }
      setMessage({
        tone: "error",
        text:
          caught instanceof Error
            ? caught.message
            : "Unknown error while creating the project.",
      });
    }
  }

  async function handleUpload(projectId: string, file: File) {
    try {
      await uploadSource(projectId, file);
      await refreshProject(projectId);
      clearActionState();
      setMessage({
        tone: "success",
        text: `Uploaded ${file.name} and refreshed project inventory state.`,
      });
    } catch (caught) {
      if (handlePotentialUnauthorized(caught)) {
        return;
      }
      setMessage({
        tone: "error",
        text:
          caught instanceof Error
            ? caught.message
            : "Unknown error while uploading the source XML.",
      });
    }
  }

  async function handleCreateLocalUser(payload: {
    username: string;
    display_name: string;
    password: string;
    role: string;
    must_change_password: boolean;
  }) {
    setAuthBusy(true);
    try {
      const created = await createLocalUser(payload);
      setUsers(await listUsers());
      setMessage({
        tone: "success",
        text: `Created local user ${created.username}.`,
      });
    } catch (caught) {
      setMessage({
        tone: "error",
        text:
          caught instanceof Error ? caught.message : "Unknown error while creating the user.",
      });
    } finally {
      setAuthBusy(false);
    }
  }

  async function handleToggleUserStatus(user: UserRecord) {
    setAuthBusy(true);
    try {
      await updateLocalUser(user.id, {
        status: user.status === "active" ? "disabled" : "active",
      });
      setUsers(await listUsers());
      setMessage({
        tone: "success",
        text: `${user.username} is now ${user.status === "active" ? "disabled" : "active"}.`,
      });
    } catch (caught) {
      setMessage({
        tone: "error",
        text:
          caught instanceof Error ? caught.message : "Unknown error while updating the user.",
      });
    } finally {
      setAuthBusy(false);
    }
  }

  async function handleRunAnalysis() {
    if (!selectedProjectId) {
      return;
    }

    setAnalysisBusy(true);

    try {
      const filters = compactFilters(analysisFilters);
      const response = await runAnalysis(selectedProjectId, filters);
      setAnalysis(response);
      setPreviewChangeSet(null);
      setLatestExport(null);
      setSelectedObjectIds([]);
      setSelectedNormalizationKeys([]);
      setMessage({
        tone: "success",
        text: "Analysis completed from canonical project inventory.",
      });
    } catch (caught) {
      if (handlePotentialUnauthorized(caught)) {
        return;
      }
      setMessage({
        tone: "error",
        text:
          caught instanceof Error
            ? caught.message
            : "Unknown error while generating the analysis report.",
      });
    } finally {
      setAnalysisBusy(false);
    }
  }

  async function handlePreviewChangeSet() {
    if (!selectedProjectId) {
      return;
    }

    setPreviewBusy(true);

    try {
      const response = await previewMerge(selectedProjectId, {
        name: previewName.trim() || "Shared promotion preview",
        description: previewDescription.trim() || undefined,
        selected_object_ids: selectedObjectIds,
        selected_normalizations: selectedNormalizationKeys
          .map((key) => {
            const [objectId, kind] = key.split("::");
            return objectId && kind ? { object_id: objectId, kind } : null;
          })
          .filter((item): item is { object_id: string; kind: string } => item !== null),
      });
      setPreviewChangeSet(response);
      setLatestExport(null);
      setMessage({
        tone: "success",
        text: `Generated preview change set ${response.id}.`,
      });
    } catch (caught) {
      if (handlePotentialUnauthorized(caught)) {
        return;
      }
      setMessage({
        tone: "error",
        text:
          caught instanceof Error
            ? caught.message
            : "Unknown error while generating the preview change set.",
      });
    } finally {
      setPreviewBusy(false);
    }
  }

  async function handleApplyChangeSet() {
    if (!selectedProjectId || !previewChangeSet) {
      return;
    }

    setApplyBusy(true);

    try {
      const applied = await applyChangeSet(selectedProjectId, previewChangeSet.id);
      setPreviewChangeSet(applied);
      await refreshProject(selectedProjectId);
      setMessage({
        tone: "success",
        text: `Applied change set ${applied.id}. Working state is now updated.`,
      });
    } catch (caught) {
      if (handlePotentialUnauthorized(caught)) {
        return;
      }
      setMessage({
        tone: "error",
        text:
          caught instanceof Error
            ? caught.message
            : "Unknown error while applying the preview change set.",
      });
    } finally {
      setApplyBusy(false);
    }
  }

  async function handleExportProject() {
    if (!selectedProjectId) {
      return;
    }

    setExportBusy(true);

    try {
      const exported = await exportProject(
        selectedProjectId,
        previewChangeSet?.status === "applied" ? { change_set_id: previewChangeSet.id } : {},
      );
      setLatestExport(exported);
      setMessage({
        tone: "success",
        text: `Generated export ${exported.filename}.`,
      });
    } catch (caught) {
      if (handlePotentialUnauthorized(caught)) {
        return;
      }
      setMessage({
        tone: "error",
        text:
          caught instanceof Error
            ? caught.message
            : "Unknown error while generating the export artifact.",
      });
    } finally {
      setExportBusy(false);
    }
  }

  function toggleObjectSelection(objectId: string) {
    setSelectedObjectIds((current) =>
      current.includes(objectId)
        ? current.filter((item) => item !== objectId)
        : [...current, objectId],
    );
  }

  function toggleNormalizationSelection(suggestion: NormalizationSuggestion) {
    const key = `${suggestion.object_id}::${suggestion.kind}`;
    setSelectedNormalizationKeys((current) =>
      current.includes(key) ? current.filter((item) => item !== key) : [...current, key],
    );
  }

  function handlePotentialUnauthorized(caught: unknown) {
    if (!(caught instanceof Error) || !caught.message.startsWith("401 ")) {
      return false;
    }

    setSession(null);
    resetWorkbenchState();
    setMessage({
      tone: "error",
      text: "Your session expired or is no longer valid. Please sign in again.",
    });
    return true;
  }

  function resetProjectView() {
    setSelectedProject(null);
    clearActionState();
  }

  function clearActionState() {
    setAnalysis(null);
    setPreviewChangeSet(null);
    setLatestExport(null);
    setSelectedObjectIds([]);
    setSelectedNormalizationKeys([]);
  }

  function resetWorkbenchState() {
    setUsers([]);
    setProjects([]);
    setSelectedProjectId(null);
    setSelectedProject(null);
    clearActionState();
  }

  const selectedAppliedChangeSet =
    previewChangeSet?.status === "applied" ? previewChangeSet.id : undefined;

  return (
    <main className="workbench-root">
      {message ? (
        <section className={`message-banner message-${message.tone}`}>{message.text}</section>
      ) : null}

      {!session ? (
        <>
          <section className="hero-panel">
            <div className="hero-brand">
              <img src="/branding/logo-readme.png" alt="Frying-PAN logo" className="hero-logo" />
              <div>
                <div className="hero-kicker">Login Portal</div>
                <h1 className="hero-title">Panorama review, merge planning, and export.</h1>
                <p className="hero-copy">
                  Sign in with a local account to access the Frying-PAN workbench. Panorama
                  parsing, dependency analysis, and merge planning remain backend-owned.
                </p>
              </div>
            </div>
          </section>

          <AuthPanel busy={authBusy || initialBusy} onLogin={handleLogin} />
        </>
      ) : session.password_change_required ? (
        <>
          <section className="hero-panel">
            <div className="hero-brand">
              <img src="/branding/logo-readme.png" alt="Frying-PAN logo" className="hero-logo" />
              <div>
                <div className="hero-kicker">First Login</div>
                <h1 className="hero-title">Finish account setup before entering the workbench.</h1>
                <p className="hero-copy">
                  This local account is still using a temporary password. Change it now to unlock
                  projects, uploads, analysis, and export workflows.
                </p>
                <div className="session-strip">
                  <div>
                    Signed in as <strong>{session.user.display_name}</strong> (@
                    {session.user.username})
                  </div>
                  <button type="button" className="secondary-button" onClick={handleLogout}>
                    Sign out
                  </button>
                </div>
              </div>
            </div>
          </section>

          <PasswordChangePanel
            busy={authBusy || initialBusy}
            username={session.user.username}
            onSubmit={handleChangePassword}
          />
        </>
      ) : (
        <>
          <section className="hero-panel">
            <div className="hero-brand">
              <img src="/branding/logo-readme.png" alt="Frying-PAN logo" className="hero-logo" />
              <div>
                <div className="hero-kicker">Workbench</div>
                <h1 className="hero-title">Review sources, preview changes, and export safely.</h1>
                <p className="hero-copy">
                  The browser stays focused on operator workflow. Panorama semantics, dependency
                  handling, and merge planning continue to live in the backend.
                </p>
                <div className="session-strip">
                  <div>
                    Signed in as <strong>{session.user.display_name}</strong> (@
                    {session.user.username})
                  </div>
                  <div className="session-strip-meta">
                    {session.user.role} • session until {formatTimestamp(session.session_expires_at)}
                  </div>
                  <button type="button" className="secondary-button" onClick={handleLogout}>
                    Sign out
                  </button>
                </div>
              </div>
            </div>
          </section>

          {session.user.role === "admin" ? (
            <AdminUserPanel
              currentUserId={session.user.id}
              users={users}
              busy={authBusy}
              onCreate={handleCreateLocalUser}
              onToggleStatus={handleToggleUserStatus}
            />
          ) : null}

          <section className="workbench-layout">
            <aside className="sidebar-stack">
              <section className="workbench-panel">
                <div className="panel-header">
                  <div>
                    <div className="panel-kicker">Project Setup</div>
                    <h2>Create Project</h2>
                  </div>
                </div>
                <CreateProjectForm onCreate={handleCreate} disabled={initialBusy} />
              </section>

              <section className="workbench-panel">
                <div className="panel-header">
                  <div>
                    <div className="panel-kicker">Project Browser</div>
                    <h2>Projects</h2>
                  </div>
                </div>
                {projects.length === 0 ? (
                  <div className="empty-state">
                    No accessible projects yet. Create one to start collecting Panorama XML
                    sources.
                  </div>
                ) : (
                  <div className="project-list">
                    {projects.map((project) => (
                      <button
                        key={project.id}
                        type="button"
                        className={`project-list-item ${
                          project.id === selectedProjectId ? "project-list-item-active" : ""
                        }`}
                        onClick={() => {
                          setSelectedProjectId(project.id);
                          clearActionState();
                        }}
                      >
                        <div className="project-list-title">{project.name}</div>
                        <div className="project-list-meta">
                          {project.description || "No description yet."}
                        </div>
                        <div className="project-list-timestamp">
                          Updated {formatTimestamp(project.updated_at)}
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </section>
            </aside>

            <section className="main-stack">
            {!selectedProject ? (
              <section className="workbench-panel">
                <div className="empty-state">
                  {projectBusy
                    ? "Loading selected project..."
                    : "Select a project to inspect sources, run analysis, and drive the merge workflow."}
                </div>
              </section>
            ) : (
              <>
                <section className="workbench-panel">
                  <div className="panel-header">
                    <div>
                      <div className="panel-kicker">Project Detail</div>
                      <h2>{selectedProject.name}</h2>
                      <p className="panel-copy">
                        {selectedProject.description ||
                          "No project description yet. Use this space to keep migration intent visible."}
                      </p>
                    </div>
                  </div>

                  <div className="detail-grid">
                    <div className="detail-card">
                      <span className="detail-label">Status</span>
                      <strong>{selectedProject.status}</strong>
                    </div>
                    <div className="detail-card">
                      <span className="detail-label">Sources</span>
                      <strong>{selectedProject.sources.length}</strong>
                    </div>
                    <div className="detail-card">
                      <span className="detail-label">Events</span>
                      <strong>{selectedProject.events.length}</strong>
                    </div>
                    <div className="detail-card">
                      <span className="detail-label">Updated</span>
                      <strong>{formatTimestamp(selectedProject.updated_at)}</strong>
                    </div>
                  </div>
                </section>

                <section className="two-column-grid">
                  <section className="workbench-panel">
                    <div className="panel-header">
                      <div>
                        <div className="panel-kicker">Source Intake</div>
                        <h2>Upload XML</h2>
                      </div>
                    </div>
                    <UploadSourceForm projectId={selectedProject.id} onUpload={handleUpload} />
                  </section>

                  <section className="workbench-panel">
                    <div className="panel-header">
                      <div>
                        <div className="panel-kicker">Audit</div>
                        <h2>Recent Events</h2>
                      </div>
                    </div>
                    {selectedProject.events.length === 0 ? (
                      <div className="empty-state">No project events recorded yet.</div>
                    ) : (
                      <div className="event-list">
                        {selectedProject.events.slice(0, 6).map((event) => (
                          <div key={event.id} className="event-row">
                            <div className="event-name">{event.event_type}</div>
                            <div className="event-meta">
                              {formatTimestamp(event.created_at)}
                              {event.actor_user_id ? ` • actor ${shortId(event.actor_user_id)}` : ""}
                            </div>
                            {event.payload ? <div className="event-payload">{event.payload}</div> : null}
                          </div>
                        ))}
                      </div>
                    )}
                  </section>
                </section>

                <section className="workbench-panel">
                  <div className="panel-header">
                    <div>
                      <div className="panel-kicker">Source Inventory</div>
                      <h2>Imported Sources</h2>
                    </div>
                  </div>

                  {selectedProject.sources.length === 0 ? (
                    <div className="empty-state">
                      No sources uploaded yet. Raw XML files remain backend-owned and are stored on
                      disk outside the browser.
                    </div>
                  ) : (
                    <div className="source-grid">
                      {selectedProject.sources.map((source) => (
                        <article key={source.id} className="source-card">
                          <div className="source-title">{source.label}</div>
                          <div className="source-meta">
                            {source.filename} • {source.source_type} • {source.parse_status}
                          </div>
                          <div className="source-meta">
                            Imported {formatTimestamp(source.imported_at)}
                            {source.imported_by_user_id
                              ? ` • actor ${shortId(source.imported_by_user_id)}`
                              : ""}
                          </div>
                          <div className="source-path">{shortSha(source.file_sha256)}</div>
                        </article>
                      ))}
                    </div>
                  )}
                </section>

                <section className="workbench-panel">
                  <div className="panel-header">
                    <div>
                      <div className="panel-kicker">Analysis</div>
                      <h2>Duplicate, normalization, and promotion review</h2>
                      <p className="panel-copy">
                        Filters only scope the backend report. They do not re-implement any config
                        logic in the browser.
                      </p>
                    </div>
                  </div>

                  <div className="filter-grid">
                    <label className="field-stack">
                      <span>Source filter</span>
                      <select
                        value={analysisFilters.source_id}
                        onChange={(event) =>
                          setAnalysisFilters((current) => ({
                            ...current,
                            source_id: event.target.value,
                          }))
                        }
                      >
                        <option value="">All imported sources</option>
                        {selectedProject.sources.map((source) => (
                          <option key={source.id} value={source.id}>
                            {source.label}
                          </option>
                        ))}
                      </select>
                    </label>

                    <label className="field-stack">
                      <span>Object type</span>
                      <select
                        value={analysisFilters.object_type}
                        onChange={(event) =>
                          setAnalysisFilters((current) => ({
                            ...current,
                            object_type: event.target.value,
                          }))
                        }
                      >
                        {objectTypeOptions.map((option) => (
                          <option key={option.value || "all"} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                    </label>

                    <label className="field-stack">
                      <span>Scope path</span>
                      <input
                        value={analysisFilters.scope_path}
                        onChange={(event) =>
                          setAnalysisFilters((current) => ({
                            ...current,
                            scope_path: event.target.value,
                          }))
                        }
                        placeholder="shared/device-group:Device-Group-1"
                      />
                    </label>

                    <div className="filter-actions">
                      <button
                        type="button"
                        className="action-button"
                        onClick={handleRunAnalysis}
                        disabled={analysisBusy || projectBusy}
                      >
                        {analysisBusy ? "Running analysis..." : "Run analysis"}
                      </button>
                    </div>
                  </div>

                  {!analysis ? (
                    <div className="empty-state">
                      Run analysis to populate duplicate findings, normalization suggestions, and
                      promotion assessments for this project.
                    </div>
                  ) : (
                    <div className="result-stack">
                      <div className="summary-grid">
                        <div className="summary-card">
                          <span>Duplicate names</span>
                          <strong>{analysis.report.duplicate_name_findings.length}</strong>
                        </div>
                        <div className="summary-card">
                          <span>Duplicate values</span>
                          <strong>{analysis.report.duplicate_value_findings.length}</strong>
                        </div>
                        <div className="summary-card">
                          <span>Normalization suggestions</span>
                          <strong>{analysis.report.normalization_suggestions.length}</strong>
                        </div>
                        <div className="summary-card">
                          <span>Promotion blockers</span>
                          <strong>{analysis.report.promotion_blockers.length}</strong>
                        </div>
                      </div>

                      <div className="three-column-grid">
                        <section className="result-panel">
                          <h3>Duplicate names</h3>
                          {analysis.report.duplicate_name_findings.length === 0 ? (
                            <p className="empty-inline">
                              No duplicate-name findings for this filter set.
                            </p>
                          ) : (
                            analysis.report.duplicate_name_findings.map((finding) => (
                              <article
                                key={`${finding.object_type}-${finding.key}`}
                                className="finding-card"
                              >
                                <div className="finding-title">
                                  {finding.object_type} • {finding.key}
                                </div>
                                <ul className="compact-list">
                                  {finding.items.map((item) => (
                                    <li key={item.id}>
                                      <strong>{item.object_name}</strong>
                                      <span>{item.scope_path}</span>
                                    </li>
                                  ))}
                                </ul>
                              </article>
                            ))
                          )}
                        </section>

                        <section className="result-panel">
                          <h3>Duplicate values</h3>
                          {analysis.report.duplicate_value_findings.length === 0 ? (
                            <p className="empty-inline">
                              No duplicate-value findings for this filter set.
                            </p>
                          ) : (
                            analysis.report.duplicate_value_findings.map((finding, index) => (
                              <article
                                key={`${finding.object_type}-${finding.key}-${index}`}
                                className="finding-card"
                              >
                                <div className="finding-title">
                                  {finding.object_type} • {truncateMiddle(finding.key, 42)}
                                </div>
                                <div className="code-pill">
                                  {renderPayloadSummary(finding.normalized_payload)}
                                </div>
                                <ul className="compact-list">
                                  {finding.items.map((item) => (
                                    <li key={item.id}>
                                      <strong>{item.object_name}</strong>
                                      <span>{item.scope_path}</span>
                                    </li>
                                  ))}
                                </ul>
                              </article>
                            ))
                          )}
                        </section>

                        <section className="result-panel">
                          <h3>Normalization suggestions</h3>
                          {analysis.report.normalization_suggestions.length === 0 ? (
                            <p className="empty-inline">No normalization suggestions right now.</p>
                          ) : (
                            analysis.report.normalization_suggestions.map((suggestion) => {
                              const key = `${suggestion.object_id}::${suggestion.kind}`;
                              return (
                                <label key={key} className="selectable-card">
                                  <input
                                    type="checkbox"
                                    checked={selectedNormalizationKeys.includes(key)}
                                    onChange={() => toggleNormalizationSelection(suggestion)}
                                  />
                                  <div>
                                    <div className="finding-title">{suggestion.object_name}</div>
                                    <div className="selectable-meta">{suggestion.scope_path}</div>
                                    <div className="code-pill">
                                      {suggestion.original_value} → {suggestion.suggested_value}
                                    </div>
                                  </div>
                                </label>
                              );
                            })
                          )}
                        </section>
                      </div>

                      <div className="two-column-grid">
                        <section className="result-panel">
                          <h3>Promotion candidates</h3>
                          {analysis.report.promotion_candidates.length === 0 ? (
                            <p className="empty-inline">
                              No promotable candidates in the current report.
                            </p>
                          ) : (
                            analysis.report.promotion_candidates.map((candidate) => (
                              <label key={candidate.object_id} className="selectable-card">
                                <input
                                  type="checkbox"
                                  checked={selectedObjectIds.includes(candidate.object_id)}
                                  onChange={() => toggleObjectSelection(candidate.object_id)}
                                />
                                <div>
                                  <div className="finding-title">
                                    {candidate.object_name}{" "}
                                    <span className="muted-tag">{candidate.object_type}</span>
                                  </div>
                                  <div className="selectable-meta">{candidate.scope_path}</div>
                                  {candidate.dependency_targets.length > 0 ? (
                                    <div className="selectable-meta">
                                      Dependencies: {candidate.dependency_targets.join(", ")}
                                    </div>
                                  ) : null}
                                </div>
                              </label>
                            ))
                          )}
                        </section>

                        <section className="result-panel">
                          <h3>Promotion blockers</h3>
                          {analysis.report.promotion_blockers.length === 0 ? (
                            <p className="empty-inline">No blockers reported in the current report.</p>
                          ) : (
                            analysis.report.promotion_blockers.map((blocker) => (
                              <article key={blocker.object_id} className="finding-card blocked-card">
                                <div className="finding-title">
                                  {blocker.object_name}{" "}
                                  <span className="muted-tag">{blocker.object_type}</span>
                                </div>
                                <div className="selectable-meta">{blocker.scope_path}</div>
                                <div className="pill-row">
                                  {blocker.blockers.map((item) => (
                                    <span key={item} className="warning-pill">
                                      {item}
                                    </span>
                                  ))}
                                </div>
                              </article>
                            ))
                          )}
                        </section>
                      </div>
                    </div>
                  )}
                </section>

                <section className="two-column-grid">
                  <section className="workbench-panel">
                    <div className="panel-header">
                      <div>
                        <div className="panel-kicker">Change Preview</div>
                        <h2>Preview and apply</h2>
                        <p className="panel-copy">
                          Selected candidates and normalization suggestions are sent directly to the
                          backend preview planner.
                        </p>
                      </div>
                    </div>

                    <div className="field-grid">
                      <label className="field-stack">
                        <span>Preview name</span>
                        <input
                          value={previewName}
                          onChange={(event) => setPreviewName(event.target.value)}
                          placeholder="Shared promotion preview"
                        />
                      </label>

                      <label className="field-stack">
                        <span>Description</span>
                        <textarea
                          value={previewDescription}
                          onChange={(event) => setPreviewDescription(event.target.value)}
                          rows={4}
                          placeholder="Explain what you want this preview to stage."
                        />
                      </label>
                    </div>

                    <div className="detail-grid">
                      <div className="detail-card">
                        <span className="detail-label">Selected promotions</span>
                        <strong>{selectedObjectIds.length}</strong>
                      </div>
                      <div className="detail-card">
                        <span className="detail-label">Selected normalizations</span>
                        <strong>{selectedNormalizationKeys.length}</strong>
                      </div>
                    </div>

                    <div className="button-row">
                      <button
                        type="button"
                        className="action-button"
                        onClick={handlePreviewChangeSet}
                        disabled={previewBusy || !analysis}
                      >
                        {previewBusy ? "Generating preview..." : "Create preview change set"}
                      </button>
                      <button
                        type="button"
                        className="secondary-button"
                        onClick={handleApplyChangeSet}
                        disabled={
                          applyBusy ||
                          !previewChangeSet ||
                          previewChangeSet.status === "applied" ||
                          ((previewChangeSet.operations_payload.blocked_objects?.length ?? 0) > 0)
                        }
                      >
                        {applyBusy ? "Applying..." : "Apply preview"}
                      </button>
                    </div>

                    {!previewChangeSet ? (
                      <div className="empty-state">
                        No preview generated yet. Run analysis, select objects, and create a change
                        set preview first.
                      </div>
                    ) : (
                      <div className="result-stack">
                        <div className="summary-grid">
                          <div className="summary-card">
                            <span>Status</span>
                            <strong>{previewChangeSet.status}</strong>
                          </div>
                          <div className="summary-card">
                            <span>Object ops</span>
                            <strong>
                              {numberFromSummary(
                                previewChangeSet.preview_summary,
                                "planned_object_count",
                              )}
                            </strong>
                          </div>
                          <div className="summary-card">
                            <span>Rewrites</span>
                            <strong>
                              {numberFromSummary(
                                previewChangeSet.preview_summary,
                                "reference_rewrite_count",
                              )}
                            </strong>
                          </div>
                          <div className="summary-card">
                            <span>Blocked</span>
                            <strong>
                              {numberFromSummary(
                                previewChangeSet.preview_summary,
                                "blocked_object_count",
                              )}
                            </strong>
                          </div>
                        </div>

                        <div className="two-column-grid">
                          <section className="result-panel">
                            <h3>Object operations</h3>
                            {renderOperationList(previewChangeSet.operations_payload.object_operations)}
                          </section>

                          <section className="result-panel">
                            <h3>Reference rewrites</h3>
                            {renderOperationList(
                              previewChangeSet.operations_payload.reference_rewrites,
                            )}
                          </section>
                        </div>

                        <div className="two-column-grid">
                          <section className="result-panel">
                            <h3>Normalization operations</h3>
                            {renderOperationList(
                              previewChangeSet.operations_payload.normalization_operations,
                            )}
                          </section>

                          <section className="result-panel">
                            <h3>Blocked objects</h3>
                            {renderOperationList(previewChangeSet.operations_payload.blocked_objects)}
                          </section>
                        </div>
                      </div>
                    )}
                  </section>

                  <section className="workbench-panel">
                    <div className="panel-header">
                      <div>
                        <div className="panel-kicker">Export</div>
                        <h2>Generate XML artifact</h2>
                        <p className="panel-copy">
                          Export serializes the backend working state. If the current preview was
                          applied, the export is linked back to that change set.
                        </p>
                      </div>
                    </div>

                    <div className="button-row">
                      <button
                        type="button"
                        className="action-button"
                        onClick={handleExportProject}
                        disabled={exportBusy}
                      >
                        {exportBusy ? "Generating export..." : "Generate export"}
                      </button>
                    </div>

                    {selectedAppliedChangeSet ? (
                      <div className="code-pill">
                        Using applied change set {selectedAppliedChangeSet}
                      </div>
                    ) : (
                      <div className="empty-inline">
                        No applied preview selected. Export will serialize the current project
                        working state without attaching a change set reference.
                      </div>
                    )}

                    {!latestExport ? (
                      <div className="empty-state">No export generated in this session yet.</div>
                    ) : (
                      <div className="result-stack">
                        <div className="detail-grid">
                          <div className="detail-card">
                            <span className="detail-label">Filename</span>
                            <strong>{latestExport.filename}</strong>
                          </div>
                          <div className="detail-card">
                            <span className="detail-label">Status</span>
                            <strong>{latestExport.export_status}</strong>
                          </div>
                          <div className="detail-card">
                            <span className="detail-label">Created</span>
                            <strong>{formatTimestamp(latestExport.created_at)}</strong>
                          </div>
                        </div>
                        <div className="code-block">{latestExport.storage_path}</div>
                        <div className="code-pill">{shortSha(latestExport.file_sha256)}</div>
                      </div>
                    )}
                  </section>
                </section>
              </>
            )}
            </section>
          </section>
        </>
      )}
    </main>
  );
}

function compactFilters(filters: Record<string, string>): AnalysisFilters {
  const result: AnalysisFilters = {};
  if (filters.source_id.trim()) {
    result.source_id = filters.source_id.trim();
  }
  if (filters.object_type.trim()) {
    result.object_type = filters.object_type.trim();
  }
  if (filters.scope_path.trim()) {
    result.scope_path = filters.scope_path.trim();
  }
  return result;
}

function formatTimestamp(value: string) {
  return new Date(value).toLocaleString();
}

function shortSha(value: string) {
  return `${value.slice(0, 12)}...`;
}

function shortId(value: string) {
  return value.slice(0, 8);
}

function truncateMiddle(value: string, maxLength: number) {
  if (value.length <= maxLength) {
    return value;
  }

  const headLength = Math.floor((maxLength - 3) / 2);
  const tailLength = maxLength - 3 - headLength;
  return `${value.slice(0, headLength)}...${value.slice(-tailLength)}`;
}

function renderPayloadSummary(payload?: Record<string, unknown> | null) {
  if (!payload) {
    return "No normalized payload";
  }

  return Object.entries(payload)
    .slice(0, 3)
    .map(([key, value]) => `${key}: ${String(value)}`)
    .join(" • ");
}

function numberFromSummary(summary: Record<string, unknown>, key: string) {
  const value = summary[key];
  return typeof value === "number" ? value : 0;
}

function renderOperationList(items?: Record<string, unknown>[]) {
  if (!items || items.length === 0) {
    return <p className="empty-inline">None in this preview.</p>;
  }

  return (
    <div className="operation-list">
      {items.map((item, index) => (
        <article key={`${item.object_id ?? item.reference_id ?? index}`} className="finding-card">
          <div className="finding-title">
            {String(item.object_name ?? item.owner_object_name ?? item.operation ?? "operation")}
          </div>
          <div className="code-block">{JSON.stringify(item, null, 2)}</div>
        </article>
      ))}
    </div>
  );
}
