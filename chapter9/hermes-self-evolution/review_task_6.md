# Sixth independent review: persisted-row backfill

The third terminal acceptance review rejected the current candidate despite all
focused tests passing. Continue the same self-update and correct this exact
persistence-boundary defect:

- `append_persistent_model_status()` mutates the newest message's in-memory
  `api_content` after that message has normally already been persisted. The
  turn-start user row is flushed before API-message construction
  (`agent/turn_context.py` around 1219–1235), and assistant/tool rows are
  incrementally flushed before tool execution (`agent/conversation_loop.py`
  around 6178–6185). The status is appended later around 1600–1612.
- `_flush_messages_to_session_db_unlocked()` deliberately skips messages with
  `_db_persisted`, and the new path has no update/backfill operation. The
  sidecar therefore survives within the current process but disappears after
  restart/session reload, changing the provider prefix across process
  boundaries.
- Existing `set_latest_user_api_content()` only updates the latest user row, is
  not called by the status path, and cannot cover a tool-result target.

Implement the smallest safe durable update at Hermes' existing string-only
database boundary. Do not widen the sidecar type or mutate clean transcript
content. Preserve role/tool ordering and fail closed for unsupported content.
Use stable row identity or another production-supported mechanism; do not rely
on list position if it could update the wrong persisted message.

Add a behavior test that persists a realistic user → assistant tool-call
(`content=None`) → string tool-result sequence, attaches status to the newest
tool evidence, reloads it through the real state/session path, and asserts the
same string sidecar and byte-identical replay after reload. The test must fail
if only the in-memory dictionary was changed.

Run the focused tests, existing sidecar/cache/turn-context regressions,
compilation, and `git diff --check`. Update `BOOK_SELF_EVOLUTION_REPORT.md` with
this sixth review and exact results. Do not edit the book, commit, push, or
claim downstream task improvement.
