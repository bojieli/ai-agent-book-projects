# Second independent review: production-path mismatch

The cache correction is sound for string content, but independent inspection
found one remaining mismatch. Correct it without expanding scope:

1. `append_persistent_model_status` writes a list-valued `api_content` for
   multimodal content, but the real replay branch in
   `agent/conversation_loop.py` only honors non-empty string sidecars. The
   next request therefore drops the earlier multimodal status, while the test
   helper `_wire_copy` incorrectly replays any type. Either support typed
   sidecars safely throughout the real persistence/replay path or fail closed
   by not enabling this feature on unsupported content. Do not leave a test
   model that is more permissive than production.
2. Refactor the sidecar replay decision into production code that the test can
   call, or add coverage through the actual production request-building path.
   The contract must exercise the same type check used by
   `conversation_loop.py`, including string, list/multimodal, empty, and
   unsupported values.
3. Update the report with this second review round and exact verification.

Run the focused tests, the same replay/cache regression set, compilation, and
`git diff --check`. Do not change the book, commit, push, or claim downstream
task improvement.
