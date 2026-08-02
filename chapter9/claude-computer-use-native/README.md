# Experiment 9-6: Anthropic native Computer Use

This record covers the provider-specific arm of Experiment 9-6: Anthropic's
native `computer`, `bash`, and text-editor tools in the official containerized
Computer Use Demo. It is separate from the completed open-model 9-7 arm.

Current status: **blocked / incomplete**. On 2026-08-03, the official
`anthropics/claude-quickstarts` source was checked out at the documented commit
`9bcc95e316e5ef6542b4c9d0469f4078829eead5`. Its Computer Use Dockerfile matched
the documented SHA-256
`3aa1f36a491f8f88d81a04c6a89b4cc9f9acd20ad946304c13419736da7c0ead`, and the
host Docker engine was available. A minimal request to Anthropic's official
Messages endpoint using the Demo's default model,
`claude-sonnet-4-5-20250929`, returned HTTP 401
`authentication_error: API key is invalid.`

The credential-free [preflight receipt](validation/exp9-6-anthropic-auth-20260803-v1/preflight.json)
records the source, host, request metadata, and provider error. It stores the
environment-variable name but never its value or an authorization header.

No container build or native computer-tool action is claimed. Building the
image cannot close the experiment when the provider rejects authentication
before model or tool access; the required weather task therefore did not run.
Completion still requires one bounded, read-only task in the pinned Demo with:

- the exact task text and an at-most-25-step limit;
- the actual Anthropic model and provider receipts;
- ordered native tool calls and screenshots/observations;
- a grounded final answer and explicit stop reason;
- no sign-in, purchase, form submission, or external-data mutation.

The intended task remains:

> Open Google, search for San Francisco weather today, and report the
> temperature and conditions. Do not sign in or change any external data.

To resume, configure a valid, funded `ANTHROPIC_API_KEY`, rerun the minimal
authentication probe, then build and execute the pinned local Demo. Do not use
the mutable `computer-use-demo-latest` image as evidence for this pinned arm.
