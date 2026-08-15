# Fourth independent review: tool-result replay and output bound

The terminal acceptance reviewer rejected the current candidate after running
the requested tests and inspecting the production path. Continue the same
self-update and correct these exact defects without expanding scope:

1. Status is currently appended to `source_messages[-1]` / `api_messages[-1]`
   without requiring a user message. After a tool call the newest message is a
   tool result, but production replay restores `api_content` sidecars only for
   user and assistant messages. A sidecar attached to the tool result therefore
   disappears on the next request, breaking the claimed byte-identical replay.
   Make attachment and replay behavior consistent with the real persisted
   message contract. Preserve role ordering and keep clean transcript content
   unchanged.
2. `build_model_status_context()` converts the TODO `item_id` to a string
   without truncating or otherwise bounding it. Enforce a deterministic total
   output bound, including adversarially long identifiers and descriptions.
3. Add behavior-contract tests that would have caught both defects: a
   successive-request sequence whose newest message is a tool result, and an
   oversized TODO identifier. Exercise the same production helpers/type checks
   used by `conversation_loop.py`.

Run the focused tests, the existing replay/cache regression set, compilation,
and `git diff --check`. Update `BOOK_SELF_EVOLUTION_REPORT.md` with this fourth
review round and exact results. Do not edit the book, commit, push, or claim
downstream task improvement.
