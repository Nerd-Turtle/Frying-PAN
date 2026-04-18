"use client";

import type { CSSProperties, FormEvent } from "react";
import { useState } from "react";

type AuthPanelProps = {
  busy?: boolean;
  onLogin: (payload: { username: string; password: string }) => Promise<void>;
};

export function AuthPanel({ busy = false, onLogin }: AuthPanelProps) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!username.trim() || !password.trim()) {
      return;
    }

    await onLogin({
      username: username.trim(),
      password: password.trim(),
    });

    setPassword("");
  }

  return (
    <section className="workbench-panel auth-panel-shell">
      <div className="panel-header">
        <div>
          <div className="panel-kicker">Login Portal</div>
          <h2>Sign in to Frying-PAN</h2>
          <p className="panel-copy">
            Use a local account to access the Panorama workbench. Fresh installs ship with the
            bootstrap administrator account <strong>chef</strong>.
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="auth-form">
        <div className="field-grid auth-field-grid">
          <div>
            <label htmlFor="auth-username" className="field-label">
              Username
            </label>
            <input
              id="auth-username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              placeholder="chef"
              disabled={busy}
              style={inputStyle}
            />
          </div>

          <div>
            <label htmlFor="auth-password" className="field-label">
              Password
            </label>
            <input
              id="auth-password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Enter your password"
              disabled={busy}
              style={inputStyle}
            />
          </div>
        </div>

        <button type="submit" disabled={busy} className="primary-button">
          {busy ? "Signing in..." : "Sign in"}
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
