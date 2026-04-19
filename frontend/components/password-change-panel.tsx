"use client";

import type { FormEvent } from "react";
import { useState } from "react";

type PasswordChangePanelProps = {
  busy?: boolean;
  username: string;
  onSubmit: (payload: { current_password: string; new_password: string }) => Promise<void>;
  kicker?: string;
  title?: string;
  copy?: string;
  submitLabel?: string;
  variant?: "panel" | "embedded";
};

export function PasswordChangePanel({
  busy = false,
  username,
  onSubmit,
  kicker = "Password Setup",
  title,
  copy,
  submitLabel = "Update password",
  variant = "panel",
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

  const form = (
    <form onSubmit={handleSubmit} className="auth-form">
      <div className="field-grid auth-field-grid">
        <label className="field-stack">
          Current password
          <input
            type="password"
            value={currentPassword}
            onChange={(event) => setCurrentPassword(event.target.value)}
            placeholder="Current password"
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
        {busy ? "Updating..." : submitLabel}
      </button>
    </form>
  );

  if (variant === "embedded") {
    return (
      <>
        <div className="profile-section-header">
          <h2>{title ?? "Password"}</h2>
          <p className="panel-copy">
            {copy ?? "Update your local account password without leaving the workbench."}
          </p>
        </div>
        {form}
      </>
    );
  }

  return (
    <section className="workbench-panel auth-panel-shell">
      <div className="panel-header">
        <div>
          <div className="panel-kicker">{kicker}</div>
          <h2>{title ?? `Change ${username}'s password`}</h2>
          <p className="panel-copy">
            {copy ??
              "This account is using a temporary password. Set a new password before entering the workbench."}
          </p>
        </div>
      </div>
      {form}
    </section>
  );
}
