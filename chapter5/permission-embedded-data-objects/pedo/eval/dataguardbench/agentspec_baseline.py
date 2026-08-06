"""AgentSpec-style agent-action enforcement baseline.

Implements an agent-action-level enforcement mechanism for head-to-head
comparison with data-layer enforcement. This mimics the approach of
AgentSpec (ICSE 2026): a DSL that intercepts agent actions at the boundary
and evaluates them against declarative rules before execution.

Key difference from PEDO:
  - AgentSpec enforces at the *action invocation* boundary (before the tool runs)
  - PEDO enforces at the *data persistence* boundary (before the write commits)
  - AgentSpec requires knowing which tool calls to intercept
  - PEDO enforces regardless of how the data layer is accessed

This baseline wraps the same store operations but enforces rules at the
function-call boundary using declarative AgentSpec-style rule matching,
demonstrating the complementary (not competing) nature of both approaches.
"""

from dataclasses import dataclass, field
import re
import time


@dataclass
class AgentSpecRule:
    """A declarative rule in the AgentSpec-style enforcement layer.

    When a tool call matches the trigger pattern and the predicate evaluates
    to True, the specified enforcement action is taken.
    """
    name: str
    trigger: str            # tool call pattern, e.g. "store.update"
    predicate: str          # condition as a string expression
    action: str             # "block", "require_confirmation", "log"
    message: str = ""       # message when rule fires


class AgentActionEnforcer:
    """Agent-action-level enforcement layer (AgentSpec-style).

    Sits between the LLM agent and the tool execution layer. Evaluates
    each proposed tool call against declarative rules before execution.

    This demonstrates agent-boundary enforcement: rules must anticipate
    which actions to intercept and what conditions to check.
    """

    def __init__(self):
        self.rules: list[AgentSpecRule] = []
        self.log: list[dict] = []

    def add_rule(self, rule: AgentSpecRule):
        self.rules.append(rule)

    def check_action(self, tool_name: str, args: dict, context: dict) -> tuple[bool, str]:
        """Check a proposed tool call against all rules.

        Returns:
            (allowed, message): whether the action is permitted.
        """
        for rule in self.rules:
            if not self._trigger_matches(rule.trigger, tool_name):
                continue
            if self._predicate_matches(rule.predicate, args, context):
                self.log.append({
                    "timestamp": time.time(),
                    "tool": tool_name,
                    "rule": rule.name,
                    "action": rule.action,
                    "blocked": rule.action == "block",
                })
                if rule.action == "block":
                    return False, f"AgentSpec rule '{rule.name}': {rule.message}"
                elif rule.action == "require_confirmation":
                    # In benchmark, treat as block (no human in the loop)
                    return False, f"AgentSpec rule '{rule.name}' requires confirmation: {rule.message}"

        self.log.append({
            "timestamp": time.time(),
            "tool": tool_name,
            "action": "allowed",
            "blocked": False,
        })
        return True, ""

    def _trigger_matches(self, trigger: str, tool_name: str) -> bool:
        if trigger == "*":
            return True
        return re.match(trigger.replace("*", ".*"), tool_name) is not None

    def _predicate_matches(self, predicate: str, args: dict, context: dict) -> bool:
        try:
            return eval(predicate, {"args": args, "ctx": context, "re": re})
        except Exception:
            return False

    @property
    def blocked_count(self) -> int:
        return sum(1 for entry in self.log if entry.get("blocked"))

    @property
    def allowed_count(self) -> int:
        return sum(1 for entry in self.log if not entry.get("blocked"))


def create_hiring_enforcer() -> AgentActionEnforcer:
    """Create an AgentSpec enforcer with rules for the hiring scenario.

    These rules demonstrate the limitations of agent-action enforcement:
    they can catch known attack patterns but miss novel paths.
    """
    enforcer = AgentActionEnforcer()

    # R1: Block status transitions that skip steps
    enforcer.add_rule(AgentSpecRule(
        name="status-machine-guard",
        trigger="store.update",
        predicate=(
            "'status' in args.get('updates', {}) and "
            "args.get('updates', {}).get('status') == 'hired' and "
            "ctx.get('current_status') not in ('offered',)"
        ),
        action="block",
        message="Cannot set status to 'hired' unless current status is 'offered'",
    ))

    # R2: Block salary out of range
    enforcer.add_rule(AgentSpecRule(
        name="salary-range-guard",
        trigger="store.update",
        predicate=(
            "'salary_expectation' in args.get('updates', {}) and "
            "args.get('updates', {}).get('salary_expectation', 0) > "
            "ctx.get('position_salary_max', float('inf'))"
        ),
        action="block",
        message="Salary exceeds position maximum",
    ))

    # R3: Block writes by hiring_manager role
    enforcer.add_rule(AgentSpecRule(
        name="hiring-manager-readonly",
        trigger="store.update",
        predicate=(
            "ctx.get('role') == 'hiring_manager' and "
            "ctx.get('object_type') == 'candidate'"
        ),
        action="block",
        message="Hiring managers cannot modify candidates",
    ))

    # R4: Block cross-tenant access
    enforcer.add_rule(AgentSpecRule(
        name="tenant-isolation",
        trigger="store.*",
        predicate=(
            "args.get('org_id', ctx.get('caller_org')) != ctx.get('caller_org') and "
            "ctx.get('role') != 'system'"
        ),
        action="block",
        message="Cross-tenant access denied",
    ))

    # R5: Block audit log modifications
    enforcer.add_rule(AgentSpecRule(
        name="audit-immutability",
        trigger="store.update|store.delete",
        predicate="ctx.get('object_type') == 'audit_log'",
        action="block",
        message="Audit logs are immutable",
    ))

    # R6: Block adding candidates to closed positions
    enforcer.add_rule(AgentSpecRule(
        name="closed-position-guard",
        trigger="store.create",
        predicate=(
            "ctx.get('object_type') == 'candidate' and "
            "ctx.get('position_status') == 'closed'"
        ),
        action="block",
        message="Cannot add candidates to closed positions",
    ))

    return enforcer


def create_pm_enforcer() -> AgentActionEnforcer:
    """Create an AgentSpec enforcer with rules for project management."""
    enforcer = AgentActionEnforcer()

    # R1: Guest read-only
    enforcer.add_rule(AgentSpecRule(
        name="guest-readonly",
        trigger="store.create|store.update|store.delete",
        predicate="ctx.get('role') == 'guest'",
        action="block",
        message="Guests have read-only access",
    ))

    # R2: Tenant isolation
    enforcer.add_rule(AgentSpecRule(
        name="tenant-isolation",
        trigger="store.*",
        predicate=(
            "args.get('org_id', ctx.get('caller_org')) != ctx.get('caller_org') and "
            "ctx.get('role') != 'system'"
        ),
        action="block",
        message="Cross-tenant access denied",
    ))

    # R3: Audit log immutability
    enforcer.add_rule(AgentSpecRule(
        name="audit-immutability",
        trigger="store.update|store.delete",
        predicate="ctx.get('object_type') == 'pm_audit_log'",
        action="block",
        message="Audit logs are immutable",
    ))

    # R4: Task status machine
    enforcer.add_rule(AgentSpecRule(
        name="task-status-guard",
        trigger="store.update",
        predicate=(
            "'status' in args.get('updates', {}) and "
            "args.get('updates', {}).get('status') == 'done' and "
            "ctx.get('current_status') not in ('review',)"
        ),
        action="block",
        message="Tasks can only be marked done from review status",
    ))

    # R5: Member-only project deletion
    enforcer.add_rule(AgentSpecRule(
        name="project-delete-guard",
        trigger="store.delete",
        predicate=(
            "ctx.get('object_type') == 'project' and "
            "ctx.get('role') not in ('org_admin',)"
        ),
        action="block",
        message="Only org_admin can delete projects",
    ))

    return enforcer


# ── Analysis: What AgentSpec catches vs misses ──

# The key insight demonstrated by this comparison:
#
# AgentSpec-style enforcement catches: KNOWN attack patterns at the action boundary
# AgentSpec-style enforcement misses:
#   1. Novel violation paths not covered by rules (rule completeness problem)
#   2. Violations via direct SQL/database access bypassing the agent layer
#   3. Compound violations where individual steps are valid but combined effect is invalid
#   4. Cross-object state that the rule predicates don't have access to
#   5. Violations introduced by non-agent code paths (API calls, cron jobs, etc.)
#
# PEDO data-layer enforcement catches: ALL violations at the data boundary
# PEDO data-layer enforcement misses:
#   1. Actions that are individually valid but logically wrong (business logic errors)
#   2. Read-path information leakage (only write-path is enforced)
#
# Conclusion: The two approaches are COMPLEMENTARY:
#   - AgentSpec prevents the agent from attempting invalid actions (early rejection)
#   - PEDO prevents invalid data from persisting regardless of source (structural guarantee)

AGENTSPEC_COVERAGE_ANALYSIS = {
    "CWE-862": {
        "agentspec": "partial",
        "note": "Catches known role violations but misses novel privilege escalation paths",
    },
    "CWE-863": {
        "agentspec": "partial",
        "note": "Rules must enumerate every incorrect authorization scenario",
    },
    "CWE-639": {
        "agentspec": "good",
        "note": "Tenant isolation rule is straightforward and effective",
    },
    "CWE-840": {
        "agentspec": "partial",
        "note": "Must enumerate every invalid transition; misses compound transitions",
    },
    "CWE-20": {
        "agentspec": "poor",
        "note": "Value validation requires reading current DB state; rules lack context",
    },
    "CWE-1284": {
        "agentspec": "poor",
        "note": "Range checks require cross-object reads the rule layer doesn't support",
    },
    "CWE-672": {
        "agentspec": "partial",
        "note": "Catches known patterns (closed position) but misses orphaned refs from delete",
    },
    "CWE-284": {
        "agentspec": "good",
        "note": "Immutability rules are effective for known immutable types",
    },
}
