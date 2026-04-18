"use client";

import type { FormEvent } from "react";
import { useState } from "react";

type PasswordChangePanelProps = {
  busy?: boolean;
  username: string;
  onSubmit: (payload: { current_password: string; new_password: string }) => Promise<void>;
};

export function PasswordChangePanel({
  busy = false,
  username,
  onSubmit,
}: PasswordChangePanelProps) {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!currentPassword.trim() || !newPassword.trim()) {
      return;
    }

    await onSubmit({
      current_password: currentPassword,
      new_password: newPassword,
    });

    setCurrentPassword("");
    setNewPassword("");
  }

  return (
    <section className="workbench-panel auth-panel-shell">
      <div className="panel-header">
        <div>
          <div className="panel-kicker">Password Setup</div>
          <h2>Change {username}&apos;s password</h2>
          <p className="panel-copy">
            This account is using a temporary password. Set a new password before entering the
            workbench.
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="auth-form">
        <div className="field-grid auth-field-grid">
          <label className="field-stack">
            Current password
            <input
              type="password"
              value={currentPassword}
              onChange={(event) => setCurrentPassword(event.target.value)}
              placeholder="Current temporary password"
              disabled={busy}
            />
          </label>
          <label className="field-stack">
            New password
            <input
              type="password"
              value={newPassword}
              onChange={(event) => setNewPassword(event.target.value)}
              placeholder="Choose a new password"
              disabled={busy}
            />
          </label>
        </div>
        <button type="submit" disabled={busy} className="primary-button">
          {busy ? "Updating..." : "Update password"}
        </button>
      </form>
    </section>
  );
}
