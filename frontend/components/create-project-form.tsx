"use client";

import type { CSSProperties, FormEvent } from "react";
import { useEffect, useState } from "react";

type CreateProjectFormProps = {
  onCreate: (payload: {
    name: string;
    description?: string;
  }) => Promise<void>;
  submitLabel?: string;
  heading?: string;
  copy?: string;
  initialName?: string;
  initialDescription?: string;
  onCancel?: () => void;
  disabled?: boolean;
};

export function CreateProjectForm({
  onCreate,
  submitLabel = "Create project",
  heading,
  copy,
  initialName = "",
  initialDescription = "",
  onCancel,
  disabled = false,
}: CreateProjectFormProps) {
  const [name, setName] = useState(initialName);
  const [description, setDescription] = useState(initialDescription);

  useEffect(() => {
    setName(initialName);
    setDescription(initialDescription);
  }, [initialDescription, initialName]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!name.trim()) {
      return;
    }

    await onCreate({
      name: name.trim(),
      description: description.trim() || undefined,
    });

    if (!initialName && !initialDescription) {
      setName("");
      setDescription("");
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      style={{
        display: "grid",
        gap: 12,
        padding: 0,
      }}
    >
      {heading ? (
        <div className="profile-section-header">
          <h2>{heading}</h2>
          {copy ? <p className="panel-copy">{copy}</p> : null}
        </div>
      ) : null}
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

      <div className="button-row">
        <button disabled={disabled} type="submit" style={buttonStyle}>
          {disabled ? "Working..." : submitLabel}
        </button>
        {onCancel ? (
          <button type="button" disabled={disabled} className="secondary-button" onClick={onCancel}>
            Cancel
          </button>
        ) : null}
      </div>
    </form>
  );
}

const inputStyle: CSSProperties = {
  width: "100%",
  marginTop: 8,
  borderRadius: 0,
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
