"use client";

import { ChangeEvent, useRef, useState } from "react";

type UploadSourceFormProps = {
  projectId: string;
  onUpload: (projectId: string, file: File) => Promise<void>;
};

export function UploadSourceForm({
  projectId,
  onUpload,
}: UploadSourceFormProps) {
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const inputRef = useRef<HTMLInputElement | null>(null);

  function handleChange(event: ChangeEvent<HTMLInputElement>) {
    setFile(event.target.files?.[0] ?? null);
  }

  async function handleUpload() {
    if (!file) {
      return;
    }

    setBusy(true);
    try {
      await onUpload(projectId, file);
      setFile(null);
      if (inputRef.current) {
        inputRef.current.value = "";
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ display: "grid", gap: 10 }}>
      <label style={{ fontWeight: 600 }}>Upload source XML</label>
      <input
        ref={inputRef}
        type="file"
        accept=".xml,text/xml,application/xml"
        onChange={handleChange}
      />
      {file ? (
        <div style={{ color: "var(--muted)", fontSize: 14 }}>
          Selected: <strong>{file.name}</strong>
        </div>
      ) : null}
      <button
        type="button"
        onClick={handleUpload}
        disabled={!file || busy}
        style={{
          border: "1px solid var(--line-strong)",
          borderRadius: 999,
          padding: "10px 14px",
          background: "var(--panel-strong)",
          color: "var(--text)",
          fontWeight: 700,
          justifySelf: "start",
        }}
      >
        {busy ? "Uploading..." : "Upload XML"}
      </button>
    </div>
  );
}
