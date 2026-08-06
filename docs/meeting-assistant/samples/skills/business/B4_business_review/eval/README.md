positive:
  - id: B4_prior_actions_and_chart
    expect: prior_actions_recalled=true and chart_series sourced
negative:
  - id: B4_invented_metrics
    expect: fail if chart points lack source / contradict payload.metrics
