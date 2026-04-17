export type HealthResponse = {
  status: string;
  service: string;
};

export type Source = {
  id: string;
  filename: string;
  storage_path: string;
  kind: string;
  parse_status: string;
  uploaded_at: string;
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
