# Fifth independent review: realistic tool-call placement

The second terminal acceptance review rejected the corrected candidate after
running all requested checks. Continue the same self-update and address these
exact findings:

1. In the normal tool loop, the newest durable message is commonly an assistant
   tool-call message whose `content` is `None` or empty, followed by a tool
   result. The current backward search selects that assistant message, then
   fails closed because its content is unsupported. The model-visible status is
   therefore absent during common tool-loop requests.
2. The current test uses assistant tool-call messages with ordinary string
   content, so it does not cover the production shape above.
3. If the assistant tool-call message does have text, the current code appends
   status before the following tool result instead of at the request context
   end. This violates the book/report placement requirement that current
   model-visible state be closest to generation.

Implement a durable solution at the actual string-only persistence/replay
boundary. It may extend string `api_content` sidecar replay to tool messages if
that is supported by the state and flush contracts, but must not widen the
database type, mutate clean transcript content, disturb role/tool-call ordering,
or attach status to unsupported list/multimodal content. Inspect and test the
real production contract rather than relying on a permissive test helper.

Add coverage for an assistant tool call with `content=None` followed by a
string tool result, across at least three successive requests. Assert both
byte-identical historical replay and placement after the newest tool evidence.
Retain the adversarial output-bound test.

Run the focused tests, existing sidecar/cache/turn-context regressions,
compilation, and `git diff --check`. Update `BOOK_SELF_EVOLUTION_REPORT.md` with
this fifth review and exact results. Do not edit the book, commit, push, or
claim downstream task improvement.
