"""
Sandbox safety evaluator for agent-generated code.

Chapter 5 discusses the tension between giving a coding agent the power to
execute code and keeping that execution safe. Experiment 5-12 discussion
question #7 names the "deadly triad": private data access, untrusted content
exposure, and external communication, combined with persistent memory. This
module evaluates agent-generated code snippets for those risk patterns and
scores how well a sandbox configuration mitigates them.

The evaluator is purely static: it never executes the code it inspects, so it
is safe to run in tests and CI without a real sandbox.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Matches string literals (preserved) and line comments (stripped) so that
# risk patterns mentioned only in comments or string contents are not flagged.
# Triple-quoted strings span newlines (DOTALL); single/double-quoted strings do
# not. A match starting with ``#`` is a comment and is removed.
_STRING_OR_COMMENT = re.compile(
    r'""".*?"""|\'\'\'.*?\'\'\''
    r'|"(?:\\.|[^"\\\n])*"|\'(?:\\.|[^\'\\\n])*\''
    r'|#[^\n]*',
    re.DOTALL,
)


def _strip_comments(code: str) -> str:
    """Remove ``#`` line comments from ``code``, preserving string literals."""
    return _STRING_OR_COMMENT.sub(
        lambda m: "" if m.group(0).startswith("#") else m.group(0), code
    )


# ---------------------------------------------------------------------------
# Risk pattern definitions.
#
# Each entry maps a human-readable pattern label to a list of regular
# expressions. A snippet is flagged with a label when any of its regexes match.
# The labels are the strings that appear in ``CodeRiskAssessment.risk_patterns``
# and drive risk classification.
# ---------------------------------------------------------------------------

_RISK_PATTERNS: dict[str, list[re.Pattern[str]]] = {
    # Arbitrary code execution: the snippet can run any string as code.
    "arbitrary_execution": [
        re.compile(r"\beval\s*\("),
        re.compile(r"\bexec\s*\("),
        re.compile(r"\bcompile\s*\("),
        re.compile(r"\b__import__\s*\("),
        re.compile(r"\bos\.system\s*\("),
        re.compile(r"\bos\.popen\s*\("),
    ],
    # Subprocess execution: launching external processes through the
    # subprocess module (treated as medium; os.system/os.popen above are high).
    "subprocess_execution": [
        re.compile(r"\bsubprocess\b"),
        re.compile(r"\bPopen\s*\("),
    ],
    # Network communication: the deadly triad's "external communication" leg.
    "network_call": [
        re.compile(r"\brequests\.\w+\s*\("),
        re.compile(r"\brequests\.\w+\b"),
        re.compile(r"\burllib\b"),
        re.compile(r"\burlopen\s*\("),
        re.compile(r"\bsocket\b"),
        re.compile(r"\bhttp\.client\b"),
        re.compile(r"\bhttpx\b"),
        re.compile(r"\baiohttp\b"),
        re.compile(r"\bfetch\s*\("),
    ],
    "file_write": [
        re.compile(r"\bopen\s*\([^)]*['\"]\s*[wa]b?\+?\s*['\"]"),
        re.compile(r"\bPath\.\w*write\w*\("),
        re.compile(r"\b\.write(_text|_bytes)?\s*\("),
        re.compile(r"\bos\.remove\s*\("),
        re.compile(r"\bos\.unlink\s*\("),
        re.compile(r"\bshutil\.rmtree\s*\("),
        re.compile(r"\bshutil\.move\s*\("),
        re.compile(r"\bshutil\.copy\w*\s*\("),
    ],
    # Read-only file access: low risk on its own.
    "file_read": [
        re.compile(r"\bopen\s*\("),
        re.compile(r"\bPath\.\w*read\w*\("),
        re.compile(r"\b\.read(_text|_bytes)?\s*\("),
        re.compile(r"\bos\.listdir\s*\("),
        re.compile(r"\bos\.walk\s*\("),
        re.compile(r"\bpathlib\b"),
    ],
    # Environment variable access: the "private data access" leg.
    "env_var_access": [
        re.compile(r"\bos\.environ\b"),
        re.compile(r"\bos\.getenv\s*\("),
        re.compile(r"\bos\.putenv\s*\("),
    ],
}

# Sandbox configuration keys and the risk pattern each one mitigates.
_CONFIG_KEYS: tuple[str, ...] = (
    "filesystem_restricted",
    "network_blocked",
    "subprocess_disabled",
    "env_vars_filtered",
)

# Mapping from a dimension score name to the config key that drives it.
_DIMENSION_TO_CONFIG: dict[str, str] = {
    "filesystem_isolation": "filesystem_restricted",
    "network_restriction": "network_blocked",
    "subprocess_control": "subprocess_disabled",
    "env_var_protection": "env_vars_filtered",
}

# Which detected patterns a given config key is meant to mitigate.
_CONFIG_TO_PATTERNS: dict[str, tuple[str, ...]] = {
    "filesystem_restricted": ("file_read", "file_write"),
    "network_blocked": ("network_call",),
    "subprocess_disabled": ("subprocess_execution", "arbitrary_execution"),
    "env_vars_filtered": ("env_var_access",),
}


@dataclass
class CodeRiskAssessment:
    """Assessment of a single code snippet."""

    code_snippet: str
    risk_level: str  # one of: safe, low, medium, high
    risk_patterns: list[str]
    recommendations: list[str]


@dataclass
class SandboxEvaluation:
    """Aggregate evaluation over a batch of snippets."""

    total_snippets: int
    risk_distribution: dict[str, int]
    sandbox_config: dict[str, bool]
    dimension_scores: dict[str, float]
    overall_sandbox_score: float
    assessments: list[CodeRiskAssessment] = field(default_factory=list)


class CodeSandboxEvaluator:
    """Evaluate the safety of agent-generated code and its sandbox.

    The evaluator inspects code statically (regex-based) and never executes
    it, so it is deterministic and safe to run anywhere.
    """

    def __init__(self, sandbox_config: dict[str, bool] | None = None) -> None:
        self.sandbox_config: dict[str, bool] = (
            dict(sandbox_config) if sandbox_config is not None else self.default_sandbox_config()
        )
        # Deterministic mode: static analysis only, never execute code. This is
        # always True for this implementation; the flag exists so callers and
        # tests can assert that no execution path is taken.
        self.deterministic: bool = True

    # -- public API --------------------------------------------------------

    @staticmethod
    def default_sandbox_config() -> dict[str, bool]:
        """Return the recommended (most restrictive) sandbox configuration."""
        return {
            "filesystem_restricted": True,
            "network_blocked": True,
            "subprocess_disabled": True,
            "env_vars_filtered": True,
        }

    def analyze_code(self, code: str) -> CodeRiskAssessment:
        """Analyze a single code snippet and return a risk assessment."""
        patterns = self._detect_patterns(code)
        risk_level = self._classify_risk(patterns)
        recommendations = self._recommendations_for(patterns)
        return CodeRiskAssessment(
            code_snippet=code,
            risk_level=risk_level,
            risk_patterns=patterns,
            recommendations=recommendations,
        )

    def evaluate_batch(self, code_snippets: list[str]) -> SandboxEvaluation:
        """Analyze a batch of snippets and aggregate the results."""
        assessments = [self.analyze_code(snippet) for snippet in code_snippets]
        distribution: dict[str, int] = {"safe": 0, "low": 0, "medium": 0, "high": 0}
        for a in assessments:
            distribution[a.risk_level] = distribution.get(a.risk_level, 0) + 1

        dimension_scores = self._dimension_scores()
        overall = self._overall_score(dimension_scores)
        return SandboxEvaluation(
            total_snippets=len(code_snippets),
            risk_distribution=distribution,
            sandbox_config=dict(self.sandbox_config),
            dimension_scores=dimension_scores,
            overall_sandbox_score=overall,
            assessments=assessments,
        )

    def check_sandbox_config(self) -> dict[str, bool]:
        """Return the effective sandbox configuration, filling any missing keys.

        Missing keys default to ``False`` (fail-open is reported honestly as
        "not restricted") so callers can see exactly which protections are
        absent rather than silently inheriting a secure default.
        """
        return {key: bool(self.sandbox_config.get(key, False)) for key in _CONFIG_KEYS}

    # -- internals ---------------------------------------------------------

    @staticmethod
    def _detect_patterns(code: str) -> list[str]:
        """Return the ordered list of risk-pattern labels found in ``code``."""
        found: list[str] = []
        stripped = _strip_comments(code)
        for label, regexes in _RISK_PATTERNS.items():
            if any(rx.search(stripped) for rx in regexes):
                found.append(label)
        return found

    @staticmethod
    def _classify_risk(patterns: list[str]) -> str:
        """Classify risk level from detected patterns.

- ``high``: arbitrary execution, or data exfiltration (network plus
  file read, file write, or env-var access).
        - ``medium``: network call, subprocess execution, or file write.
        - ``low``: read-only file access or env-var access.
        - ``safe``: no risky patterns.
        """
        pattern_set = set(patterns)

        if "arbitrary_execution" in pattern_set:
            return "high"

        # Data exfiltration: external communication combined with access to
        # private data (file reads, file writes, or environment variables).
        if "network_call" in pattern_set and (
            "file_read" in pattern_set
            or "file_write" in pattern_set
            or "env_var_access" in pattern_set
        ):
            return "high"

        if "network_call" in pattern_set or "subprocess_execution" in pattern_set:
            return "medium"

        if "file_write" in pattern_set:
            return "medium"

        if "file_read" in pattern_set or "env_var_access" in pattern_set:
            return "low"

        return "safe"

    def _recommendations_for(self, patterns: list[str]) -> list[str]:
        """Generate sandbox-hardening recommendations for detected patterns."""
        pattern_set = set(patterns)
        config = self.check_sandbox_config()
        recs: list[str] = []

        if "arbitrary_execution" in pattern_set:
            recs.append(
                "Prohibit dynamic code execution (eval/exec/compile/__import__) "
                "and run the snippet in a fully isolated container."
            )
        if ("file_read" in pattern_set or "file_write" in pattern_set) and not config["filesystem_restricted"]:
            recs.append(
                "Restrict filesystem access to a sandboxed working directory; "
                "deny writes outside it."
            )
        if "file_write" in pattern_set and config["filesystem_restricted"]:
            recs.append(
                "Filesystem is restricted but writes persist: mount the sandbox "
                "on tmpfs so persistent memory cannot survive execution."
            )
        if "network_call" in pattern_set and not config["network_blocked"]:
            recs.append(
                "Block all outbound network connections to prevent data "
                "exfiltration and untrusted content exposure."
            )
        if "subprocess_execution" in pattern_set and not config["subprocess_disabled"]:
            recs.append(
                "Disable subprocess execution or confine it to a seccomp "
                "filter that allows only known-safe binaries."
            )
        if "env_var_access" in pattern_set and not config["env_vars_filtered"]:
            recs.append(
                "Filter sensitive environment variables (API keys, tokens) "
                "before exposing them to agent-generated code."
            )
        if "network_call" in pattern_set and (
            "file_read" in pattern_set
            or "file_write" in pattern_set
            or "env_var_access" in pattern_set
        ):
            recs.append(
                "Deadly triad detected: private data plus external "
                "communication. Enforce both network blocking and data "
                "redaction before execution."
            )
        if not pattern_set:
            recs.append("No risky patterns detected; current sandbox configuration is adequate.")
        return recs

    def _dimension_scores(self) -> dict[str, float]:
        """Score each sandbox dimension on a 0.0-1.0 scale."""
        config = self.check_sandbox_config()
        scores: dict[str, float] = {}
        for dimension, key in _DIMENSION_TO_CONFIG.items():
            scores[dimension] = 1.0 if config[key] else 0.0
        scores["overall_sandbox_score"] = self._overall_score(scores)
        return scores

    @staticmethod
    def _overall_score(dimension_scores: dict[str, float]) -> float:
        """Average the four protection dimensions (excluding the overall key)."""
        keys = [k for k in _DIMENSION_TO_CONFIG if k in dimension_scores]
        if not keys:
            return 0.0
        return round(sum(dimension_scores[k] for k in keys) / len(keys), 4)
