positive:
  - id: general_minutes_only
    expect: artifact only; no work_object
negative:
  - id: general_embed_attempt
    expect: deny any connector write when maturity=L0
