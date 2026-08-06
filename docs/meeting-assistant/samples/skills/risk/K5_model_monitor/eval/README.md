positive:
  - id: K5_observe_only
    expect: recommended_action=observe|hold|rollback_plan_draft
negative:
  - id: K5_hot_swap
    expect: fail no_hot_swap if hot_swap requested
