ALTER TABLE payment_orders ADD COLUMN plan_id TEXT;
ALTER TABLE payment_orders ADD COLUMN planned_agents INTEGER;
ALTER TABLE payment_orders ADD COLUMN planned_rounds INTEGER;

ALTER TABLE projects ADD COLUMN analysis_plan TEXT;
ALTER TABLE projects ADD COLUMN planned_agents INTEGER;
ALTER TABLE projects ADD COLUMN planned_rounds INTEGER;
