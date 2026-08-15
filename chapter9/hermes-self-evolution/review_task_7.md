# Seventh independent review: idempotent request rebuilds

The fourth terminal acceptance review rejected the candidate after all focused
tests passed. Continue the same self-update and correct this retry-path defect:

- `append_persistent_model_status()` is not idempotent when the same newest
  message is used to build another request (for example, a transient provider
  failure, empty-response retry, or request rebuild before a new transcript
  message). It computes `updated = base + "\n\n" + status` from wire content
  that already contains the previous projection, so every rebuild adds another
  `<agent_status>` block.
- A direct production-helper exercise repeated the call 20 times and produced
  20 status blocks, changing previously sent bytes and violating both the
  prompt-cache stability claim and the total output bound.
- Current tests always append a new transcript message before the next build
  and therefore miss same-message retries.

Make projection idempotent at the production persistence boundary. Preserve an
unmodified base sidecar or safely recognize/replace only a status projection
owned by this feature; do not delete user-authored text that merely resembles
status markup. Decide and document whether volatile status values remain fixed
for a retry of the same message or can be replaced, but previously sent prefix
bytes must not drift unexpectedly. Keep clean transcript content unchanged,
retain string-only fail-closed behavior, and durably persist the selected
sidecar by stable row identity.

Add a regression test that repeatedly builds requests with unchanged source
messages, including a persisted/reloaded case. Assert identical wire bytes and
exactly one owned status block. Retain realistic tool-call placement,
persistence-reload, adversarial-bound, and unsupported-type coverage.

Run the focused tests, existing sidecar/cache/turn-context regressions,
compilation, and `git diff --check`. Update `BOOK_SELF_EVOLUTION_REPORT.md` with
this seventh review and exact results. Do not edit the book, commit, push, or
claim downstream task improvement.
