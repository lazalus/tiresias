DROP TABLE IF EXISTS users;
CREATE TABLE users (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT DEFAULT 'user',  -- user, admin
  credits INTEGER DEFAULT 0,
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

DROP TABLE IF EXISTS reports;
CREATE TABLE IF NOT EXISTS reports (
  id TEXT PRIMARY KEY,
  simulation_id TEXT,
  user_id TEXT NOT NULL,
  title TEXT,
  summary TEXT,
  content TEXT,
  sections TEXT,  -- JSON array of section objects
  status TEXT DEFAULT 'pending',
  created_at TEXT NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 크레딧 거래 내역
CREATE TABLE IF NOT EXISTS credit_transactions (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  amount INTEGER NOT NULL,
  type TEXT NOT NULL,  -- purchase, usage, admin_grant
  description TEXT,
  payment_key TEXT,  -- 토스페이먼츠 결제키
  created_at TEXT NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 이용권 상품
CREATE TABLE IF NOT EXISTS credit_plans (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  credits INTEGER NOT NULL,
  price INTEGER NOT NULL,  -- KRW
  active INTEGER DEFAULT 1
);

-- 기본 이용권 상품 삽입
INSERT OR IGNORE INTO credit_plans (id, name, credits, price) VALUES
  ('plan_1', '시뮬레이션 1회', 1, 9900),
  ('plan_5', '시뮬레이션 5회', 5, 44000),
  ('plan_10', '시뮬레이션 10회', 10, 79000);

-- Migration: ALTER TABLE reports ADD COLUMN title TEXT;
-- Migration: ALTER TABLE reports ADD COLUMN summary TEXT;
-- Migration: ALTER TABLE reports ADD COLUMN sections TEXT;
