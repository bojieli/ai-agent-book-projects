positive:
  - id: X1_resolve_before_embed
    expect: ambiguity.resolved before work embed
negative:
  - id: X1_unresolved_all_agree
    expect: fail evaluate if status=open but prose claims 各方同意
  - id: X1_embed_while_open
    expect: deny embed when blocks_embed=true
