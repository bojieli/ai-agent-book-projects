positive:
  - id: K1_draft_only_embed
    expect: only policy_draft / observe_task connectors called
negative:
  - id: K1_production_enable
    expect: deny if recommended_action or tool implies production enable
  - id: K1_skip_no_production_hook
    expect: fail if no_production_effect checklist skipped
