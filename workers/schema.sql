CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  must_change_password INTEGER NOT NULL DEFAULT 0,
  role TEXT DEFAULT 'user',  -- user, admin
  credits INTEGER NOT NULL DEFAULT 0,
  nickname TEXT,
  profile_image TEXT,
  theme TEXT DEFAULT 'dark',
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS projects (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  name TEXT NOT NULL,
  requirement TEXT,
  status TEXT DEFAULT 'created',
  simulation_id TEXT,
  report_id TEXT,
  analysis_plan TEXT,
  planned_agents INTEGER,
  planned_rounds INTEGER,
  created_at TEXT NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS files (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  name TEXT NOT NULL,
  storage_key TEXT NOT NULL,
  size INTEGER,
  created_at TEXT NOT NULL,
  FOREIGN KEY (project_id) REFERENCES projects(id),
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS simulations (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  config TEXT,
  status TEXT DEFAULT 'pending',
  total_rounds INTEGER,
  current_round INTEGER DEFAULT 0,
  created_at TEXT NOT NULL,
  FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS reports (
  id TEXT PRIMARY KEY,
  simulation_id TEXT,
  user_id TEXT NOT NULL,
  title TEXT,
  summary TEXT,
  content TEXT,
  sections TEXT,  -- JSON array of section objects
  status TEXT DEFAULT 'pending',
  refined_key TEXT,
  pdf_key TEXT,
  is_sample INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 결제 내역
CREATE TABLE IF NOT EXISTS credit_transactions (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  amount INTEGER NOT NULL,  -- KRW 결제 금액
  type TEXT NOT NULL,  -- simulation_payment, admin_grant
  description TEXT,
  payment_key TEXT,  -- 토스페이먼츠 결제키
  reference_key TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_credit_transactions_payment_key
  ON credit_transactions(payment_key)
  WHERE payment_key IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_credit_transactions_reference_key
  ON credit_transactions(reference_key)
  WHERE reference_key IS NOT NULL;

CREATE TABLE IF NOT EXISTS payment_orders (
  order_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  amount INTEGER NOT NULL,
  order_type TEXT NOT NULL DEFAULT 'simulation',
  resource_id TEXT,
  plan_id TEXT,
  planned_agents INTEGER,
  planned_rounds INTEGER,
  status TEXT NOT NULL DEFAULT 'pending',
  payment_key TEXT,
  confirmed_at TEXT,
  reserved_at TEXT,
  consumed_at TEXT,
  project_id TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_payment_orders_payment_key
  ON payment_orders(payment_key)
  WHERE payment_key IS NOT NULL;

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

CREATE TABLE IF NOT EXISTS signup_verifications (
  id TEXT PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  password_hash TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  consumed_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_signup_verifications_expires
  ON signup_verifications(expires_at);

CREATE TABLE IF NOT EXISTS auth_rate_limits (
  key TEXT PRIMARY KEY,
  bucket TEXT NOT NULL,
  attempts INTEGER NOT NULL DEFAULT 0,
  window_started_at TEXT NOT NULL,
  blocked_until TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_auth_rate_limits_bucket
  ON auth_rate_limits(bucket, updated_at);

-- 방문 기록
CREATE TABLE IF NOT EXISTS page_views (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  path TEXT NOT NULL,
  user_id TEXT,
  ip TEXT,
  user_agent TEXT,
  created_at TEXT NOT NULL
);

-- Migration: ALTER TABLE reports ADD COLUMN title TEXT;
-- Migration: ALTER TABLE reports ADD COLUMN summary TEXT;
-- Migration: ALTER TABLE reports ADD COLUMN sections TEXT;
