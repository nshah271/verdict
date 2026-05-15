"""Shared type contracts for verdict.

Every check, the CLI, and the MCP server code against these interfaces so the
four-person team can build in parallel without blocking on each other's
implementations. Do not modify these shapes silently; discuss in Discord first.
"""

from typing import Literal, Protocol, TypedDict


class ChangedFile(TypedDict):
    path: str
    added_lines: list[int]
    removed_lines: list[int]


class AddedFunction(TypedDict):
    file: str
    name: str
    line: int
    end_line: int
    is_test: bool
    decorators: list[str]


class Finding(TypedDict):
    kind: str  # e.g. "dead_function", "vacuous_test"
    file: str
    line: int
    message: str
    confidence: float


VerdictLevel = Literal["PASS", "SUSPICIOUS", "LIED"]


class Scorecard(TypedDict):
    verdict: VerdictLevel
    findings: list[Finding]
    summary: dict


class Check(Protocol):
    """All checks implement this interface."""

    name: str

    def run(
        self, diff_root: str, added_functions: list[AddedFunction]
    ) -> list[Finding]: ...
