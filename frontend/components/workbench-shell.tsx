"use client";

import { useEffect, useState } from "react";

import { CreateProjectForm } from "@/components/create-project-form";
import { StatusCard } from "@/components/status-card";
import { UploadSourceForm } from "@/components/upload-source-form";
import { createProject, getHealth, listProjects, uploadSource } from "@/lib/api";
import type { HealthResponse, Project } from "@/src/types";

export function WorkbenchShell() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setBusy(true);
    setError(null);

    try {
      const [healthResponse, projectResponse] = await Promise.all([
        getHealth(),
        listProjects(),
      ]);
      setHealth(healthResponse);
      setProjects(projectResponse);
    } catch (caught) {
      const message =
        caught instanceof Error ? caught.message : "Unknown error while loading the workbench.";
      setError(message);
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function handleCreate(payload: { name: string; description?: string }) {
    await createProject(payload);
    await refresh();
  }

  async function handleUpload(projectId: string, file: File) {
    await uploadSource(projectId, file);
    await refresh();
  }

  return (
    <main
      style={{
        maxWidth: 1180,
        margin: "0 auto",
        display: "grid",
        gap: 24,
      }}
    >
      <section
        style={{
          background: "var(--panel)",
          border: "1px solid var(--line)",
          borderRadius: 28,
          padding: 28,
          boxShadow: "var(--shadow)",
        }}
      >
        <div style={{ color: "var(--accent)", fontWeight: 700, letterSpacing: 1.2 }}>
          FRYING-PAN
        </div>
        <h1 style={{ margin: "10px 0 12px", fontSize: "clamp(2rem, 5vw, 4rem)" }}>
          Panorama merge workbench, scaffolded honestly.
        </h1>
        <p style={{ maxWidth: 780, color: "var(--muted)", fontSize: 18, lineHeight: 1.6 }}>
          This starter UI is intentionally focused on project setup, source upload, and workflow
          placeholders. Panorama parsing, normalization, diffing, merge semantics, dependency
          analysis, and export generation belong in the backend.
        </p>
      </section>

      <section
        style={{
          display: "grid",
          gap: 16,
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
        }}
      >
        <StatusCard
          label="Backend status"
          value={health?.status ?? (busy ? "loading" : "offline")}
          tone={health?.status === "ok" ? "success" : "warning"}
        />
        <StatusCard label="Projects" value={String(projects.length)} />
        <StatusCard label="Scope" value="MVP scaffold" />
      </section>

      {error ? (
        <section
          style={{
            padding: 18,
            borderRadius: 18,
            border: "1px solid var(--accent)",
            background: "var(--accent-soft)",
          }}
        >
          <strong>Backend connection issue:</strong> {error}
        </section>
      ) : null}

      <section
        style={{
          display: "grid",
          gap: 20,
          gridTemplateColumns: "minmax(280px, 360px) minmax(0, 1fr)",
        }}
      >
        <div>
          <h2 style={{ marginTop: 0 }}>Create Project</h2>
          <CreateProjectForm onCreate={handleCreate} disabled={busy} />
        </div>

        <div
          style={{
            display: "grid",
            gap: 16,
          }}
        >
          <h2 style={{ marginTop: 0 }}>Projects</h2>
          {projects.length === 0 ? (
            <article
              style={{
                padding: 20,
                borderRadius: 18,
                border: "1px dashed var(--line-strong)",
                background: "var(--panel)",
              }}
            >
              No projects yet. Create one to start collecting Panorama XML sources.
            </article>
          ) : (
            projects.map((project) => (
              <article
                key={project.id}
                style={{
                  display: "grid",
                  gap: 16,
                  padding: 20,
                  borderRadius: 20,
                  background: "var(--panel)",
                  border: "1px solid var(--line)",
                  boxShadow: "var(--shadow)",
                }}
              >
                <div>
                  <h3 style={{ margin: 0 }}>{project.name}</h3>
                  <p style={{ margin: "8px 0 0", color: "var(--muted)" }}>
                    {project.description || "No description yet."}
                  </p>
                </div>

                <div style={{ display: "grid", gap: 8 }}>
                  <strong>Uploaded sources</strong>
                  {project.sources && project.sources.length > 0 ? (
                    project.sources.map((source) => (
                      <div
                        key={source.id}
                        style={{
                          padding: "10px 12px",
                          borderRadius: 12,
                          background: "var(--panel-strong)",
                          border: "1px solid var(--line)",
                        }}
                      >
                        <div style={{ fontWeight: 600 }}>{source.label}</div>
                        <div style={{ fontSize: 13, color: "var(--muted)" }}>
                          {source.source_type} • {source.parse_status} •{" "}
                          {new Date(source.imported_at).toLocaleString()}
                        </div>
                      </div>
                    ))
                  ) : (
                    <div style={{ color: "var(--muted)" }}>
                      No sources uploaded yet. Raw XML files will be stored on disk by the backend.
                    </div>
                  )}
                </div>

                <UploadSourceForm projectId={project.id} onUpload={handleUpload} />

                <div
                  style={{
                    display: "grid",
                    gap: 10,
                    gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))",
                  }}
                >
                  {[
                    "Analysis scaffold",
                    "Diff / merge scaffold",
                    "Export scaffold",
                  ].map((label) => (
                    <div
                      key={label}
                      style={{
                        padding: 14,
                        borderRadius: 14,
                        background: "var(--panel-strong)",
                        border: "1px dashed var(--line-strong)",
                        color: "var(--muted)",
                      }}
                    >
                      {label}
                      <div style={{ marginTop: 6, fontSize: 13 }}>
                        TODO: connect to backend workflow endpoints.
                      </div>
                    </div>
                  ))}
                </div>
              </article>
            ))
          )}
        </div>
      </section>
    </main>
  );
}
