positive:
  - id: R1_actions_to_task
    expect: confirm_only then connector.task.create draft
negative:
  - id: R1_embed_without_hitl
    expect: deny embed when embed_gate=confirm_only and hitl not passed
  - id: R1_open_as_decision
    expect: fail evaluate if open_questions written as committed decisions
