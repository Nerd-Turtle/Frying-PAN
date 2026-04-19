"use client";

import type { FormEvent } from "react";
import { useEffect, useState } from "react";

import { formatUserRole } from "@/lib/labels";
import type { UserRecord } from "@/src/types";

type ProfilePanelProps = {
  busy?: boolean;
  user: UserRecord;
  onSubmit: (payload: { display_name?: string; email?: string }) => Promise<void>;
  variant?: "panel" | "embedded";
};

export function ProfilePanel({
  busy = false,
  user,
  onSubmit,
  variant = "panel",
}: ProfilePanelProps) {
  const [displayName, setDisplayName] = useState(user.display_name);
  const [email, setEmail] = useState(user.email ?? "");

  useEffect(() => {
    setDisplayName(user.display_name);
    setEmail(user.email ?? "");
  }, [user.display_name, user.email]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSubmit({
      display_name: displayName.trim() || undefined,
      email: email.trim() || undefined,
    });
  }

  const form = (
    <form onSubmit={handleSubmit} className="auth-form">
      <div className="field-grid auth-field-grid">
        <label className="field-stack">
          Username
          <input value={user.username} disabled readOnly />
        </label>
        <label className="field-stack">
          Role
          <input value={formatUserRole(user.role)} disabled readOnly />
        </label>
        <label className="field-stack">
          Display name
          <input
            value={displayName}
            onChange={(event) => setDisplayName(event.target.value)}
            disabled={busy}
            placeholder="Chef"
          />
        </label>
        <label className="field-stack">
          Email
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            disabled={busy}
            placeholder="chef@example.com"
          />
        </label>
      </div>

      <div className="button-row">
        <button type="submit" disabled={busy} className="primary-button">
          {busy ? "Saving..." : "Save profile"}
        </button>
      </div>
    </form>
  );

  if (variant === "embedded") {
    return (
      <>
        <div className="profile-section-header">
          <h2>Account details</h2>
          <p className="panel-copy">
            Update the identity details shown in the workbench. Username and role stay managed by
            local access.
          </p>
        </div>
        {form}
      </>
    );
  }

  return (
    <section className="workbench-panel">
      <div className="panel-header">
        <div>
          <div className="panel-kicker">Profile</div>
          <h2>Account details</h2>
          <p className="panel-copy">
            Update the identity details shown in the workbench. Username and role remain managed by
            the local access layer.
          </p>
        </div>
      </div>
      {form}
    </section>
  );
}
