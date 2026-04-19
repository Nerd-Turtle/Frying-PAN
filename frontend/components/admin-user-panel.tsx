"use client";

import type { FormEvent } from "react";
import { useState } from "react";

import { formatUserRole } from "@/lib/labels";
import type { UserRecord } from "@/src/types";

type AdminUserPanelProps = {
  currentUserId: string;
  users: UserRecord[];
  busy?: boolean;
  onCreate: (payload: {
    username: string;
    display_name: string;
    password: string;
    role: string;
    must_change_password: boolean;
  }) => Promise<void>;
  onToggleStatus: (user: UserRecord) => Promise<void>;
};

export function AdminUserPanel({
  currentUserId,
  users,
  busy = false,
  onCreate,
  onToggleStatus,
}: AdminUserPanelProps) {
  const [username, setUsername] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("operator");
  const [mustChangePassword, setMustChangePassword] = useState(true);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!username.trim() || !displayName.trim() || !password.trim()) {
      return;
    }

    await onCreate({
      username: username.trim(),
      display_name: displayName.trim(),
      password: password.trim(),
      role,
      must_change_password: mustChangePassword,
    });

    setUsername("");
    setDisplayName("");
    setPassword("");
    setRole("operator");
    setMustChangePassword(true);
  }

  return (
    <section className="workbench-panel">
      <div className="panel-header">
        <div>
          <div className="panel-kicker">Administration</div>
          <h2>Local users</h2>
          <p className="panel-copy">
            Admins create and control local accounts here. Panorama merge semantics still remain in
            the backend workbench layer.
          </p>
        </div>
      </div>

      <div className="two-column-grid">
        <form onSubmit={handleSubmit} className="result-panel">
          <h3>Create local user</h3>
          <label className="field-stack">
            Username
            <input
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              placeholder="operator1"
              disabled={busy}
            />
          </label>
          <label className="field-stack">
            Display name
            <input
              value={displayName}
              onChange={(event) => setDisplayName(event.target.value)}
              placeholder="Operator One"
              disabled={busy}
            />
          </label>
          <label className="field-stack">
            Temporary password
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="At least 8 characters"
              disabled={busy}
            />
          </label>
          <label className="field-stack">
            Role
            <select value={role} onChange={(event) => setRole(event.target.value)} disabled={busy}>
              <option value="operator">Operator</option>
              <option value="admin">Administrator</option>
            </select>
          </label>
          <label className="field-stack checkbox-row">
            <input
              type="checkbox"
              checked={mustChangePassword}
              onChange={(event) => setMustChangePassword(event.target.checked)}
              disabled={busy}
            />
            Require password change on first login
          </label>
          <button type="submit" className="primary-button" disabled={busy}>
            {busy ? "Working..." : "Create user"}
          </button>
        </form>

        <div className="result-panel">
          <h3>Current accounts</h3>
          {users.length === 0 ? (
            <div className="empty-state">No local users found.</div>
          ) : (
            <div className="event-list">
              {users.map((user) => (
                <article key={user.id} className="event-row">
                  <div className="event-name">
                    {user.display_name} <span className="muted-tag">{user.username}</span>
                  </div>
                  <div className="event-meta">
                    {formatUserRole(user.role)} • {user.status}
                    {user.must_change_password ? " • password change required" : ""}
                  </div>
                  <div className="button-row">
                    <button
                      type="button"
                      className="secondary-button"
                      disabled={busy || user.id === currentUserId}
                      onClick={() => onToggleStatus(user)}
                    >
                      {user.status === "active" ? "Disable" : "Enable"}
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
