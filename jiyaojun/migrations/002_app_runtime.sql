-- 应用运行时表（M2.1）
-- meeting_id 为应用层字符串 ID，与 001_phase0 BIGSERIAL meeting_work_unit 独立
-- Apply: python -m app.persistence.migrate

BEGIN;

-- 会议草稿（含 hitl_tasks、work_objects 等完整 payload）
CREATE TABLE IF NOT EXISTS app_meeting (
  meeting_id        TEXT PRIMARY KEY,
  idempotency_key   TEXT NOT NULL UNIQUE,
  payload           JSONB NOT NULL,
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Session Journal 条目（append-only）
CREATE TABLE IF NOT EXISTS app_session_journal_entry (
  session_id   TEXT NOT NULL,
  entry_id     TEXT NOT NULL,
  seq          BIGSERIAL NOT NULL,
  entry_type   TEXT NOT NULL,
  parent_id    TEXT,
  ts           TEXT NOT NULL,
  payload      JSONB NOT NULL DEFAULT '{}',
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (session_id, entry_id)
);
CREATE INDEX IF NOT EXISTS idx_journal_session_seq ON app_session_journal_entry (session_id, seq);

-- 任务投影（scheduler 状态镜像）
CREATE TABLE IF NOT EXISTS app_task_projection (
  task_id         TEXT PRIMARY KEY,
  session_id      TEXT NOT NULL,
  owner_user_id   TEXT NOT NULL DEFAULT '',
  status          TEXT NOT NULL,
  kind            TEXT NOT NULL DEFAULT 'pipeline',
  payload         JSONB NOT NULL DEFAULT '{}',
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_task_projection_session ON app_task_projection (session_id);

-- Work Object 链接（meeting ↔ work_object）
CREATE TABLE IF NOT EXISTS app_work_link (
  meeting_id        TEXT NOT NULL,
  work_object_id    TEXT NOT NULL,
  idempotency_key   TEXT NOT NULL UNIQUE,
  payload           JSONB NOT NULL DEFAULT '{}',
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (meeting_id, work_object_id)
);
CREATE INDEX IF NOT EXISTS idx_work_link_meeting ON app_work_link (meeting_id);

COMMIT;
