positive:
  - id: C2_continuum_open_items
    expect: retrieve continuum open remediations before extract
  - id: C2_done_with_evidence
    expect: done items require evidence_ref + references
negative:
  - id: C2_verbal_done
    expect: fail evidence_required if done without evidence_ref
  - id: C2_skip_checklist
    expect: fail if evidence_gate skipped
