positive:
  - id: H2_sealed_no_blast
    expect: write_class=sealed; delivery allowlist_only or suppressed
negative:
  - id: H2_broadcast_email
    expect: fail / suppress if delivery_scope=all_participants
  - id: H2_wide_continuum
    expect: fail continuum.write_decided if write_class forced wide
  - id: H2_auto_notify_all
    expect: delivery.suppressed for non-allowlist
