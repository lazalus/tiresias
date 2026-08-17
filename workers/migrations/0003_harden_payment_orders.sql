ALTER TABLE payment_orders ADD COLUMN reserved_at TEXT;
ALTER TABLE payment_orders ADD COLUMN consumed_at TEXT;
ALTER TABLE payment_orders ADD COLUMN project_id TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_payment_orders_payment_key
  ON payment_orders(payment_key)
  WHERE payment_key IS NOT NULL;
