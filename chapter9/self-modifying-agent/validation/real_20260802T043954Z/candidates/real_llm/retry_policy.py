"""Candidate version 1.0.1-rc.1 with permanent-failure handling."""

VERSION = "1.0.1-rc.1"
MAX_RETRIES = 3
CIRCUIT_BREAKER_THRESHOLD = 5
NON_RETRYABLE_CODES = {"AUTH_DENIED", "INVALID_ARGUMENT"}


def should_retry(error_code, retryable, attempt):
    """Return whether another tool call should be attempted."""
    if not retryable or error_code in NON_RETRYABLE_CODES:
        return False
    return attempt < MAX_RETRIES


def should_open_circuit(consecutive_failures, *, error_code="", retryable=True):
    """Open immediately for permanent failures or after repeated temporary failures."""
    if not retryable or error_code in NON_RETRYABLE_CODES:
        return consecutive_failures >= 1
    return consecutive_failures >= CIRCUIT_BREAKER_THRESHOLD
