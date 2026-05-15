"""CLI entry point for verdict.

This module provides the command-line interface for verdict, including:
- verdict run: Run checks on a git diff
- verdict mcp install: Install the MCP server into Bob's configuration
"""

import json
import os
import platform
import sys
from pathlib import Path

import click

from verdict.types import Scorecard


def get_mcp_config_path() -> Path:
    """Get the platform-specific path to Bob's MCP configuration file.

    Returns:
        Path to mcp_settings.json for the current platform
    """
    system = platform.system()

    if system == "Windows":
        appdata = os.environ.get("APPDATA")
        if not appdata:
            raise RuntimeError("APPDATA environment variable not set")
        return Path(appdata) / "Bob" / "mcp_settings.json"
    elif system == "Darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "Bob" / "mcp_settings.json"
    else:  # Linux and others
        return Path.home() / ".config" / "Bob" / "mcp_settings.json"


def install_mcp_server() -> None:
    """Install verdict MCP server into Bob's configuration.

    This function:
    1. Locates Bob's MCP config file (platform-specific)
    2. Loads existing config or creates new structure
    3. Adds/updates the verdict server entry
    4. Writes back atomically
    5. Also creates a portable claude_desktop_config.json
    """
    try:
        # Get config path
        config_path = get_mcp_config_path()
        click.echo(f"Installing verdict MCP server to: {config_path}")

        # Create directory if it doesn't exist
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing config or create new
        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                config = json.load(f)
            click.echo("Loaded existing MCP configuration")
        else:
            config = {"mcpServers": {}}
            click.echo("Creating new MCP configuration")

        # Ensure mcpServers key exists
        if "mcpServers" not in config:
            config["mcpServers"] = {}

        # Add/update verdict server entry
        config["mcpServers"]["verdict"] = {
            "command": "verdict-mcp",
            "args": [],
            "env": {},
        }

        # Write back atomically (write to temp, then rename)
        temp_path = config_path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
            f.write("\n")  # Add trailing newline

        # Atomic rename
        temp_path.replace(config_path)
        click.echo("✓ Verdict MCP server installed successfully")

        # Also create a portable claude_desktop_config.json
        portable_config = {
            "mcpServers": {
                "verdict": {
                    "command": "verdict-mcp",
                    "args": [],
                    "env": {},
                }
            }
        }

        portable_path = Path.cwd() / "claude_desktop_config.json"
        with open(portable_path, "w", encoding="utf-8") as f:
            json.dump(portable_config, f, indent=2)
            f.write("\n")

        click.echo(f"✓ Portable config written to: {portable_path}")
        click.echo("\nTo verify installation:")
        click.echo("1. Restart Bob")
        click.echo("2. Check that 'verdict' tools appear in Bob's tool list")
        click.echo("3. Try calling check_diff on a repository")

    except Exception as e:
        click.echo(f"✗ Installation failed: {e}", err=True)
        sys.exit(1)


def run_checks(repo_path: str, diff_range: str = "HEAD", static_only: bool = False) -> Scorecard:
    """Run verdict checks and return scorecard.

    This is a placeholder implementation that will be replaced by P0.4.
    For now, it returns a minimal PASS scorecard.

    Args:
        repo_path: Path to the git repository to audit
        diff_range: Git diff range to audit (default: "HEAD")
        static_only: If True, run only static checks (no test execution)

    Returns:
        Scorecard with verdict, findings, and summary
    """
    # Placeholder implementation - will be replaced by P0.4
    return {
        "verdict": "PASS",
        "findings": [],
        "summary": {
            "total_findings": 0,
            "static_only": static_only,
            "diff_range": diff_range,
        },
    }


@click.group()
def cli() -> None:
    """Verdict - a lie detector for AI coding agents."""
    pass


@cli.command()
@click.argument("repo_path", type=click.Path(exists=True), default=".")
@click.option(
    "--diff-range",
    default="HEAD",
    help="Git diff range to audit (default: HEAD for working tree vs HEAD)",
)
@click.option(
    "--static-only",
    is_flag=True,
    help="Run only static checks (no test execution)",
)
def run(repo_path: str, diff_range: str, static_only: bool) -> None:
    """Run verdict checks on a git diff.

    This is a placeholder implementation that will be replaced by P0.4.
    """
    click.echo(f"Running verdict on {repo_path} (diff: {diff_range})")
    if static_only:
        click.echo("Mode: static checks only")

    scorecard = run_checks(repo_path, diff_range, static_only)
    click.echo(f"\nVerdict: {scorecard['verdict']}")
    click.echo(f"Findings: {len(scorecard['findings'])}")


@cli.command()
def mcp_install() -> None:
    """Install verdict MCP server into Bob's configuration.

    This command:
    - Locates Bob's MCP config file (platform-specific)
    - Adds the verdict server entry
    - Creates a portable config for other MCP clients
    """
    install_mcp_server()


if __name__ == "__main__":
    cli()

# Made with Bob
