# Live diagnosis experiment PRD

- R1 (P0): Every refund must call `verify_refund_eligibility` before
  `process_refund`; a refund without the check is a policy violation.
- R2 (P1): `check_stock` must complete within 250 ms. On origin timeout the
  orchestrator must use the degraded cache route; it must not simply fail.
- R3 (P1): Regression cases must cite the source trajectory ID and the exact
  observed turn where the violation is visible.
