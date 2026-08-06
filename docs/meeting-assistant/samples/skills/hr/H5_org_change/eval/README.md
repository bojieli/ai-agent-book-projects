positive:
  - id: H5_sealed_skip_without_allowlist
    expect: render.skipped reason=critical_no_allowlist when no allowlist
negative:
  - id: H5_broadcast
    expect: deny all_participants delivery
  - id: H5_wide_index
    expect: deny continuum write_class=wide
  - id: H5_auto_notify
    expect: delivery.suppressed
