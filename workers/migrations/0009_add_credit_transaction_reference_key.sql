ALTER TABLE credit_transactions ADD COLUMN reference_key TEXT;

CREATE INDEX IF NOT EXISTS idx_credit_transactions_reference_key
  ON credit_transactions(reference_key)
  WHERE reference_key IS NOT NULL;
