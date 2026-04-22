"use client";

type ToastItem = {
  id: string;
  tone: "info" | "success" | "error";
  text: string;
};

type ToastStackProps = {
  notifications: ToastItem[];
  onDismiss: (id: string) => void;
};

export function ToastStack({ notifications, onDismiss }: ToastStackProps) {
  if (notifications.length === 0) {
    return null;
  }

  return (
    <div className="toast-stack" aria-live="polite" aria-atomic="true">
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className={`toast-notification toast-${notification.tone}`}
          role="status"
        >
          <div className="toast-copy">{notification.text}</div>
          <button
            type="button"
            className="toast-dismiss"
            onClick={() => onDismiss(notification.id)}
            aria-label="Dismiss notification"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  );
}
