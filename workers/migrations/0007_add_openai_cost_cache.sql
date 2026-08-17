CREATE TABLE IF NOT EXISTS openai_cost_cache (
  cache_key TEXT PRIMARY KEY,
  days INTEGER NOT NULL,
  payload TEXT,
  total_cost_usd REAL NOT NULL DEFAULT 0,
  total_cost_krw INTEGER NOT NULL DEFAULT 0,
  fetched_at TEXT,
  refresh_started_at TEXT,
  last_error TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_openai_cost_cache_days
  ON openai_cost_cache(days);
