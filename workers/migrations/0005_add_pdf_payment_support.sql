ALTER TABLE reports ADD COLUMN pdf_key TEXT;

ALTER TABLE payment_orders ADD COLUMN order_type TEXT NOT NULL DEFAULT 'simulation';
ALTER TABLE payment_orders ADD COLUMN resource_id TEXT;

CREATE INDEX IF NOT EXISTS idx_payment_orders_type_resource_status
  ON payment_orders(user_id, order_type, resource_id, status, created_at DESC);
