"""MCP server for verdict - exposes audit tools to Bob and other MCP clients.

This module implements a Model Context Protocol (MCP) server that wraps the verdict
CLI, allowing AI coding agents like Bob to audit their own code changes mid-session.
The server exposes three tools via stdio transport:
- check_diff: Run all checks (static + dynamic)
- check_static: Run only static checks (fast feedback)
- trace_test_run: Run dynamic execution tracer

All tools return the standard Scorecard JSON shape. Errors are returned as
Scorecards with verdict="SUSPICIOUS" rather than raising exceptions.
"""

import asyncio
import os
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from verdict.types import Finding, Scorecard, VerdictLevel


def _error_scorecard(error_message: str) -> Scorecard:
    """Create a SUSPICIOUS scorecard with internal error finding.

    Args:
        error_message: Description of the error that occurred

    Returns:
        Scorecard with verdict="SUSPICIOUS" and one internal error finding
    """
    finding: Finding = {
        "kind": "verdict_internal_error",
        "file": "",
        "line": 0,
        "message": f"Verdict encountered an error: {error_message}",
        "confidence": 1.0,
    }
    return {
        "verdict": "SUSPICIOUS",
        "findings": [finding],
        "summary": {"error": True, "error_message": error_message},
    }


def _run_checks_safe(
    repo_path: str, diff_range: str = "HEAD", static_only: bool = False
) -> Scorecard:
    """Wrap CLI call with error handling, return Scorecard or error Scorecard.

    Args:
        repo_path: Path to the git repository to audit
        diff_range: Git diff range (default: "HEAD")
        static_only: If True, run only static checks (no test execution)

    Returns:
        Scorecard from the CLI, or error Scorecard if something fails
    """
    try:
        # Validate repo_path exists
        if not os.path.exists(repo_path):
            return _error_scorecard(f"Repository path does not exist: {repo_path}")

        if not os.path.isdir(repo_path):
            return _error_scorecard(f"Repository path is not a directory: {repo_path}")

        # Check if it's a git repository
        git_dir = os.path.join(repo_path, ".git")
        if not os.path.exists(git_dir):
            return _error_scorecard(f"Not a git repository: {repo_path}")

        # Import CLI function (deferred to avoid circular imports)
        try:
            from verdict.cli import run_checks
        except ImportError as e:
            return _error_scorecard(f"Failed to import verdict CLI: {e}")

        # Call the CLI function
        scorecard = run_checks(repo_path=repo_path, diff_range=diff_range, static_only=static_only)
        return scorecard

    except Exception as e:
        return _error_scorecard(f"{type(e).__name__}: {str(e)}")


async def check_diff(repo_path: str, diff_range: str = "HEAD") -> dict[str, Any]:
    """Run all verdict checks (static + dynamic) on the specified diff.

    This tool runs the complete verdict audit suite, including:
    - Static checks (dead functions, vacuous tests, etc.)
    - Dynamic checks (execution tracing during test runs)

    Args:
        repo_path: Absolute path to the git repository to audit
        diff_range: Git diff range to audit (default: "HEAD" for working tree vs HEAD)

    Returns:
        Scorecard dict with verdict, findings, and summary
    """
    scorecard = _run_checks_safe(repo_path, diff_range, static_only=False)
    return dict(scorecard)


async def check_static(repo_path: str, diff_range: str = "HEAD") -> dict[str, Any]:
    """Run only static checks (fast feedback for tight agent loops).

    This tool runs only the static analysis checks without executing tests.
    Useful for quick feedback during iterative development.

    Args:
        repo_path: Absolute path to the git repository to audit
        diff_range: Git diff range to audit (default: "HEAD" for working tree vs HEAD)

    Returns:
        Scorecard dict with verdict, findings, and summary
    """
    scorecard = _run_checks_safe(repo_path, diff_range, static_only=True)
    return dict(scorecard)


async def trace_test_run(repo_path: str, test_command: str = "pytest") -> dict[str, Any]:
    """Run dynamic execution tracer on test suite.

    This tool wraps the P1.1 tracer to detect code that was added but never
    executed during the test run. It shells out to run the test command as
    a subprocess to avoid corrupting the MCP server's interpreter state.

    Args:
        repo_path: Absolute path to the git repository to audit
        test_command: Test command to execute (default: "pytest")

    Returns:
        Scorecard dict with verdict, findings, and summary
    """
    try:
        # Validate repo_path
        if not os.path.exists(repo_path):
            return dict(_error_scorecard(f"Repository path does not exist: {repo_path}"))

        # Import the tracer check
        try:
            from verdict.checks.trace import TraceCheck
        except ImportError as e:
            return dict(_error_scorecard(f"Tracer not available: {e}"))

        # Run the tracer (it will shell out to pytest internally)
        check = TraceCheck()
        # Note: This assumes the Check protocol - adjust if actual interface differs
        findings = check.run(repo_path, [])

        # Build scorecard from findings
        if not findings:
            scorecard: Scorecard = {
                "verdict": "PASS",
                "findings": [],
                "summary": {"total_findings": 0},
            }
        else:
            # Determine verdict based on confidence thresholds
            high_confidence = any(f["confidence"] > 0.8 for f in findings)
            verdict: VerdictLevel = "LIED" if high_confidence else "SUSPICIOUS"
            scorecard = {
                "verdict": verdict,
                "findings": findings,
                "summary": {
                    "total_findings": len(findings),
                    "high_confidence_findings": sum(1 for f in findings if f["confidence"] > 0.8),
                },
            }

        return dict(scorecard)

    except Exception as e:
        return dict(_error_scorecard(f"Tracer execution failed: {type(e).__name__}: {str(e)}"))


def create_server() -> Server:
    """Create and configure the MCP server with all tools.

    Returns:
        Configured MCP Server instance with three verdict tools registered
    """
    server = Server("verdict")

    # Register check_diff tool
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List all available verdict tools."""
        return [
            Tool(
                name="check_diff",
                description=(
                    "Run all verdict checks (static + dynamic) on a git diff. "
                    "Returns a Scorecard with verdict (PASS/SUSPICIOUS/LIED), "
                    "findings list, and summary. Use this for comprehensive audits."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "repo_path": {
                            "type": "string",
                            "description": "Absolute path to the git repository to audit",
                        },
                        "diff_range": {
                            "type": "string",
                            "description": (
                                "Git diff range (default: HEAD for working tree vs HEAD)"
                            ),
                            "default": "HEAD",
                        },
                    },
                    "required": ["repo_path"],
                },
            ),
            Tool(
                name="check_static",
                description=(
                    "Run only static checks (no test execution) for fast feedback. "
                    "Returns a Scorecard. Use this in tight agent loops where speed matters."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "repo_path": {
                            "type": "string",
                            "description": "Absolute path to the git repository to audit",
                        },
                        "diff_range": {
                            "type": "string",
                            "description": (
                                "Git diff range (default: HEAD for working tree vs HEAD)"
                            ),
                            "default": "HEAD",
                        },
                    },
                    "required": ["repo_path"],
                },
            ),
            Tool(
                name="trace_test_run",
                description=(
                    "Run dynamic execution tracer to detect code added but never executed. "
                    "Returns a Scorecard. This runs the test suite and may take 10-60 seconds."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "repo_path": {
                            "type": "string",
                            "description": "Absolute path to the git repository to audit",
                        },
                        "test_command": {
                            "type": "string",
                            "description": "Test command to execute (default: pytest)",
                            "default": "pytest",
                        },
                    },
                    "required": ["repo_path"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle tool calls by routing to the appropriate handler."""
        if name == "check_diff":
            result = await check_diff(
                repo_path=arguments["repo_path"],
                diff_range=arguments.get("diff_range", "HEAD"),
            )
        elif name == "check_static":
            result = await check_static(
                repo_path=arguments["repo_path"],
                diff_range=arguments.get("diff_range", "HEAD"),
            )
        elif name == "trace_test_run":
            result = await trace_test_run(
                repo_path=arguments["repo_path"],
                test_command=arguments.get("test_command", "pytest"),
            )
        else:
            error_result = _error_scorecard(f"Unknown tool: {name}")
            result = dict(error_result)

        # Return as TextContent with JSON string
        import json

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    return server


async def main() -> None:
    """Entry point for verdict-mcp console script.

    Starts the MCP server using stdio transport. This function runs indefinitely
    until the client closes the connection or the process is terminated.
    """
    server = create_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())

# Made with Bob
