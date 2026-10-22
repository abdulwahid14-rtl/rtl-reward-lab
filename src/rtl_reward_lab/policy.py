"""Check the permitted RTL subset."""

from __future__ import annotations

import dataclasses
import re

ALLOWED_TOP_MODULE = "TopModule"

_MODULE_DECL_RE = re.compile(r"\bmodule\s+(\w+)")
_FORBIDDEN_PATTERNS = (
    (re.compile(r"\$system\b"), "$system calls are not permitted"),
    (
        re.compile(r"\$fopen\b|\$fwrite\b|\$fclose\b|\$fdisplay\b|\$fscanf\b"),
        "file I/O system calls are not permitted",
    ),
    (re.compile(r"\$readmemh\b|\$readmemb\b"), "memory-load system calls are not permitted"),
    (re.compile(r"^\s*`include\b", re.MULTILINE), "`include directives are not permitted"),
    (re.compile(r"\$finish\b"), "$finish is reserved for the trusted testbench"),
    (re.compile(r"\$stop\b"), "$stop is reserved for the trusted testbench"),
)


@dataclasses.dataclass(frozen=True)
class PolicyResult:
    """Outcome of checking a candidate against the permitted RTL subset."""

    allowed: bool
    violations: tuple[str, ...]


def check_policy(source: str) -> PolicyResult:
    """Reject candidates that use disallowed constructs or declare
    anything other than the single expected top module.

    This exists to stop evaluator-manipulating submissions: a candidate
    must not redefine the reference module or testbench, escape to the
    file system or shell, or force the simulation to finish/stop on its
    own terms.
    """

    violations = []

    for name in _MODULE_DECL_RE.findall(source):
        if name != ALLOWED_TOP_MODULE:
            violations.append(f"candidate must only define '{ALLOWED_TOP_MODULE}', found module '{name}'")

    for pattern, message in _FORBIDDEN_PATTERNS:
        if pattern.search(source):
            violations.append(message)

    return PolicyResult(allowed=len(violations) == 0, violations=tuple(violations))
