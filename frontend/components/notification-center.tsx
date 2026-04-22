"use client";

import { useEffect, useRef } from "react";

import type { NotificationHistoryEntry } from "@/src/types";

type NotificationCenterProps = {
  entries: NotificationHistoryEntry[];
  open: boolean;
  onToggle: () => void;
  onClose: () => void;
  onClear: () => void;
  formatTimestamp: (value: string) => string;
};

export function NotificationCenter({
  entries,
  open,
  onToggle,
  onClose,
  onClear,
  formatTimestamp,
}: NotificationCenterProps) {
  const rootRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!open) {
      return;
    }

    function handlePointerDown(event: MouseEvent) {
      if (!rootRef.current?.contains(event.target as Node)) {
        onClose();
      }
    }

    document.addEventListener("mousedown", handlePointerDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
    };
  }, [onClose, open]);

  return (
    <div className="notification-center" ref={rootRef}>
      <button
        type="button"
        className={`notification-bell ${open ? "notification-bell-open" : ""}`}
        onClick={onToggle}
        aria-label="Open notifications"
        title="Notifications"
      >
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path
            d="M12 4.5a4 4 0 0 0-4 4v2.2c0 .7-.2 1.4-.6 2L6 15h12l-1.4-2.3a3.9 3.9 0 0 1-.6-2V8.5a4 4 0 0 0-4-4Z"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d="M10 18a2.2 2.2 0 0 0 4 0"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinecap="round"
          />
        </svg>
      </button>

      {open ? (
        <div className="notification-popover">
          <div className="notification-popover-header">
            <div>
              <h3>Notifications</h3>
              <p className="panel-copy">Recent workbench activity and admin changes.</p>
            </div>
            <div className="notification-popover-actions">
              {entries.length > 0 ? (
                <button
                  type="button"
                  className="notification-clear-button"
                  onClick={onClear}
                >
                  Clear
                </button>
              ) : null}
              <button
                type="button"
                className="notification-popover-close"
                onClick={onClose}
                aria-label="Close notifications"
              >
                ×
              </button>
            </div>
          </div>

          {entries.length === 0 ? (
            <div className="empty-state">No recent notifications yet.</div>
          ) : (
            <div className="notification-history-list">
              {entries.map((entry) => (
                <article key={entry.id} className="notification-history-item">
                  <div className="notification-history-title">{entry.event_type}</div>
                  <div className="notification-history-meta">
                    {entry.actor_display_name ? `${entry.actor_display_name} • ` : ""}
                    {entry.project_name ? `${entry.project_name} • ` : ""}
                    {formatTimestamp(entry.created_at)}
                  </div>
                  {entry.payload ? (
                    <div className="notification-history-copy">{entry.payload}</div>
                  ) : null}
                </article>
              ))}
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
}
