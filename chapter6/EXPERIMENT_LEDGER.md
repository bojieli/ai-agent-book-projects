# Chapter 6 experiment ledger

Records for the two experiments that moved here from chapter 4 when chapter 6 (“Interaction”) was split
out. Same convention as the chapter 4 ledger: `official_complete` is true only when every gate named by
the manuscript has substantive real evidence.

| Experiment | Canonical run | Status | `official_complete` | Manifest SHA-256 |
| --- | --- | --- | --- | --- |
| 6-1 | `agent-with-event-trigger/validation/experiment_6_1/credential_probe_20260730T064500Z` | blocked | false | `3f689dfee915503f61ca30e9b590e24c8950496ca90fbf365def83805e877d0a` (stale, see note) |
| 6-2 | `async-agent/validation/experiment_6_2/real_subprocess_20260730T052500Z` | passed | true | `fff6b43a2e3a0b706fdd68bca289119f726d3f827f3f4d837e97321f7d48a825` |

> **6-1's recorded hash no longer verifies.** The manifest's `experiment` field was relabelled 4-5 → 6-1
> during the chapter-6 split, which changed the file, but neither this value nor the one in
> `agent-with-event-trigger/validation/experiment_6_1/latest.json` was updated. The file now hashes to
> `5b8befd016806b719bec1eca4ac3caa12067308b65cdee19e8ef358bd8f864c5`. It is left as-is pending a
> re-run or an explicitly documented recomputation, rather than being silently overwritten.

## Experiment 6-1 — event-driven mailbox agent

Manuscript gates: three real inbound test-mailbox events processed FIFO: meeting/calendar conflict plus draft, complaint extraction plus high-priority notification, and marketing archive plus provider verification.

- The campaign fetched and hashed all eight official Unipile Email/Calendar schema documents and made credential-redacted live API probes.
- Blocked before mailbox mutation: the configured Unipile credential returns 401 with both documented `X-API-KEY` and diagnostic Bearer authentication. Therefore zero local/synthetic mail objects were substituted and no three-email success is claimed.

## Experiment 6-2 — interruptible asynchronous agent

All four exact manuscript scenarios passed with real OS subprocesses: a 3–5
second command remained non-blocking while the time question was answered;
queued instructions were appended once and produced a Japanese HTML artifact;
an interrupt terminated the real child process and the runtime recovered; and
the 3%/2%/1% parallel jobs triggered exactly one status query after the fast
job, preserved the >50% job, cancelled only the <=50% job, and produced a
hashed integrated report. The canonical summary is
`async-agent/validation/experiment_6_2/real_subprocess_20260730T052500Z/summary.json`.
