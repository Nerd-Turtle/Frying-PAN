type StatusCardProps = {
  label: string;
  value: string;
  tone?: "default" | "success" | "warning";
};

export function StatusCard({
  label,
  value,
  tone = "default",
}: StatusCardProps) {
  const accent =
    tone === "success"
      ? "var(--success)"
      : tone === "warning"
        ? "var(--accent)"
        : "var(--line-strong)";

  return (
    <article
      style={{
        borderBottom: `1px solid ${accent}`,
        padding: "10px 0 14px",
      }}
    >
      <div style={{ color: "var(--muted)", fontSize: 13, textTransform: "uppercase" }}>
        {label}
      </div>
      <div style={{ fontSize: 24, fontWeight: 700, marginTop: 10 }}>{value}</div>
    </article>
  );
}
