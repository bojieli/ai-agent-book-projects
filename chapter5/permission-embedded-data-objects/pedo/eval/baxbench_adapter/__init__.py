"""BaxBench-derived adapter benchmark.

Translates a subset of BaxBench (arXiv:2502.11844, ETH Zurich) backend
scenarios into the function-level harness format used by DataGuardBench,
so the same security oracle can be applied to PEDO and RAW conditions.

This is an adapter — not official BaxBench numbers. The contract:
  - Each adapter scenario reproduces BaxBench's API surface (same endpoints,
    same per-endpoint contract) and security tests (same exploits) for the
    subset of CWEs that PEDO architecturally addresses.
  - Out-of-scope CWEs (SQL injection at the parsing layer, password hashing,
    JWT generation) are reported but not claimed to be in PEDO's scope.

Currently adapted scenarios:
  - SecretStorage (BaxBench id "SecretStorage")
      Tests: cross-user secret access (CWE-IMPROPER_ACCESS_CONTROL)
"""
