# Eighth independent review: pre-existing sidecar composition

The fifth terminal acceptance review rejected the candidate after all focused
checks passed. Continue the same self-update and correct this production-path
collision:

- `append_persistent_model_status()` currently treats any existing non-empty
  `api_content` as an already installed status projection and returns it
  unchanged.
- Hermes already uses `api_content` for ordinary API-only composition,
  including memory/plugin prefetch context and sanitization-divergence replay.
  `build_turn_context()` can populate the current user sidecar before the model
  status helper runs. On that normal path, enabling the feature silently adds
  no `<agent_status>` block.
- Existing tests cover only messages with no pre-existing sidecar.

Compose safely with pre-existing string sidecars while remaining idempotent.
Distinguish a projection owned by this feature from unrelated API-only content
using a bounded, deterministic representation that survives persistence and
reload. Never parse or delete clean transcript content. If using an ownership
marker/suffix, recognize only the exact feature-owned terminal form and preserve
the pre-existing sidecar byte-for-byte; malformed/lookalike user or plugin text
must be treated as ordinary base content rather than destructively replaced.
Retain fail-closed handling for unsupported types and stable-row database
backfill.

Add regression coverage for a realistic pre-existing string `api_content`
sidecar (representing memory/plugin prefetch), repeated same-message request
builds, database close/reopen, and exact byte preservation of the original
sidecar plus exactly one status projection. Include a malformed/lookalike marker
case if the chosen ownership scheme can collide with ordinary content.

Run the focused tests, existing sidecar/cache/turn-context regressions,
compilation, and `git diff --check`. Update `BOOK_SELF_EVOLUTION_REPORT.md` with
this eighth review and exact results. Do not edit the book, commit, push, or
claim downstream task improvement.
