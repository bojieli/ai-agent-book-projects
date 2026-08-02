# Independent review of the first candidate

An independent reviewer rejected the first candidate pending correction. Read
the current diff and `BOOK_SELF_EVOLUTION_REPORT.md`, then address these exact
findings without expanding scope:

1. The request-local status is not prefix-stable across the tool loop. On call
   1 it is appended to the user API copy; on call 2 that historical user copy
   loses the status. On later calls, the previous tool result loses its old
   status before the newest tool result gains a new one. This changes prior
   wire bytes and invalidates the cached suffix, conflicting with Hermes'
   byte-stability rule. Use a persistent-append design (for example, stable
   `api_content` sidecars) or another design that proves previously sent wire
   messages remain byte-identical. Keep clean transcript content unchanged.
2. The tests exercise only the formatter. Add behavior-contract coverage for
   the actual attachment/replay mechanism over at least three successive API
   requests. Assert that each earlier wire message is byte-identical in every
   later request and that the newest status is closest to generation.
3. Correct the report's contradictory verification wording: the repository
   wrapper was blocked because its environment lacked pytest, but the focused
   tests did execute and pass through `uv run --with pytest`.

Run the focused tests, relevant existing replay/cache tests, compilation, and
`git diff --check`. Update the report with the review round and exact results.
Do not claim end-to-end benefit without an ablation campaign, do not push or
commit, and do not edit the book repository.
