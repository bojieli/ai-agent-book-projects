"""Runtime timeout configuration."""

DEFAULT_TIMEOUT = 30


def resolve_timeout(explicit=None, env=None):
    """Return a positive timeout using explicit > environment > default."""
    env = env or {}
    raw = env.get("AGENT_TIMEOUT", explicit)
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return DEFAULT_TIMEOUT
    return value if value > 0 else DEFAULT_TIMEOUT
