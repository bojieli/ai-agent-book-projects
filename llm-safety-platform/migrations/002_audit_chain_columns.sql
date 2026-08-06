-- Idempotent upgrade: audit chain columns + legacy row backfill
-- Applied automatically by app.db.migrate.upgrade_audit_chain on startup
--
-- Single-writer boundary: backfill assumes one process; multi-replica production
-- must hold Postgres pg_advisory_lock or use a dedicated audit-chain writer.

ALTER TABLE audit_decisions ADD COLUMN IF NOT EXISTS chain_hash VARCHAR(128) DEFAULT '';
ALTER TABLE audit_decisions ADD COLUMN IF NOT EXISTS prev_chain_hash VARCHAR(128) DEFAULT '';
