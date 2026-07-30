"""Stable version 1.0.0. It intentionally contains the reproduced bug."""

VERSION = "1.0.1-rejected"
MAX_RETRIES = 3
CIRCUIT_BREAKER_THRESHOLD = 5
NON_RETRYABLE_CODES = {"AUTH_DENIED", "INVALID_ARGUMENT"}


def should_retry(error_code, retryable, attempt):
    """Incorrect over-broad fix retained as a rejected candidate."""
    return False


def should_open_circuit(consecutive_failures, *, error_code="", retryable=True):
    """Open immediately for permanent errors; otherwise use the threshold."""
    if not retryable or error_code in NON_RETRYABLE_CODES:
        return consecutive_failures >= 1
    return consecutive_failures >= CIRCUIT_BREAKER_THRESHOLD
