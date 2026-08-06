positive:
  - id: R5_recall_open_blockers
    expect: continuum open blockers recalled; open_blockers_recalled=true
negative:
  - id: R5_skip_continuum_all_green
    expect: fail if open_blockers_recalled=false while series has open items
