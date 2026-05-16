"""CLI entry point for verdict.

This module provides the command-line interface for verdict, including:
- verdict run: Run checks on a git diff
- verdict mcp install: Install the MCP server into Bob's configuration
- verdict bob-mode install: Install Bob Custom Mode and slash command
"""

import importlib
import json
import pkgutil
import shutil
import sys
from pathlib import Path

import click

import verdict.checks
from verdict.ast_utils import get_added_functions
from verdict.diff import get_changed_files
from verdict.report import build_scorecard, format_json, format_terminal
from verdict.types import Check, Scorecard


def get_global_mcp_config_path() -> Path:
    """Get the path to Bob's global MCP configuration file.

    Returns:
        Path to global mcp_settings.json (~/.bob/settings/mcp_settings.json on all platforms)
    """
    return Path.home() / ".bob" / "settings" / "mcp_settings.json"


def get_project_mcp_config_path() -> Path:
    """Get the path to project-level Bob MCP configuration file.

    Returns:
        Path to .bob/mcp.json in the current project
    """
    return Path.cwd() / ".bob" / "mcp.json"


def check_mcp_installed() -> bool:
    """Check if the verdict MCP server is registered in Bob's config.

    Checks both project-level and global configurations.

    Returns:
        True if MCP server is installed, False otherwise
    """
    try:
        # Check project-level first
        project_config = get_project_mcp_config_path()
        if project_config.exists():
            with open(project_config, encoding="utf-8") as f:
                config = json.load(f)
            if "verdict" in config.get("mcpServers", {}):
                return True

        # Check global config
        global_config = get_global_mcp_config_path()
        if global_config.exists():
            with open(global_config, encoding="utf-8") as f:
                config = json.load(f)
            if "verdict" in config.get("mcpServers", {}):
                return True

        return False
    except Exception:
        return False


def install_bob_mode() -> None:
    """Install verdict Custom Mode as a project-level Bob configuration.

    This function:
    1. Creates .bob directory in the current project
    2. Copies custom_modes.yaml to .bob/custom_modes.yaml
    3. Checks if MCP server is installed and warns if not

    Bob Custom Modes can be installed at two levels:
    - Project: .bob/custom_modes.yaml (this function)
    - Global: ~/.bob/settings/custom_modes.yaml (user must do manually)
    """
    try:
        # Install to project-level .bob directory
        project_bob_dir = Path.cwd() / ".bob"
        click.echo(f"Installing verdict Custom Mode to project: {project_bob_dir}")

        # Create .bob directory
        project_bob_dir.mkdir(exist_ok=True)

        # Get source file from package
        package_dir = Path(__file__).parent / "bob_integration"
        custom_mode_source = package_dir / "custom_mode.yaml"

        # Target path for project-level custom mode
        custom_mode_target = project_bob_dir / "custom_modes.yaml"

        # Copy Custom Mode (non-destructive - preserve if exists)
        if custom_mode_target.exists():
            click.echo(f"Custom Mode already exists: {custom_mode_target}")
            click.echo("Skipping to preserve existing configuration")
        else:
            shutil.copy2(custom_mode_source, custom_mode_target)
            click.echo(f"[OK] Custom Mode installed: {custom_mode_target}")

        # Check if MCP server is installed
        mcp_installed = check_mcp_installed()
        if not mcp_installed:
            click.echo("\nNote: Verifier mode works best with the MCP server.")
            click.echo("Run `verdict mcp install` to enable MCP integration.")

        # Print usage instructions
        click.echo("\nTo use:")
        click.echo("1. Restart Bob to load the new mode")
        click.echo('2. Switch to "Verifier" mode after a coding session')
        click.echo("\nNote: This installs as a project-level custom mode.")
        click.echo("For global installation, copy to ~/.bob/settings/custom_modes.yaml")

    except Exception as e:
        click.echo(f"✗ Installation failed: {e}", err=True)
        sys.exit(1)


def install_mcp_server() -> None:
    """Install verdict MCP server as a project-level Bob configuration.

    This function:
    1. Creates .bob directory in the current project
    2. Creates/updates .bob/mcp.json with verdict server entry
    3. Writes atomically to prevent corruption

    Bob MCP servers can be installed at two levels:
    - Project: .bob/mcp.json (this function)
    - Global: ~/.bob/settings/mcp_settings.json (user must do manually)
    """
    try:
        # Install to project-level .bob directory
        config_path = get_project_mcp_config_path()
        click.echo(f"Installing verdict MCP server to project: {config_path}")

        # Create .bob directory if it doesn't exist
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
        click.echo("[OK] Verdict MCP server installed successfully")

        # Print usage instructions
        click.echo("\nTo verify installation:")
        click.echo("1. Restart Bob")
        click.echo("2. Check that 'verdict' tools appear in Bob's tool list")
        click.echo("3. Try calling check_diff on a repository")
        click.echo("\nNote: This installs as a project-level MCP server.")
        click.echo("For global installation, copy to ~/.bob/settings/mcp_settings.json")

    except Exception as e:
        click.echo(f"✗ Installation failed: {e}", err=True)
        sys.exit(1)


def discover_checks() -> list[Check]:
    """Discover check modules via pkgutil.iter_modules.

    Walks verdict.checks.__path__, imports each module,
    extracts module-level 'check' attribute.

    Prints warning to stderr if module lacks 'check' attribute.

    Returns:
        List of Check protocol objects
    """
    checks: list[Check] = []

    for module_info in pkgutil.iter_modules(verdict.checks.__path__):
        module_name = f"verdict.checks.{module_info.name}"
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, "check"):
                checks.append(module.check)
            else:
                print(
                    f"Warning: {module_name} has no 'check' attribute",
                    file=sys.stderr,
                )
        except Exception as e:
            print(
                f"Warning: Failed to import {module_name}: {e}",
                file=sys.stderr,
            )

    return checks


def run_checks(
    repo_path: str,
    diff_range: str = "HEAD",
    static_only: bool = False,
    dynamic_only: bool = False,
) -> Scorecard:
    """Run verdict checks and return scorecard.

    Args:
        repo_path: Path to the git repository to audit
        diff_range: Git diff range to audit (default: "HEAD")
        static_only: If True, run only static checks (no test execution)
        dynamic_only: If True, run only dynamic checks

    Returns:
        Scorecard with verdict, findings, and summary

    Raises:
        ValueError: If both static_only and dynamic_only are True
    """
    # Validate flags
    if static_only and dynamic_only:
        raise ValueError("Cannot specify both static_only and dynamic_only")

    # Get changed files and added functions
    changed_files = get_changed_files(diff_range, repo_root=repo_path)
    added_functions = get_added_functions(changed_files, repo_root=repo_path)

    # Discover and filter checks
    all_checks = discover_checks()
    checks_to_run = []
    for check in all_checks:
        if static_only and check.kind != "static":
            continue
        if dynamic_only and check.kind != "dynamic":
            continue
        checks_to_run.append(check)

    # Run checks and collect findings
    findings = []
    checks_failed = 0
    for check in checks_to_run:
        try:
            check_findings = check.run(repo_path, added_functions)
            findings.extend(check_findings)
        except Exception as e:
            checks_failed += 1
            print(
                f"Warning: Check '{check.name}' failed: {type(e).__name__}: {e}",
                file=sys.stderr,
            )

    # Build summary
    summary = {
        "total_findings": len(findings),
        "static_only": static_only,
        "dynamic_only": dynamic_only,
        "diff_range": diff_range,
        "checks_run": len(checks_to_run),
        "checks_failed": checks_failed,
    }

    # Build and return scorecard
    return build_scorecard(findings, summary)


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
@click.option(
    "--dynamic-only",
    is_flag=True,
    help="Run only dynamic checks",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output JSON to stdout instead of terminal format",
)
@click.option(
    "--fail-on",
    type=click.Choice(["suspicious", "lied"]),
    help="Exit 1 if verdict matches or is worse",
)
def run(
    repo_path: str,
    diff_range: str,
    static_only: bool,
    dynamic_only: bool,
    output_json: bool,
    fail_on: str,
) -> None:
    """Run verdict checks on a git diff.

    REPO_PATH: Path to the git repository (default: current directory)
    """
    # Run checks
    try:
        scorecard = run_checks(repo_path, diff_range, static_only, dynamic_only)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    # Write JSON report to file
    report_path = Path(repo_path) / "verdict-report.json"
    report_path.write_text(format_json(scorecard))

    # Output to stdout
    if output_json:
        click.echo(format_json(scorecard))
    else:
        click.echo(format_terminal(scorecard))

    # Apply fail-on logic
    verdict = scorecard["verdict"]
    if fail_on == "lied" and verdict == "LIED":
        sys.exit(1)
    elif fail_on == "suspicious" and verdict in ("SUSPICIOUS", "LIED"):
        sys.exit(1)
    else:
        sys.exit(0)


@cli.command()
def mcp_install() -> None:
    """Install verdict MCP server into Bob's configuration.

    This command:
    - Locates Bob's MCP config file (platform-specific)
    - Adds the verdict server entry
    - Creates a portable config for other MCP clients
    """
    install_mcp_server()


@cli.command()
def bob_mode_install() -> None:
    """Install verdict Custom Mode and slash command into Bob's configuration.

    This command:
    - Installs the Verifier Custom Mode for post-coding audits
    - Installs the /verify slash command for one-shot audits
    - Both artifacts are non-destructive (preserve existing config)
    """
    install_bob_mode()


if __name__ == "__main__":
    cli()

# Made with Bob
