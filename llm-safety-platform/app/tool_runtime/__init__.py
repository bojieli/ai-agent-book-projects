"""Tool runtime public exports (avoid importing runtime from policy.binding)."""

from app.tool_runtime.risk_classifier import RiskAssessment, ToolRiskClassifier, ToolRiskRule

__all__ = [
    "RiskAssessment",
    "ToolRiskClassifier",
    "ToolRiskRule",
]


def __getattr__(name: str):
    if name in {
        "PLATFORM_TOOL_DENYLIST",
        "ConfirmRequiredError",
        "ToolRuntime",
    }:
        from app.tool_runtime import runtime as _rt

        return getattr(_rt, name)
    raise AttributeError(name)
