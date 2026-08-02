# Experiment 10-4: TalkAct concurrent-agent reproduction

This record covers the pinned external TalkAct reproduction used by Experiment
10-4. The required comparison runs concurrent fast/slow agents (`duplex`)
against a single-model control (`strawman`) over four hermetic tasks and two
seeds, retaining 16 episode logs plus success, latency, bridge, and failure
evidence.

Current status: **blocked / incomplete**. On 2026-08-03, the official
`19PINE-AI/TalkAct` source matched commit
`7d70007f72d45ddfc1a14e8e229b6d444e4919a2`. The Python 3.12 runtime is
available, and the benchmark's six key runtime files were hashed in the
[credential-free preflight](validation/exp10-4-anthropic-auth-20260803-v1/preflight.json).

The pinned code constructs `AsyncAnthropic` clients directly for both the fast
conversation tier and slow computer-use tier. A minimal request to Anthropic's
official Messages endpoint using TalkAct's default fast model,
`claude-haiku-4-5`, returned HTTP 401
`authentication_error: API key is invalid.` The configured Gemini credential
could supply the simulated caller, but it cannot replace the unavailable
Anthropic fast/slow agents without creating a different provider and source
configuration.

No benchmark episode is claimed. Dependency installation, the hermetic task
server, and Playwright execution were not started after the provider
precondition failed. To resume:

1. Configure a valid, funded `ANTHROPIC_API_KEY` and recheck the official
   endpoint.
2. Install the pinned `requirements.txt` under Python 3.12 and install the
   pinned Playwright Chromium build.
3. Run the hermetic task server and the exact comparison:

   ```bash
   python bench/run_bench.py \
     --tasks forms-insurance booking-flight webmail-report meeting-helper \
     --conditions duplex strawman \
     --seeds 2
   ```

4. Retain every episode, provider/model/usage receipt, deterministic task
   check, latency sample, and bridge event. A source checkout or one smoke
   episode does not complete the experiment.
