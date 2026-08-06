-- LLM Safety Platform DDL (Postgres). SQLite uses SQLAlchemy create_all.
CREATE TABLE IF NOT EXISTS policy_bindings (
  id SERIAL PRIMARY KEY,
  policy_binding_id VARCHAR(128) NOT NULL,
  tenant_id VARCHAR(64) NOT NULL,
  app_id VARCHAR(64) NOT NULL,
  version INT NOT NULL,
  reason VARCHAR(64) NOT NULL,
  risk_tier VARCHAR(16) NOT NULL,
  fail_mode VARCHAR(16) NOT NULL,
  effect_cap VARCHAR(16) NOT NULL,
  body_json TEXT NOT NULL,
  require_dual_publish BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS virtual_keys (
  id SERIAL PRIMARY KEY,
  key_id VARCHAR(64) UNIQUE NOT NULL,
  key_hash VARCHAR(128) UNIQUE NOT NULL,
  tenant_id VARCHAR(64) NOT NULL,
  app_id VARCHAR(64) NOT NULL,
  name VARCHAR(128) DEFAULT '',
  model_allowlist_json TEXT DEFAULT '[]',
  rpm_limit INT DEFAULT 120,
  budget_tokens INT DEFAULT 1000000,
  spent_tokens INT DEFAULT 0,
  revoked BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_decisions (
  id SERIAL PRIMARY KEY,
  request_id VARCHAR(64) UNIQUE NOT NULL,
  tenant_id VARCHAR(64) NOT NULL,
  app_id VARCHAR(64) NOT NULL,
  decision VARCHAR(32) NOT NULL,
  body_json TEXT NOT NULL,
  content_hash VARCHAR(128) NOT NULL,
  chain_hash VARCHAR(128) DEFAULT '',
  prev_chain_hash VARCHAR(128) DEFAULT '',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS events (
  id SERIAL PRIMARY KEY,
  event_id VARCHAR(64) UNIQUE NOT NULL,
  event_type VARCHAR(64) NOT NULL,
  tenant_id VARCHAR(64) NOT NULL,
  app_id VARCHAR(64) NOT NULL,
  request_id VARCHAR(64) NOT NULL,
  body_json TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS approvals (
  id SERIAL PRIMARY KEY,
  approval_id VARCHAR(64) UNIQUE NOT NULL,
  tenant_id VARCHAR(64) NOT NULL,
  app_id VARCHAR(64) NOT NULL,
  request_id VARCHAR(64) NOT NULL,
  action_json TEXT NOT NULL,
  status VARCHAR(32) DEFAULT 'pending',
  decided_by VARCHAR(128) DEFAULT '',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS redteam_runs (
  id SERIAL PRIMARY KEY,
  run_id VARCHAR(64) UNIQUE NOT NULL,
  suite VARCHAR(64) NOT NULL,
  status VARCHAR(32) DEFAULT 'completed',
  passed BOOLEAN DEFAULT FALSE,
  report_json TEXT DEFAULT '{}',
  leak_rate DOUBLE PRECISION DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS vault_entries (
  id SERIAL PRIMARY KEY,
  token VARCHAR(128) UNIQUE NOT NULL,
  tenant_id VARCHAR(64) NOT NULL,
  request_id VARCHAR(64) NOT NULL,
  pii_type VARCHAR(32) NOT NULL,
  ciphertext TEXT NOT NULL,
  nonce VARCHAR(64) NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS publish_gates (
  id SERIAL PRIMARY KEY,
  gate_id VARCHAR(64) UNIQUE NOT NULL,
  tenant_id VARCHAR(64) NOT NULL,
  app_id VARCHAR(64) NOT NULL,
  status VARCHAR(32) DEFAULT 'pending',
  security_approved_by VARCHAR(128) DEFAULT '',
  owner_approved_by VARCHAR(128) DEFAULT '',
  eval_passed BOOLEAN DEFAULT FALSE,
  body_json TEXT DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);
