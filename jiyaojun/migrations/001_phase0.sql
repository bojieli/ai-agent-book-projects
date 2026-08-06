-- Phase 0 DDL (PostgreSQL)
-- SoT: docs/meeting-assistant/03 §4 + 05 §2.2
-- Apply: psql "$DATABASE_URL" -f migrations/001_phase0.sql

BEGIN;

CREATE TABLE IF NOT EXISTS org_domain (
  id           BIGSERIAL PRIMARY KEY,
  code         VARCHAR(32) NOT NULL UNIQUE,
  display_name VARCHAR(128) NOT NULL,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT org_domain_code_chk CHECK (code IN ('eng','business','hr','risk','compliance'))
);

CREATE TABLE IF NOT EXISTS scenario_profile (
  id                    BIGSERIAL PRIMARY KEY,
  code                  VARCHAR(64) NOT NULL UNIQUE,
  org_domain_code       VARCHAR(32) NOT NULL REFERENCES org_domain(code),
  orchestration_mode    VARCHAR(16) NOT NULL CHECK (orchestration_mode IN ('sop','playbook')),
  maturity_level        VARCHAR(8)  NOT NULL CHECK (maturity_level IN ('L0','L1','L2','L3')),
  default_embed_gate    VARCHAR(32) NOT NULL CHECK (default_embed_gate IN ('allow','confirm_only','block')),
  classification        VARCHAR(32) NOT NULL,
  continuum_write_class VARCHAR(16) NOT NULL CHECK (continuum_write_class IN ('wide','domain','sealed','none')),
  production_effect_cap VARCHAR(32) NOT NULL DEFAULT 'draft_only',
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS scenario_skill_pack (
  id                 BIGSERIAL PRIMARY KEY,
  pack_key           VARCHAR(128) NOT NULL,
  version            VARCHAR(32)  NOT NULL,
  story_id           VARCHAR(32)  NOT NULL,
  scenario_profile_id BIGINT REFERENCES scenario_profile(id),
  orchestration_mode VARCHAR(16) NOT NULL,
  governance_status  VARCHAR(16) NOT NULL DEFAULT 'draft'
                     CHECK (governance_status IN ('draft','in_review','approved','revoked')),
  path_uri           TEXT NOT NULL,
  UNIQUE (pack_key, version)
);

CREATE TABLE IF NOT EXISTS meeting_series (
  id         BIGSERIAL PRIMARY KEY,
  series_key VARCHAR(128) NOT NULL UNIQUE,
  title      TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS agent_session (
  id          BIGSERIAL PRIMARY KEY,
  session_key VARCHAR(64) NOT NULL UNIQUE,
  user_id     VARCHAR(64),
  checkpoint_json JSONB,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS meeting_work_unit (
  id                    BIGSERIAL PRIMARY KEY,
  org_domains_json      JSONB NOT NULL,
  scenario_profile_id   BIGINT REFERENCES scenario_profile(id),
  primary_skill_pack_id BIGINT REFERENCES scenario_skill_pack(id),
  purpose               TEXT,
  success_criteria      TEXT,
  series_id             VARCHAR(128),
  project_id            VARCHAR(128),
  classification        VARCHAR(32),
  embed_gate            VARCHAR(32),
  continuum_write_class VARCHAR(16),
  policy_binding_id     BIGINT,
  status                VARCHAR(32) NOT NULL DEFAULT 'draft',
  created_by            VARCHAR(64),
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_mwu_series ON meeting_work_unit (series_id, created_at);
CREATE INDEX IF NOT EXISTS idx_mwu_scenario ON meeting_work_unit (scenario_profile_id, created_at);

CREATE TABLE IF NOT EXISTS meeting_skill_binding (
  id            BIGSERIAL PRIMARY KEY,
  meeting_id    BIGINT NOT NULL REFERENCES meeting_work_unit(id),
  skill_pack_id BIGINT NOT NULL REFERENCES scenario_skill_pack(id),
  org_domain    VARCHAR(32),
  role          VARCHAR(16) NOT NULL CHECK (role IN ('primary','secondary')),
  status        VARCHAR(32) NOT NULL DEFAULT 'bound',
  UNIQUE (meeting_id, skill_pack_id)
);

CREATE TABLE IF NOT EXISTS policy_binding (
  id                      BIGSERIAL PRIMARY KEY,
  meeting_id              BIGINT NOT NULL REFERENCES meeting_work_unit(id),
  version                 INT NOT NULL,
  reason                  VARCHAR(64) NOT NULL
    CHECK (reason IN ('initial','ambiguity_changed','understanding_changed','pre_embed')),
  embed_gate              VARCHAR(32) NOT NULL,
  classification          VARCHAR(32),
  continuum_write_class   VARCHAR(16),
  delivery_scope          VARCHAR(64),
  production_effect_cap   VARCHAR(32) NOT NULL DEFAULT 'draft_only',
  glossary_scopes_json    JSONB,
  knowledge_scopes_json   JSONB,
  tool_allowlist_json     JSONB,
  cost_quota_snapshot_json JSONB,
  created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (meeting_id, version)
);

-- meeting_work_unit.policy_binding_id soft-FK (avoid cycle); enforce in app

CREATE TABLE IF NOT EXISTS artifact (
  id                      BIGSERIAL PRIMARY KEY,
  meeting_id              BIGINT NOT NULL REFERENCES meeting_work_unit(id),
  org_domains_json        JSONB NOT NULL,
  scenario_type           VARCHAR(64) NOT NULL,
  skill_pack_id           BIGINT REFERENCES scenario_skill_pack(id),
  artifact_kind           VARCHAR(64) NOT NULL,
  schema_id               VARCHAR(128) NOT NULL,
  schema_version          VARCHAR(32) NOT NULL,
  payload_json            JSONB NOT NULL,
  confidence              VARCHAR(32),
  unresolved_json         JSONB,
  source_spans_json       JSONB,
  references_json         JSONB,
  chart_series_json       JSONB,
  classification          VARCHAR(32),
  continuum_write_class   VARCHAR(16),
  created_by_stage        VARCHAR(32),
  created_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ambiguity_record (
  id                      BIGSERIAL PRIMARY KEY,
  meeting_id              BIGINT NOT NULL REFERENCES meeting_work_unit(id),
  term                    VARCHAR(128) NOT NULL,
  candidate_senses_json   JSONB NOT NULL,
  evidence_citations_json JSONB,
  status                  VARCHAR(32) NOT NULL
    CHECK (status IN ('open','resolved','escalated','expired')),
  resolved_sense          VARCHAR(128),
  resolver_user_id        VARCHAR(64),
  deadline                TIMESTAMPTZ,
  effect_on_embed_gate    VARCHAR(32),
  created_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS work_object (
  id                BIGSERIAL PRIMARY KEY,
  connector_id      VARCHAR(128) NOT NULL,
  org_domain        VARCHAR(32) NOT NULL,
  object_type       VARCHAR(64) NOT NULL,
  external_id       VARCHAR(128),
  status            VARCHAR(64),
  production_effect VARCHAR(32) NOT NULL,
  idempotency_key   VARCHAR(128) NOT NULL UNIQUE,
  source_spans_json JSONB,
  acl_snapshot_json JSONB,
  last_synced_at    TIMESTAMPTZ,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS work_link (
  id             BIGSERIAL PRIMARY KEY,
  meeting_id     BIGINT NOT NULL REFERENCES meeting_work_unit(id),
  work_object_id BIGINT NOT NULL REFERENCES work_object(id),
  artifact_id    BIGINT REFERENCES artifact(id),
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (meeting_id, work_object_id)
);

CREATE TABLE IF NOT EXISTS pipeline_run (
  id                 BIGSERIAL PRIMARY KEY,
  meeting_id         BIGINT NOT NULL REFERENCES meeting_work_unit(id),
  orchestration_mode VARCHAR(16) NOT NULL,
  budget_json        JSONB NOT NULL,
  terminal           VARCHAR(64),
  current_step       VARCHAR(64),
  worker_id          VARCHAR(64),
  lease_until        TIMESTAMPTZ,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS domain_event (
  id              BIGSERIAL PRIMARY KEY,
  event_type      VARCHAR(64) NOT NULL,
  meeting_id      BIGINT,
  pipeline_run_id BIGINT,
  trace_id        VARCHAR(64),
  payload_json    JSONB NOT NULL,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_domain_event_meeting ON domain_event (meeting_id, created_at);
CREATE INDEX IF NOT EXISTS idx_domain_event_type ON domain_event (event_type, created_at);

CREATE TABLE IF NOT EXISTS domain_glossary (
  id                BIGSERIAL PRIMARY KEY,
  org_domain        VARCHAR(32) NOT NULL,
  term              VARCHAR(128) NOT NULL,
  gloss             TEXT NOT NULL,
  governance_status VARCHAR(16) NOT NULL DEFAULT 'draft',
  UNIQUE (org_domain, term)
);

CREATE TABLE IF NOT EXISTS unknown_term (
  id         BIGSERIAL PRIMARY KEY,
  meeting_id BIGINT NOT NULL REFERENCES meeting_work_unit(id),
  term       VARCHAR(128) NOT NULL,
  status     VARCHAR(32) NOT NULL DEFAULT 'open',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS doc_chunk_index (
  id             BIGSERIAL PRIMARY KEY,
  chunk_key      VARCHAR(128) NOT NULL UNIQUE,
  org_domain     VARCHAR(32) NOT NULL,
  classification VARCHAR(32) NOT NULL,
  write_class    VARCHAR(16),
  vector_ref     VARCHAR(256),
  sparse_text    TEXT,
  acl_key        VARCHAR(128),
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS meeting_continuum_index (
  id             BIGSERIAL PRIMARY KEY,
  continuum_key  VARCHAR(128) NOT NULL UNIQUE,
  meeting_id     BIGINT REFERENCES meeting_work_unit(id),
  org_domain     VARCHAR(32) NOT NULL,
  classification VARCHAR(32) NOT NULL,
  write_class    VARCHAR(16) NOT NULL,
  vector_ref     VARCHAR(256),
  sparse_text    TEXT,
  acl_key        VARCHAR(128),
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS continuum_write_receipt (
  id               BIGSERIAL PRIMARY KEY,
  meeting_id       BIGINT NOT NULL REFERENCES meeting_work_unit(id),
  write_class      VARCHAR(16) NOT NULL,
  index_alias      VARCHAR(128),
  rejected_reason  TEXT,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS retrieval_trace (
  id           BIGSERIAL PRIMARY KEY,
  meeting_id   BIGINT NOT NULL REFERENCES meeting_work_unit(id),
  query_text   TEXT,
  citations_json JSONB,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tool_call_log (
  id                 BIGSERIAL PRIMARY KEY,
  meeting_id         BIGINT,
  tool_id            VARCHAR(128) NOT NULL,
  args_json          JSONB,
  result_json        JSONB,
  error              TEXT,
  production_effect  VARCHAR(32),
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS render_job (
  id                  BIGSERIAL PRIMARY KEY,
  meeting_id          BIGINT NOT NULL REFERENCES meeting_work_unit(id),
  acl_view_id         VARCHAR(128) NOT NULL,
  template_id         VARCHAR(128),
  status              VARCHAR(32) NOT NULL
    CHECK (status IN ('requested','completed','skipped')),
  skip_reason         VARCHAR(128),
  delivery_suppressed BOOLEAN NOT NULL DEFAULT FALSE,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS render_artifact (
  id            BIGSERIAL PRIMARY KEY,
  render_job_id BIGINT NOT NULL REFERENCES render_job(id),
  format        VARCHAR(32) NOT NULL,
  object_key    TEXT,
  content_hash  VARCHAR(128),
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS task_delivery_log (
  id            BIGSERIAL PRIMARY KEY,
  meeting_id    BIGINT NOT NULL REFERENCES meeting_work_unit(id),
  channel       VARCHAR(32) NOT NULL,
  acl_view_id   VARCHAR(128),
  render_job_id BIGINT REFERENCES render_job(id),
  recipient_set_hash VARCHAR(128),
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS usage_ledger (
  id               BIGSERIAL PRIMARY KEY,
  day              DATE NOT NULL,
  org_domain       VARCHAR(32) NOT NULL,
  scenario         VARCHAR(64) NOT NULL,
  llm_tokens       BIGINT NOT NULL DEFAULT 0,
  tool_calls       BIGINT NOT NULL DEFAULT 0,
  retrieve_hops    BIGINT NOT NULL DEFAULT 0,
  embed_attempts   BIGINT NOT NULL DEFAULT 0,
  render_variants  BIGINT NOT NULL DEFAULT 0,
  wall_clock_sec   DOUBLE PRECISION NOT NULL DEFAULT 0,
  meeting_count    BIGINT NOT NULL DEFAULT 0,
  UNIQUE (day, org_domain, scenario)
);

CREATE TABLE IF NOT EXISTS trace_span (
  id         BIGSERIAL PRIMARY KEY,
  trace_id   VARCHAR(64) NOT NULL,
  span_id    VARCHAR(64) NOT NULL UNIQUE,
  name       VARCHAR(128) NOT NULL,
  meeting_id BIGINT,
  attrs_json JSONB,
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  ended_at   TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS governance_change (
  id          BIGSERIAL PRIMARY KEY,
  object_type VARCHAR(64) NOT NULL,
  object_id   VARCHAR(128) NOT NULL,
  from_status VARCHAR(32),
  to_status   VARCHAR(32) NOT NULL,
  approver    VARCHAR(64),
  eval_run_id VARCHAR(64),
  ticket_id   VARCHAR(64),
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS eval_case (
  id         BIGSERIAL PRIMARY KEY,
  story_id   VARCHAR(32) NOT NULL,
  case_key   VARCHAR(128) NOT NULL UNIQUE,
  kind       VARCHAR(16) NOT NULL CHECK (kind IN ('positive','negative')),
  spec_json  JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS eval_run (
  id         BIGSERIAL PRIMARY KEY,
  case_id    BIGINT REFERENCES eval_case(id),
  passed     BOOLEAN NOT NULL,
  detail_json JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS transcript_document (
  id                  BIGSERIAL PRIMARY KEY,
  meeting_id          BIGINT REFERENCES meeting_work_unit(id),
  object_key          TEXT NOT NULL,
  hotword_profile_id  VARCHAR(64),
  segment_count       INT,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- seed org domains
INSERT INTO org_domain (code, display_name) VALUES
  ('eng', '研发/科技'),
  ('business', '业务'),
  ('hr', '人力资源'),
  ('risk', '风控'),
  ('compliance', '合规')
ON CONFLICT (code) DO NOTHING;

COMMIT;
