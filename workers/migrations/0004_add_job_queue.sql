CREATE TABLE IF NOT EXISTS job_queue (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  job_type TEXT NOT NULL,
  resource_key TEXT,
  request_path TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'queued',
  started_at TEXT,
  finished_at TEXT,
  last_error TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_job_queue_job_status_created
  ON job_queue(job_type, status, created_at);

CREATE INDEX IF NOT EXISTS idx_job_queue_user_created
  ON job_queue(user_id, created_at DESC);

CREATE UNIQUE INDEX IF NOT EXISTS idx_job_queue_active_dedupe
  ON job_queue(user_id, job_type, request_path, resource_key)
  WHERE status IN ('queued', 'dispatching');
