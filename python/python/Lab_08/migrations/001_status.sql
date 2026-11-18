-- Existing Lab_07 v1 database only; fresh schema already has status.
ALTER TABLE orders ADD COLUMN status TEXT NOT NULL DEFAULT 'new';
