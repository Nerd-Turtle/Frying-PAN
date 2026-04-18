"use client";

import type { CSSProperties, FormEvent } from "react";
import { useState } from "react";

type AuthPanelProps = {
  busy?: boolean;
  onRegister: (payload: {
    email: string;
    display_name: string;
    password: string;
    organization_name?: string;
  }) => Promise<void>;
  onLogin: (payload: { email: string; password: string }) => Promise<void>;
};

export function AuthPanel({ busy = false, onRegister, onLogin }: AuthPanelProps) {
  const [mode, setMode] = useState<"register" | "login">("register");
  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [organizationName, setOrganizationName] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!email.trim() || !password.trim()) {
      return;
    }

    if (mode === "register") {
      if (!displayName.trim()) {
        return;
      }
      await onRegister({
        email: email.trim(),
        display_name: displayName.trim(),
        password: password.trim(),
        organization_name: organizationName.trim() || undefined,
      });
    } else {
      await onLogin({
        email: email.trim(),
        password: password.trim(),
      });
    }

    setPassword("");
  }

  return (
    <section className="workbench-panel">
      <div className="panel-header">
        <div>
          <div className="panel-kicker">Access</div>
          <h2>Sign In To Frying-PAN</h2>
          <p className="panel-copy">
            Phase 9 adds the first app-layer identity boundary. Sign in to access your
            projects, uploads, and audit trail.
          </p>
        </div>
        <div className="segmented-toggle">
          <button
            type="button"
            className={mode === "register" ? "segmented-toggle-active" : ""}
            onClick={() => setMode("register")}
          >
            Register
          </button>
          <button
            type="button"
            className={mode === "login" ? "segmented-toggle-active" : ""}
            onClick={() => setMode("login")}
          >
            Login
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="auth-form">
        <div className="field-grid">
          <div>
            <label htmlFor="auth-email" className="field-label">
              Email
            </label>
            <input
              id="auth-email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="operator@example.com"
              disabled={busy}
              style={inputStyle}
            />
          </div>

          {mode === "register" ? (
            <div>
              <label htmlFor="auth-display-name" className="field-label">
                Display name
              </label>
              <input
                id="auth-display-name"
                value={displayName}
                onChange={(event) => setDisplayName(event.target.value)}
                placeholder="Firewall Team"
                disabled={busy}
                style={inputStyle}
              />
            </div>
          ) : null}

          <div>
            <label htmlFor="auth-password" className="field-label">
              Password
            </label>
            <input
              id="auth-password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="At least 8 characters"
              disabled={busy}
              style={inputStyle}
            />
          </div>

          {mode === "register" ? (
            <div>
              <label htmlFor="auth-organization" className="field-label">
                Organization name
              </label>
              <input
                id="auth-organization"
                value={organizationName}
                onChange={(event) => setOrganizationName(event.target.value)}
                placeholder="Optional. Defaults to a personal workspace."
                disabled={busy}
                style={inputStyle}
              />
            </div>
          ) : null}
        </div>

        <button type="submit" disabled={busy} className="primary-button">
          {busy ? "Working..." : mode === "register" ? "Create account" : "Sign in"}
        </button>
      </form>
    </section>
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
