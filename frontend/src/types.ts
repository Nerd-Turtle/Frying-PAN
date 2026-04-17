export type HealthResponse = {
  status: string;
  service: string;
};

export type Source = {
  id: string;
  label: string;
  filename: string;
  storage_path: string;
  file_sha256: string;
  source_type: string;
  parse_status: string;
  imported_at: string;
};

export type EventRecord = {
  id: string;
  event_type: string;
  payload?: string | null;
  created_at: string;
};

export type Project = {
  id: string;
  name: string;
  description?: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  sources?: Source[];
  events?: EventRecord[];
};
