"use client";

import type { CSSProperties, FormEvent } from "react";
import { useEffect, useState } from "react";

type CreateProjectFormProps = {
  organizations?: Array<{ id: string; name: string }>;
  onCreate: (payload: {
    name: string;
    description?: string;
    organization_id?: string;
  }) => Promise<void>;
  disabled?: boolean;
};

export function CreateProjectForm({
  organizations,
  onCreate,
  disabled = false,
}: CreateProjectFormProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [organizationId, setOrganizationId] = useState(organizations?.[0]?.id ?? "");

  useEffect(() => {
    if (!organizations?.length) {
      setOrganizationId("");
      return;
    }

    setOrganizationId((current) =>
      current && organizations.some((organization) => organization.id === current)
        ? current
        : organizations[0].id,
    );
  }, [organizations]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!name.trim()) {
      return;
    }

    await onCreate({
      name: name.trim(),
      description: description.trim() || undefined,
      organization_id: organizationId || undefined,
    });

    setName("");
    setDescription("");
  }

  return (
    <form
      onSubmit={handleSubmit}
      style={{
        display: "grid",
        gap: 12,
        padding: 18,
        background: "var(--panel)",
        border: "1px solid var(--line)",
        borderRadius: 18,
      }}
    >
      <div>
        {organizations && organizations.length > 0 ? (
          <div>
            <label htmlFor="project-organization" style={{ display: "block", fontWeight: 600 }}>
              Organization
            </label>
            <select
              id="project-organization"
              value={organizationId}
              onChange={(event) => setOrganizationId(event.target.value)}
              disabled={disabled}
              style={inputStyle}
            >
              {organizations.map((organization) => (
                <option key={organization.id} value={organization.id}>
                  {organization.name}
                </option>
              ))}
            </select>
          </div>
        ) : null}
      </div>

      <div>
        <label htmlFor="project-name" style={{ display: "block", fontWeight: 600 }}>
          Project name
        </label>
        <input
          id="project-name"
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="Migration Sprint A"
          disabled={disabled}
          style={inputStyle}
        />
      </div>

      <div>
        <label htmlFor="project-description" style={{ display: "block", fontWeight: 600 }}>
          Description
        </label>
        <textarea
          id="project-description"
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          placeholder="Optional context about the source Panorama instances or migration goal."
          disabled={disabled}
          rows={4}
          style={{ ...inputStyle, resize: "vertical" }}
        />
      </div>

      <button disabled={disabled} type="submit" style={buttonStyle}>
        {disabled ? "Working..." : "Create project"}
      </button>
    </form>
  );
}

const inputStyle: CSSProperties = {
  width: "100%",
  marginTop: 8,
  borderRadius: 12,
  border: "1px solid var(--line)",
  padding: "12px 14px",
  background: "var(--panel-strong)",
};

const buttonStyle: CSSProperties = {
  border: "none",
  borderRadius: 999,
  padding: "12px 16px",
  background: "var(--accent)",
  color: "white",
  fontWeight: 700,
};
