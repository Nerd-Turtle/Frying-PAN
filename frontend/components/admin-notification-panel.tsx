"use client";

import type { FormEvent } from "react";
import { useEffect, useState } from "react";

import type { NotificationSettings } from "@/src/types";

type AdminNotificationPanelProps = {
  settings: NotificationSettings | null;
  busy?: boolean;
  onSave: (payload: NotificationSettings) => Promise<void>;
  onOpenAuditLog: () => void;
};

export function AdminNotificationPanel({
  settings,
  busy = false,
  onSave,
  onOpenAuditLog,
}: AdminNotificationPanelProps) {
  const [timeoutSeconds, setTimeoutSeconds] = useState("10");

  useEffect(() => {
    if (settings) {
      setTimeoutSeconds(String(settings.notification_timeout_seconds));
    }
  }, [settings]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const parsed = Number(timeoutSeconds);
    if (!Number.isFinite(parsed)) {
      return;
    }

    await onSave({
      notification_timeout_seconds: parsed,
    });
  }

  return (
    <section className="workbench-panel">
      <div className="panel-header">
        <div>
          <h2>Notifications</h2>
          <p className="panel-copy">
            Configure how long pop-up notifications stay visible in the workbench.
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="result-panel">
        <h3>Banner timeout</h3>
        <label className="field-stack">
          Toast timeout in seconds
          <input
            type="number"
            min={3}
            max={60}
            step={1}
            value={timeoutSeconds}
            onChange={(event) => setTimeoutSeconds(event.target.value)}
            disabled={busy}
          />
        </label>
        <div className="button-row">
          <button
            type="submit"
            className="primary-button compact-button"
            disabled={busy || !settings}
          >
            {busy ? "Saving..." : "Save settings"}
          </button>
          <button type="button" className="secondary-button" onClick={onOpenAuditLog}>
            Open audit log
          </button>
        </div>
      </form>
    </section>
  );
}
