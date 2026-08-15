# Third independent review: persistence boundary

The second correction still overclaims multimodal support. Inspection of the
actual persistence boundary found:

- `hermes_state.py` types `api_content` as `Optional[str]` and writes non-string
  values as `None` (around lines 5632–5750 and 6078–6106);
- `run_agent.py` discards non-string `_row_api_content` during flush (around
  lines 2104–2110);
- `agent/turn_context.py` exposes string-only sidecar helpers.

Thus a list sidecar is replayed within the in-memory loop but disappears after
persistence/resume, invalidating the claimed durable byte stability. Make the
smallest compatible correction: fail closed for non-string content and do not
attach the model status on unsupported multimodal/list messages. Do not widen
the database schema or persistence contract in this experiment.

Update tests to assert list, empty, mapping, and numeric values are rejected by
the same production helper, and that string sidecars remain stable across
three requests. Remove any multimodal-support claim from code comments and the
report. Run the focused tests, the existing replay/cache regression set,
compilation, and `git diff --check`; update the report with exact results.

Do not edit the book, commit, push, or claim downstream task improvement.
