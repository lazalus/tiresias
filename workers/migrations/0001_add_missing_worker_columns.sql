ALTER TABLE users ADD COLUMN credits INTEGER NOT NULL DEFAULT 0;

ALTER TABLE reports ADD COLUMN refined_key TEXT;
ALTER TABLE reports ADD COLUMN is_sample INTEGER NOT NULL DEFAULT 0;

CREATE UNIQUE INDEX IF NOT EXISTS idx_credit_transactions_payment_key
  ON credit_transactions(payment_key)
  WHERE payment_key IS NOT NULL;
