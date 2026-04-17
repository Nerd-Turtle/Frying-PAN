"use client";

import type { CSSProperties, FormEvent } from "react";
import { useState } from "react";

type CreateProjectFormProps = {
  onCreate: (payload: { name: string; description?: string }) => Promise<void>;
  disabled?: boolean;
};

export function CreateProjectForm({
  onCreate,
  disabled = false,
}: CreateProjectFormProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!name.trim()) {
      return;
    }

    await onCreate({
      name: name.trim(),
      description: description.trim() || undefined,
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
        Create project
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
