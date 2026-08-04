# Experiment 6-11 AndroidWorld iteration report

- Run ID: `exp6-11-20260804T045559Z`
- Generated (UTC): `2026-08-04T09:13:52Z`
- Upstream commit: `d9c569f764b3a5629321858de03ff653d0f24056`
- Device: `sdk_gphone64_x86_64`, API `33` (upstream tested reference: API `33`)
- Observation method: `uiautomator_compact`
- Provider/model: `local-vllm` / `qwen2.5-7b-instruct-local`
- Model source/runtime: `local_gpu` / `vllm-0.19.0`
- Accelerator: `NVIDIA_RTX_PRO_6000_Blackwell_96GB`
- Required apps: `24/24`
- Scope: 116 task(s), 5 trial(s), mode `candidate_rerun`
- Full 116-task × 5-seed suite completed: **false**

The bundled ~88% baseline is historical input evidence. The manuscript's 88%→94% numbers are explicitly hypothetical and are not used as rerun results here.

## 1. Diagnose

- The historical run evaluated 116 tasks once each and reports approximately 88% overall success.
- Wi-Fi is a concentrated failure cluster: three of the four SystemWifiTurn* rows failed in the bundled per-task table.
- The capability matrix links the cluster to weak complex_ui_understanding, information_retrieval, and requires_setup behavior.
- The failed traces show navigation/state-verification loops; increasing the step cap alone would treat a symptom rather than the cause.

## 2. Hypothesis

The diagnosis produced explicit surface, middle, and deep hypotheses. Only one variable is changed in this run; the other hypotheses remain untested.

| Layer / ID | Proposed change | Target | Verification | Status |
| --- | --- | --- | --- | --- |
| surface / `H1` | Add Wi-Fi Settings navigation and final-state verification guidance. | At least one net paired success across the four Wi-Fi tasks, with no regression. | Paired upstream-prompt versus task-guideline ablation with matched seeds. | tested in source phase 1 |
| surface / `H2` | Add application-specific recognition rules for the non-standard Tasks UI. | Improve at least two of the six historical Tasks failures with no regression. | Paired Tasks-only prompt/tool-description ablation after app provisioning. | not tested |
| middle / `H3` | Repair and validate the multimodal input path for transcription tasks. | Raise transcription success above the historical 0% while bounding added tokens and latency. | Paired screenshot-disabled versus screenshot-enabled transcription run. | not tested |
| middle / `H4` | Conditionally enable deeper thinking for counting tasks. | Improve math/counting success without applying the cost to unrelated tasks. | Paired tag-routed thinking-mode ablation with latency and token guardrails. | not tested |
| middle / `H5` | Replace the API-35-incompatible gRPC accessibility feed with upstream's UIAutomator observation path. | At least one net paired Wi-Fi success with no regression and at most 1.5x latency/tokens. | Paired a11y-forwarder versus UIAutomator run with the same upstream T3A prompt and matched seeds. | tested in source phase 2 |
| middle / `H5C` | Filter non-semantic UIAutomator container nodes after H5 exposed excessive prompt-token cost. | Preserve H5 paired success with no regression while using at most 0.75x raw-UIAutomator tokens and 1.5x latency. | Paired raw-UIAutomator versus compact-UIAutomator run with matched tasks, seeds, prompt, and evaluator. | tested in this run |
| deep / `H6` | Combine screenshots with the structured UI tree and compare stronger vision-capable models. | Improve complex-UI success enough to justify multimodal latency and token cost. | Factorial UI-tree/screenshot/model ablation on the full tagged slice. | not tested |

Selected hypothesis: `H5C`
- Change: Use the real upstream UIAutomator hierarchy but retain only visible text, descriptions, and actionable/scrollable elements.
- Expected measurable result: Preserve H5 paired success with no regression while using at most 0.75x raw-UIAutomator tokens and 1.5x latency.
- Guardrails: Same model, seed, task parameters, emulator, checkout, and step budget; require at least four completed pairs, every compact-UIAutomator treatment pair successful, no paired regression, at most 1.5x mean latency, and at most 0.75x raw-UIAutomator mean tokens. Passing a paired gate permits only a full-suite candidate rerun; it is not deployment approval, and a subset must never be reported as full-suite success.

## 3. Controlled experiment

- Phase: `phase_2_cost_refinement` — middle-layer input-pipeline cost refinement after the H5 success/cost result
- Independent variable: raw versus semantic-filtered UIAutomator element list
- Controls: same checkout, model, task parameters, generated seed, step budget, and emulator; arm order alternates by pair.

| Arm | Episodes | Success | Reward | Steps | Latency (s) | LLM calls | Mean tokens | Input / output tokens | Est. cost (USD) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| candidate | 116/116 | 0.026 | 0.129 | 9.698 | 110.113 | 19.103 | 174058.216 | 20054856 / 135897 | 0.000000 |

## 4. Data-driven decision

- Outcome: **`candidate_subset_rerun_completed`**
- Reason: A real modified candidate subset rerun completed, but it is not the 116-task × five-trial gate and cannot approve deployment.
- Treatment/control mean latency ratio: n/a
- Treatment/control mean token ratio: n/a
- Treatment/control mean LLM-call ratio: n/a
- Cost guardrails passed: **false**
- Deployment approved: **false**

## 5. Rerun and next report

This run is a real controlled subset/smoke rerun, not the complete AndroidWorld benchmark. The next gate is a conditionally enabled candidate rerun over all 116 tasks with five seeds after provisioning the upstream API-33 app environment.

Observed residual failures:
- `candidate / AudioRecorderRecordAudio / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / AudioRecorderRecordAudioWithFileName / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / BrowserDraw / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / BrowserMaze / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / BrowserMultiply / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / CameraTakePhoto / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / CameraTakeVideo / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / ClockStopWatchPausedVerify / trial 1`: final evaluator state passed, but the agent never declared completion
- `candidate / ClockStopWatchRunning / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / ClockTimerEntry / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / ContactsAddContact / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / ExpenseAddMultiple / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / ExpenseAddMultipleFromGallery / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / ExpenseAddMultipleFromMarkor / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / ExpenseAddSingle / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / ExpenseDeleteDuplicates / trial 1`: final evaluator state passed, but the agent never declared completion
- `candidate / ExpenseDeleteMultiple / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / ExpenseDeleteMultiple2 / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / ExpenseDeleteSingle / trial 1`: final evaluator state passed, but the agent never declared completion
- `candidate / FilesDeleteFile / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / ContactsNewContactDraft / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / ExpenseDeleteDuplicates2 / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / FilesMoveFile / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / MarkorAddNoteHeader / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / MarkorChangeNoteContent / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / MarkorCreateFolder / trial 1`: final evaluator state passed, but the agent never declared completion
- `candidate / MarkorCreateNote / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / MarkorCreateNoteAndSms / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / MarkorDeleteAllNotes / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / MarkorDeleteNewestNote / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / MarkorDeleteNote / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / MarkorEditNote / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / MarkorMergeNotes / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / MarkorMoveNote / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / MarkorTranscribeReceipt / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / MarkorTranscribeVideo / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / NotesTodoItemCount / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / OpenAppTaskEval / trial 1`: final evaluator state passed, but the agent never declared completion
- `candidate / OsmAndFavorite / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / OsmAndMarker / trial 1`: agent declared completion, but the real evaluator state failed
- `candidate / OsmAndTrack / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / RecipeAddMultipleRecipes / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / RecipeAddMultipleRecipesFromImage / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / RecipeAddMultipleRecipesFromMarkor / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / RecipeAddMultipleRecipesFromMarkor2 / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / RecipeAddSingleRecipe / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / RecipeDeleteDuplicateRecipes / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / RecipeDeleteDuplicateRecipes2 / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / RecipeDeleteDuplicateRecipes3 / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / RecipeDeleteMultipleRecipes / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / RecipeDeleteMultipleRecipesWithConstraint / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / RecipeDeleteMultipleRecipesWithNoise / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / RecipeDeleteSingleWithRecipeWithNoise / trial 1`: final evaluator state passed, but the agent never declared completion
- `candidate / RetroCreatePlaylist / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / RetroPlaylistDuration / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / RetroSavePlaylist / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / SaveCopyOfReceiptTaskEval / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / SimpleCalendarAddOneEvent / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / SimpleCalendarAddOneEventInTwoWeeks / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / SimpleCalendarAddOneEventRelativeDay / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / SimpleCalendarAddOneEventTomorrow / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / SimpleCalendarAddRepeatingEvent / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / SimpleCalendarAnyEventsOnDate / trial 1`: agent declared completion, but the real evaluator state failed
- `candidate / SimpleCalendarDeleteEvents / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / SimpleCalendarDeleteEventsOnRelativeDay / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / SimpleCalendarDeleteOneEvent / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / SimpleCalendarEventOnDateAtTime / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / SimpleCalendarEventsInNextWeek / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / SimpleCalendarEventsInTimeRange / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / SimpleCalendarEventsOnDate / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / SimpleCalendarFirstEventAfterStartTime / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / SimpleCalendarLocationOfEvent / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / SimpleCalendarNextEvent / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / SimpleDrawProCreateDrawing / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / SimpleSmsReply / trial 1`: agent declared completion, but the real evaluator state failed
- `candidate / SimpleSmsResend / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / SimpleSmsSend / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / SimpleSmsSendReceivedAddress / trial 1`: agent declared completion, but the real evaluator state failed
- `candidate / SportsTrackerActivitiesCountForWeek / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / SportsTrackerActivitiesOnDate / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / SportsTrackerActivityDuration / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / SportsTrackerLongestDistanceActivity / trial 1`: agent declared completion, but the real evaluator state failed
- `candidate / SportsTrackerTotalDistanceForCategoryOverInterval / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / SportsTrackerTotalDurationForCategoryThisWeek / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / SystemBluetoothTurnOff / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / SystemBluetoothTurnOffVerify / trial 1`: final evaluator state passed, but the agent never declared completion
- `candidate / SystemBluetoothTurnOn / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / SystemBluetoothTurnOnVerify / trial 1`: final evaluator state passed, but the agent never declared completion
- `candidate / SystemBrightnessMax / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / SystemBrightnessMaxVerify / trial 1`: final evaluator state passed, but the agent never declared completion
- `candidate / SystemBrightnessMin / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / SystemBrightnessMinVerify / trial 1`: final evaluator state passed, but the agent never declared completion
- `candidate / SystemWifiTurnOff / trial 1`: agent declared completion, but the real evaluator state failed
- `candidate / SystemWifiTurnOffVerify / trial 1`: final evaluator state passed, but the agent never declared completion
- `candidate / SystemWifiTurnOn / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / SystemWifiTurnOnVerify / trial 1`: final evaluator state passed, but the agent never declared completion
- `candidate / TasksCompletedTasksForDate / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / TasksDueNextWeek / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / TasksDueOnDate / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / TasksHighPriorityTasks / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / TasksHighPriorityTasksDueOnDate / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / TasksIncompleteTasksOnDate / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / TurnOffWifiAndTurnOnBluetooth / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / TurnOnWifiAndOpenApp / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / VlcCreatePlaylist / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / VlcCreateTwoPlaylists / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / MarkorCreateNoteFromClipboard / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / RetroPlayingQueue / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / SimpleSmsSendClipboardContent / trial 1`: agent declared completion, but the real evaluator state failed
- `candidate / SystemCopyToClipboard / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / SimpleSmsReplyMostRecent / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / NotesIsTodo / trial 1`: evaluator reward / completion gate was not satisfied
- `candidate / NotesMeetingAttendeeCount / trial 1`: evaluator reward / completion gate was not satisfied

### LLM analysis of this run

The following bounded interpretation was produced by the configured real LLM from the aggregate evidence (the JSON remains authoritative):

- Summary: The candidate subset of 116 tasks was rerun, achieving a success rate of 2.59% with an estimated cost of $0.00. The mean latency was 110.11 seconds, and the mean number of LLM calls was 19.10. The mean total tokens used were 174,058.22.
- Cost/benefit interpretation: The cost of running the 116 tasks was minimal, with an estimated cost of $0.00. However, the low success rate of 2.59% indicates that the current approach is not cost-effective. The high latency and token usage suggest that the model may need optimization to reduce computational overhead.
- Residual pattern: Most tasks failed to achieve success, with only 3 out of 116 tasks succeeding.
- Residual pattern: Tasks involving complex interactions with the UI, such as 'RetroPlayingQueue' and 'SportsTrackerTotalDistanceForCategoryOverInterval', had the highest failure rates.
- Residual pattern: Tasks that required multiple steps or complex conditions, like 'RecipeDeleteMultipleRecipesWithNoise', were particularly challenging.
- Next hypothesis `H5C` (middle): Use the real upstream UIAutomator hierarchy but retain only visible text, descriptions, and actionable/scrollable elements. Target: Preserve H5 paired success with no regression while using at most 0.75x raw-UIAutomator tokens and 1.5x latency. Verification: Paired raw-UIAutomator versus compact-UIAutomator run with matched tasks, seeds, prompt, and evaluator.

## Environment boundaries

- UIAutomator is an upstream AndroidWorld observation option selected by the companion runner; it preserves real UI actions/evaluators but is a compatibility path, not the upstream API-33 reference configuration.
- Compact UIAutomator removes only non-semantic container nodes; observations, coordinates, Android actions, and AndroidWorld evaluators remain real.
- The full-suite candidate uses model qwen2.5-7b-instruct-local, while the promoted paired H5C source used doubao-seed-1-6-250615. This local-GPU campaign evaluates the promoted observation treatment but is not a same-model extension of the paired result.
- ContactsNewContactDraft's official success predicate was fed the upstream UIAutomator state.ui_elements because that observation mode does not populate state.forest; the predicate and requested contact fields were not changed.
- Clipboard get/set retries once after the exact Clipper foreground-access runtime error; the operation, content, task, and evaluator are unchanged.
- SimpleSmsReplyMostRecent polls the unchanged inbox query for up to five additional seconds because emulator-injected SMS delivery can lag past upstream's fixed wait; task data and the evaluator are unchanged.
- The pinned official Retro Music APK omits the playing_queue table, a known upstream runtime error. Only that exact missing-table condition was mapped to an empty observed queue so the unchanged exact queue predicate records an evaluator failure instead of losing the episode.
- Runtime-error retries reuse the exact task parameters retained in the discarded error checkpoints; upstream parameter-generator drift cannot silently change the retried task.
- SimpleSmsReplyMostRecent polls the unchanged inbox query for up to five additional seconds because emulator-injected SMS delivery can lag past upstream's fixed wait. If the inbox remains empty, the exact last injected address/body is inserted into the same SMS database that upstream clears directly; task data and the evaluator are unchanged.
- If compact UIAutomator still exceeds the pinned model's native 32,768-token context, the retry removes 8,192 characters only from the middle of the current-screen indexed UI section. Prompt prefix, goal, history, leading and trailing UI elements and indices, guidance, and output format remain; per-episode removal counters are retained.
- If compact UIAutomator still exceeds the pinned model's native 32,768-token context, the retry removes a bounded middle span only from indexed UI descriptions: 8,192 characters for action selection or 4,096 from each before/after summary screen. Prompt prefix, goal, history, action, reason, leading/trailing UI elements and indices, guidance, and output format remain; per-episode removal counters are retained.
- If compact UIAutomator still exceeds the pinned model's native 32,768-token context, the retry removes a bounded middle span only from indexed UI descriptions: 16,384 characters for action selection or 8,192 from each before/after summary screen. Prompt prefix, goal, history, action, reason, leading/trailing UI elements and indices, guidance, and output format remain; per-episode removal counters are retained.
- If compact UIAutomator still exceeds the pinned model's native 32,768-token context, the retry removes a bounded middle span only from indexed UI descriptions: at most 12,000 retained characters for action selection or 6,000 for each before/after summary screen. Prompt prefix, goal, history, action, reason, leading/trailing UI elements and indices, guidance, and output format remain; per-episode removal counters are retained.

The JSON beside this report is the authoritative evidence. It contains episode-level evaluator rewards, actions, timing, token counts, configuration, and explicit completion gates; credentials and raw prompts are not stored.
