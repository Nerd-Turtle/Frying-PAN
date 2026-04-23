"use client";

import type { CSSProperties, FormEvent } from "react";
import { useEffect, useMemo, useState } from "react";

import type { UserDirectoryEntry } from "@/src/types";

type CreateProjectFormProps = {
  availableUsers: UserDirectoryEntry[];
  onCreate: (payload: {
    name: string;
    description?: string;
    visibility: "public" | "private";
    contributor_usernames: string[];
  }) => Promise<void>;
  submitLabel?: string;
  heading?: string;
  copy?: string;
  initialName?: string;
  initialDescription?: string;
  initialVisibility?: "public" | "private";
  initialContributorUsernames?: string[];
  onCancel?: () => void;
  disabled?: boolean;
};

export function CreateProjectForm({
  availableUsers,
  onCreate,
  submitLabel = "Create project",
  heading,
  copy,
  initialName = "",
  initialDescription = "",
  initialVisibility = "public",
  initialContributorUsernames = [],
  onCancel,
  disabled = false,
}: CreateProjectFormProps) {
  const [name, setName] = useState(initialName);
  const [description, setDescription] = useState(initialDescription);
  const [visibility, setVisibility] = useState<"public" | "private">(initialVisibility);
  const [selectedContributorUsernames, setSelectedContributorUsernames] = useState(
    normalizeContributorUsernames(initialContributorUsernames),
  );
  const [contributorQuery, setContributorQuery] = useState("");

  useEffect(() => {
    setName(initialName);
    setDescription(initialDescription);
    setVisibility(initialVisibility);
    setSelectedContributorUsernames(normalizeContributorUsernames(initialContributorUsernames));
    setContributorQuery("");
  }, [initialContributorUsernames, initialDescription, initialName, initialVisibility]);

  const filteredUsers = useMemo(() => {
    const query = contributorQuery.trim().toLowerCase();
    if (!query) {
      return availableUsers;
    }

    return availableUsers.filter((user) =>
      `${user.display_name} ${user.username}`.toLowerCase().includes(query),
    );
  }, [availableUsers, contributorQuery]);

  const selectedContributors = useMemo(() => {
    const availableByUsername = new Map(
      availableUsers.map((user) => [user.username.toLowerCase(), user] as const),
    );

    return selectedContributorUsernames.map((username) => {
      const matched = availableByUsername.get(username.toLowerCase());
      return {
        username,
        displayName: matched?.display_name ?? username,
      };
    });
  }, [availableUsers, selectedContributorUsernames]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!name.trim()) {
      return;
    }

    await onCreate({
      name: name.trim(),
      description: description.trim() || undefined,
      visibility,
      contributor_usernames: visibility === "private" ? selectedContributorUsernames : [],
    });

    if (!initialName && !initialDescription && initialContributorUsernames.length === 0) {
      setName("");
      setDescription("");
      setVisibility("public");
      setSelectedContributorUsernames([]);
      setContributorQuery("");
    }
  }

  function toggleContributor(username: string) {
    const normalized = username.trim().toLowerCase();
    if (!normalized) {
      return;
    }

    setSelectedContributorUsernames((current) =>
      current.includes(normalized)
        ? current.filter((value) => value !== normalized)
        : [...current, normalized],
    );
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

      <div>
        <label htmlFor="project-visibility" style={{ display: "block", fontWeight: 600 }}>
          Visibility
        </label>
        <select
          id="project-visibility"
          value={visibility}
          onChange={(event) => setVisibility(event.target.value as "public" | "private")}
          disabled={disabled}
          style={inputStyle}
        >
          <option value="public">Public</option>
          <option value="private">Private</option>
        </select>
      </div>

      {visibility === "private" ? (
        <div className="contributor-selector">
          <div>
            <label htmlFor="project-contributors-search" style={{ display: "block", fontWeight: 600 }}>
              Contributors
            </label>
            <input
              id="project-contributors-search"
              value={contributorQuery}
              onChange={(event) => setContributorQuery(event.target.value)}
              placeholder="Search users by name or username"
              disabled={disabled}
              style={inputStyle}
            />
          </div>

          <div className="contributor-selector-meta">
            {selectedContributorUsernames.length > 0
              ? `${selectedContributorUsernames.length} contributor${
                  selectedContributorUsernames.length === 1 ? "" : "s"
                } selected.`
              : "Select one or more contributors. Owners can always contribute."}
          </div>

          {selectedContributors.length > 0 ? (
            <div className="contributor-chip-list">
              {selectedContributors.map((contributor) => (
                <button
                  key={contributor.username}
                  type="button"
                  className="contributor-chip"
                  onClick={() => toggleContributor(contributor.username)}
                  disabled={disabled}
                >
                  <span>
                    {contributor.displayName}
                    {contributor.displayName.toLowerCase() !== contributor.username.toLowerCase()
                      ? ` (${contributor.username})`
                      : ""}
                  </span>
                  <span aria-hidden="true">×</span>
                </button>
              ))}
            </div>
          ) : null}

          <div className="contributor-option-list" role="listbox" aria-multiselectable="true">
            {filteredUsers.length > 0 ? (
              filteredUsers.map((user) => {
                const checked = selectedContributorUsernames.includes(user.username.toLowerCase());

                return (
                  <label key={user.id} className="contributor-option">
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => toggleContributor(user.username)}
                      disabled={disabled}
                    />
                    <span className="contributor-option-copy">
                      <strong>{user.display_name}</strong>
                      <span>@{user.username}</span>
                    </span>
                  </label>
                );
              })
            ) : (
              <div className="empty-inline">No users match the current search.</div>
            )}
          </div>
        </div>
      ) : (
        <p className="panel-copy">
          Public projects can be opened and worked on by any signed-in user.
        </p>
      )}

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

function normalizeContributorUsernames(usernames: string[]) {
  const seen = new Set<string>();
  const normalized: string[] = [];

  for (const username of usernames) {
    const value = username.trim().toLowerCase();
    if (!value || seen.has(value)) {
      continue;
    }
    seen.add(value);
    normalized.push(value);
  }

  return normalized;
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
