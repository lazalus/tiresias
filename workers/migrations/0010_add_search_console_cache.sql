CREATE TABLE IF NOT EXISTS search_console_cache (
  cache_key TEXT PRIMARY KEY,
  days INTEGER NOT NULL,
  site_url TEXT,
  payload TEXT,
  fetched_at TEXT,
  refresh_started_at TEXT,
  last_error TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_search_console_cache_days
  ON search_console_cache(days);
