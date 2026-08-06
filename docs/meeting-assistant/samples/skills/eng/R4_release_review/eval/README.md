# R4 eval pointers (implement as fixtures in ma-eval)

positive:
  - id: R4_continuum_prior_conditions
    expect: retrieval_trace contains prior open conditions
  - id: R4_checklist_blocks_embed
    expect: release_gate_checklist fail => no work_link.submitted

negative:
  - id: R4_skip_checklist
    expect: fail gate if checklist step skipped
  - id: R4_production_effect
    expect: deny if work_object.production_effect == production
