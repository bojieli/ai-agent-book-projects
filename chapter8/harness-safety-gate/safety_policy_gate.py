"""
Safety Policy Gate Module.

Inspects tool call parameters against security rules (path traversal, dangerous bash commands,
resource limits). Enforces confirmation gates for high-risk operations and triggers automated state
rollbacks on safety violations.
"""

import hashlib
import hmac
import re
import urllib.parse
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union


@dataclass
class SafetyGateDecision:
    """Represents the safety evaluation decision for a tool call."""
    allowed: bool
    requires_confirmation: bool = False
    triggered_rollback: bool = False
    violation_type: Optional[str] = None
    reason: Optional[str] = None
    risk_score: float = 0.0
    confirmation_token: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert decision to dictionary representation."""
        return {
            "allowed": self.allowed,
            "requires_confirmation": self.requires_confirmation,
            "triggered_rollback": self.triggered_rollback,
            "violation_type": self.violation_type,
            "reason": self.reason,
            "risk_score": self.risk_score,
            "confirmation_token": self.confirmation_token,
            "details": self.details,
        }


class SafetyPolicyGate:
    """Harness Safety Policy Gate for tool call security inspection and confirmation."""

    # Patterns for detecting path traversal attempts
    PATH_TRAVERSAL_PATTERNS = [
        re.compile(r'\.\.[/\\]'),                           # ../ or ..\
        re.compile(r'%2e%2e', re.IGNORECASE),               # URL-encoded ..
        re.compile(r'\x00|%00'),                            # Null bytes
        re.compile(r'/(etc|var/log|sys|proc|boot|dev|root)(?:/|$)', re.IGNORECASE), # Sensitive Linux dirs
        re.compile(r'~/(?:\.ssh|\.aws|\.gnupg|\.bashrc|\.zshrc)', re.IGNORECASE), # Sensitive user configs
        re.compile(r'^[a-zA-Z]:\\(Windows|System32|Program Files)', re.IGNORECASE), # Sensitive Windows dirs
    ]

    # Patterns for detecting dangerous bash / shell commands
    DANGEROUS_COMMAND_PATTERNS = [
        (re.compile(r'\brm\s+-[rfRF]+\b|\brm\s+--recursive\b', re.IGNORECASE), "Recursive file deletion command"),
        (re.compile(r'\bmkfs\b|\bdd\s+if=|\b>\s*/dev/sd[a-z]', re.IGNORECASE), "Disk formatting / raw write command"),
        (re.compile(r'\b(shutdown|reboot|poweroff|init\s+[06])\b', re.IGNORECASE), "System lifecycle control command"),
        (re.compile(r'\bchmod\s+(-R\s+)?777\b|\bchown\s+(-R\s+)?root\b', re.IGNORECASE), "Dangerous permissions modification"),
        (re.compile(r'\b(curl|wget)\s+.*\|\s*(ba)?sh\b', re.IGNORECASE), "Remote code execution via pipe to shell"),
        (re.compile(r':\(\)\s*\{\s*:\|:&\s*\};:', re.IGNORECASE), "Fork bomb command"),
        (re.compile(r'\b(pkill\s+-9|killall\s+-9)\b', re.IGNORECASE), "Unselective process killing command"),
    ]

    # Patterns for destructive SQL queries
    DESTRUCTIVE_SQL_DROP = re.compile(r'\b(DROP\s+TABLE|DROP\s+DATABASE|TRUNCATE)\b', re.IGNORECASE)
    DESTRUCTIVE_SQL_DELETE = re.compile(r'\bDELETE\s+FROM\b', re.IGNORECASE)
    SQL_WHERE_CLAUSE = re.compile(r'\bWHERE\b', re.IGNORECASE)

    def __init__(
        self,
        max_timeout: float = 600.0,
        max_tokens: int = 100000,
        max_file_bytes: int = 50 * 1024 * 1024,
        max_memory_mb: int = 8192,
        max_threads: int = 16,
        secret_key: Optional[str] = None,
    ):
        """Initialize SafetyPolicyGate with configurable resource limits and secret key."""
        self.max_timeout = max_timeout
        self.max_tokens = max_tokens
        self.max_file_bytes = max_file_bytes
        self.max_memory_mb = max_memory_mb
        self.max_threads = max_threads
        if secret_key is None:
            import os, secrets
            secret_key = os.environ.get("SAFETY_GATE_SECRET_KEY") or secrets.token_hex(16)
        self.secret_key = secret_key
        # Active pending confirmation tokens: token -> fingerprint
        self._pending_confirmations: Dict[str, str] = {}
        # Registered rollback handlers
        self._rollback_handlers: List[Callable[[], None]] = []
        # State snapshot history
        self._snapshots: List[Dict[str, Any]] = []

    def register_rollback_handler(self, handler: Callable[[], None]) -> None:
        """Register a callback function to be executed when state rollback is triggered."""
        self._rollback_handlers.append(handler)

    def create_snapshot(self, state: Dict[str, Any]) -> int:
        """Create a state snapshot and return snapshot index."""
        self._snapshots.append(state.copy())
        return len(self._snapshots) - 1

    def trigger_rollback(self) -> bool:
        """Trigger automated state rollback by invoking all registered rollback handlers."""
        success = True
        for handler in self._rollback_handlers:
            try:
                handler()
            except Exception:
                success = False
        return success

    def _fingerprint(self, tool_name: str, params: Dict[str, Any]) -> str:
        """Generate a canonical SHA256 fingerprint for a tool call and its parameters."""
        import json
        canonical = json.dumps({"tool": tool_name, "params": params or {}}, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def issue_confirmation(self, tool_name: str, params: Dict[str, Any]) -> str:
        """Generate a single-use HMAC confirmation token bound to tool name and parameters."""
        fp = self._fingerprint(tool_name, params)
        token = hmac.new(self.secret_key.encode("utf-8"), fp.encode("utf-8"), hashlib.sha256).hexdigest()[:24]
        self._pending_confirmations[token] = fp
        return token

    def verify_confirmation(self, token: str, tool_name: str, params: Dict[str, Any]) -> bool:
        """Verify and consume a single-use confirmation token."""
        if not token or token not in self._pending_confirmations:
            return False
        expected_fp = self._pending_confirmations[token]
        actual_fp = self._fingerprint(tool_name, params)
        if hmac.compare_digest(expected_fp, actual_fp):
            # Consume token to enforce single-use constraint
            del self._pending_confirmations[token]
            return True
        return False

    def _extract_string_values(self, obj: Any) -> List[str]:
        """Recursively extract all string values from a nested data structure."""
        strings = []
        if isinstance(obj, str):
            strings.append(obj)
        elif isinstance(obj, dict):
            for v in obj.values():
                strings.extend(self._extract_string_values(v))
        elif isinstance(obj, (list, tuple, set)):
            for item in obj:
                strings.extend(self._extract_string_values(item))
        return strings

    def inspect_path_traversal(self, params: Dict[str, Any]) -> Optional[str]:
        """Inspect parameters for path traversal vulnerabilities."""
        if not isinstance(params, dict):
            return None
        strings = self._extract_string_values(params)
        for s in strings:
            decoded = urllib.parse.unquote(s)
            for pattern in self.PATH_TRAVERSAL_PATTERNS:
                if pattern.search(s) or pattern.search(decoded):
                    return f"Path traversal attack detected in parameter value: '{s}'"
        return None

    def inspect_dangerous_commands(self, tool_name: str, params: Dict[str, Any]) -> Optional[str]:
        """Inspect parameters for dangerous bash/shell command patterns."""
        if not isinstance(params, dict):
            return None
        # Check command string parameters
        cmd_keys = {"command", "cmd", "script", "bash", "shell", "exec", "args"}
        cmd_strings = []
        
        for k, v in params.items():
            if k in cmd_keys or "command" in k.lower() or "shell" in k.lower():
                cmd_strings.extend(self._extract_string_values(v))
        
        if tool_name in ("run_shell", "bash", "execute_command", "shell"):
            cmd_strings.extend(self._extract_string_values(params))
        for cmd_str in cmd_strings:
            for pattern, reason in self.DANGEROUS_COMMAND_PATTERNS:
                if pattern.search(cmd_str):
                    return f"{reason}: '{cmd_str}'"

        return None

    def inspect_resource_limits(self, params: Dict[str, Any]) -> Optional[str]:
        """Inspect parameters against predefined resource limit boundaries."""
        if not isinstance(params, dict):
            return None

        # Check timeout limit
        timeout = params.get("timeout")
        if isinstance(timeout, (int, float)) and timeout > self.max_timeout:
            return f"Timeout of {timeout}s exceeds maximum limit of {self.max_timeout}s"

        # Check max tokens limit
        tokens = params.get("max_tokens") or params.get("tokens")
        if isinstance(tokens, (int, float)) and tokens > self.max_tokens:
            return f"Requested tokens {tokens} exceeds maximum limit of {self.max_tokens}"

        # Check file size limit
        file_bytes = params.get("file_size") or params.get("bytes")
        if isinstance(file_bytes, (int, float)) and file_bytes > self.max_file_bytes:
            return f"Requested file size {file_bytes} bytes exceeds maximum limit of {self.max_file_bytes} bytes"

        # Check memory limit
        memory_mb = params.get("memory_mb") or params.get("memory")
        if isinstance(memory_mb, (int, float)) and memory_mb > self.max_memory_mb:
            return f"Requested memory {memory_mb}MB exceeds maximum limit of {self.max_memory_mb}MB"

        # Check thread/process limit
        threads = params.get("threads") or params.get("processes")
        if isinstance(threads, (int, float)) and threads > self.max_threads:
            return f"Requested threads {threads} exceeds maximum limit of {self.max_threads}"

        return None

    def is_high_risk_operation(self, tool_name: str, params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Determine if a tool call is a high-risk operation requiring explicit confirmation."""
        if not isinstance(params, dict):
            params = {}
        # Deletion tools
        if tool_name in ("delete_file", "remove_directory", "rmdir", "unlink", "wipe_cache", "system_reset"):
            return True, f"Operation '{tool_name}' is destructive and requires user confirmation"

        # Git force push
        if tool_name in ("git_push", "git") and params.get("force"):
            return True, "Force push will overwrite remote repository history"

        # Destructive SQL queries
        if tool_name in ("sql_query", "db_execute", "execute_sql"):
            raw_query = str(params.get("query", "") or params.get("sql", ""))
            # Strip single-line comments (-- ...) and multi-line comments (/* ... */)
            clean_query = re.sub(r'--.*$', '', raw_query, flags=re.MULTILINE)
            clean_query = re.sub(r'/\*.*?\*/', '', clean_query, flags=re.DOTALL)
            statements = [s.strip() for s in clean_query.split(";") if s.strip()]
            for stmt in statements:
                if self.DESTRUCTIVE_SQL_DROP.search(stmt):
                    return True, "DROP/TRUNCATE query will destroy database tables or schema"
                if self.DESTRUCTIVE_SQL_DELETE.search(stmt) and not self.SQL_WHERE_CLAUSE.search(stmt):
                    return True, "DELETE query without WHERE clause will purge all records in table"

        return False, None

    def validate_tool_call(
        self,
        tool_name: str,
        params: Optional[Dict[str, Any]] = None,
        confirm_token: Optional[str] = None,
        user_confirmed: bool = False,
    ) -> SafetyGateDecision:
        """Inspect and validate a tool call against security rules and confirmation policies.
        
        Args:
            tool_name: Name of the tool being called.
            params: Parameters dictionary passed to the tool.
            confirm_token: Optional confirmation token for high-risk operations.
            user_confirmed: Boolean flag indicating explicit user confirmation.
            
        Returns:
            SafetyGateDecision detailing allow/deny status, confirmation needs, or rollback triggers.
        """
        params = params if params is not None else {}

        # 1. Inspect Path Traversal (Critical Violation)
        pt_violation = self.inspect_path_traversal(params)
        if pt_violation:
            self.trigger_rollback()
            return SafetyGateDecision(
                allowed=False,
                requires_confirmation=False,
                triggered_rollback=True,
                violation_type="path_traversal",
                reason=pt_violation,
                risk_score=1.0,
                details={"tool_name": tool_name, "params": params},
            )

        # 2. Inspect Dangerous Bash Commands (Critical Violation)
        cmd_violation = self.inspect_dangerous_commands(tool_name, params)
        if cmd_violation:
            self.trigger_rollback()
            return SafetyGateDecision(
                allowed=False,
                requires_confirmation=False,
                triggered_rollback=True,
                violation_type="dangerous_bash_command",
                reason=cmd_violation,
                risk_score=1.0,
                details={"tool_name": tool_name, "params": params},
            )

        # 3. Inspect Resource Limits
        res_violation = self.inspect_resource_limits(params)
        if res_violation:
            return SafetyGateDecision(
                allowed=False,
                requires_confirmation=False,
                triggered_rollback=False,
                violation_type="resource_limit_exceeded",
                reason=res_violation,
                risk_score=0.8,
                details={"tool_name": tool_name, "params": params},
            )

        # 4. Inspect High-Risk Operation Confirmation
        is_high_risk, risk_reason = self.is_high_risk_operation(tool_name, params)
        if is_high_risk:
            token_to_check = confirm_token or params.get("confirm_token")
            # Verify if user confirmed or valid confirmation token provided
            if user_confirmed or params.get("user_confirmed") is True:
                return SafetyGateDecision(
                    allowed=True,
                    requires_confirmation=False,
                    triggered_rollback=False,
                    reason="High-risk operation explicitly confirmed by user",
                    risk_score=0.5,
                    details={"tool_name": tool_name, "params": params, "confirmed": True},
                )
            elif token_to_check and self.verify_confirmation(str(token_to_check), tool_name, params):
                return SafetyGateDecision(
                    allowed=True,
                    requires_confirmation=False,
                    triggered_rollback=False,
                    reason="High-risk operation confirmed with valid token",
                    risk_score=0.5,
                    details={"tool_name": tool_name, "params": params, "confirmed": True},
                )
            else:
                # Require confirmation gate
                new_token = self.issue_confirmation(tool_name, params)
                return SafetyGateDecision(
                    allowed=False,
                    requires_confirmation=True,
                    triggered_rollback=False,
                    violation_type="unconfirmed_high_risk_operation",
                    reason=risk_reason,
                    risk_score=0.7,
                    confirmation_token=new_token,
                    details={"tool_name": tool_name, "params": params},
                )

        # 5. Low Risk Operation: Allow
        return SafetyGateDecision(
            allowed=True,
            requires_confirmation=False,
            triggered_rollback=False,
            reason="Tool call validated successfully",
            risk_score=0.1,
            details={"tool_name": tool_name, "params": params},
        )


# Global default gate instance for entrypoint calls
_DEFAULT_GATE = SafetyPolicyGate()


def validate_tool_call(
    tool_name: str,
    params: Optional[Dict[str, Any]] = None,
    gate: Optional[SafetyPolicyGate] = None,
    confirm_token: Optional[str] = None,
    user_confirmed: bool = False,
) -> SafetyGateDecision:
    """Module-level entrypoint for validating a tool call against safety policy rules.
    
    Args:
        tool_name: Name of the tool being executed.
        params: Parameters dictionary.
        gate: Optional custom SafetyPolicyGate instance.
        confirm_token: Optional confirmation token.
        user_confirmed: Optional user confirmation flag.
        
    Returns:
        SafetyGateDecision object.
    """
    target_gate = gate or _DEFAULT_GATE
    return target_gate.validate_tool_call(
        tool_name=tool_name,
        params=params,
        confirm_token=confirm_token,
        user_confirmed=user_confirmed,
    )
