"""Stable version 1.0.0. It intentionally contains the reproduced bug."""

VERSION = "1.0.0"
MAX_RETRIES = 3
CIRCUIT_BREAKER_THRESHOLD = 5
NON_RETRYABLE_CODES = {"AUTH_DENIED", "INVALID_ARGUMENT"}


def should_retry(error_code, retryable, attempt):
    """Return whether another tool call should be attempted."""
    return attempt < MAX_RETRIES


def should_open_circuit(consecutive_failures, *, error_code="", retryable=True):
    """Open after repeated failures."""
    return consecutive_failures >= CIRCUIT_BREAKER_THRESHOLD
