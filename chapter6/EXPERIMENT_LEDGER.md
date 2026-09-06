# Chapter 6 experiment ledger

Records for the two experiments that moved here from chapter 4 when chapter 6 (“Interaction”) was split
out, plus the native-asynchronous-model experiment. Same convention as the chapter 4 ledger: `official_complete` is true only when every gate named by
the manuscript has substantive real evidence.

| Experiment | Canonical run | Status | `official_complete` | Manifest SHA-256 |
| --- | --- | --- | --- | --- |
| 6-1 | `agent-with-event-trigger/validation/experiment_6_1/credential_probe_20260730T064500Z` | blocked | false | `3f689dfee915503f61ca30e9b590e24c8950496ca90fbf365def83805e877d0a` (stale, see note) |
| 6-2 | `async-agent/validation/experiment_6_2/real_subprocess_20260730T052500Z` | passed | true | `fff6b43a2e3a0b706fdd68bca289119f726d3f827f3f4d837e97321f7d48a825` |
| 6-3 | `astra-async-steering/validation/runs/exp6-14-20260905-formal` | passed | true | `bfece1666a63131e44c911908f4b0a07e6afffb719e8463b7507840d7d998c9e` |

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

## Experiment 6-3 — native asynchronous tools and mid-turn steering

The Astra experiment follows the event queue (6-1) and the compatibility runtime
(6-2) in manuscript order. Its five groups, each repeated three times, have
retained wire events and replayable judgments; the three legacy-model cases
require an explicit capability rejection. See the [companion README](astra-async-steering/README.md)
for protocol details, measurements, and limits.

## Current numbering and archived evidence

正文按阅读顺序编号。项目名称用于定位代码，运行目录及证据内部标识用于定位已经发生的实验；重新编号不改写既有记录、源码快照或哈希。以下“归档编号”只用于查阅历史记录，不是当前正文的编号。各项目 README 使用当前编号，既有运行器与验证器可继续使用原有证据标识。

| 当前正文 | 项目与主题 | 归档编号 |
| --- | --- | --- |
| 6-1 | [邮件事件](agent-with-event-trigger/) | 6-1 |
| 6-2 | [运行时异步与打断](async-agent/) | 6-2 |
| 6-3 | [模型原生异步与中途引导](astra-async-steering/) | 6-14 |
| 6-4 | [传统语音 Agent](live-audio/) | 6-3 |
| 6-5 | [流式语音感知](streaming-speech/) | 6-4 |
| 6-6 | [端到端全模态语音](end-to-end-speech/) | 6-5 |
| 6-7 | [控制标记 TTS](controllable-tts/) | 6-6 |
| 6-8 | [Anthropic Computer Use](claude-computer-use-native/) | 6-7 |
| 6-9 | [browser-use 开放模型](computer-use-open-model/) | 6-8 |
| 6-10 | [XLeRobot 真机遥操作](xlerobot-teleoperation/) | 6-9 |
| 6-11 | [模拟控制上限](xlerobot-teleoperation/) | 6-10 |
| 6-12 | [XLeRobot 自主操作](gemini-xlerobot-navigation/) | 6-11 |
| 6-13 | [模拟闭环比较](gemini-xlerobot-navigation/) | 6-12 |
| 6-14 | [RGB 跨环境测试](rgb-sim2real-grasping/) | 6-13 |
