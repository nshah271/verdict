"""CLI entry point for verdict.

This module provides the command-line interface for verdict, including:
- verdict run: Run checks on a git diff
- verdict mcp install: Install the MCP server into Bob's configuration
- verdict bob-mode install: Install Bob Custom Mode and slash command
"""

import concurrent.futures
import importlib
import json
import pkgutil
import shutil
import subprocess
import sys
from pathlib import Path

import click
import questionary

import verdict.checks
from verdict.ast_utils import get_added_functions
from verdict.diff import get_changed_files
from verdict.report import build_scorecard, format_json, format_terminal
from verdict.types import Check, Finding, Scorecard


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


def install_bob_mode(is_global: bool = False) -> None:
    """Install verdict Custom Mode + slash commands into Bob's configuration.

    Args:
        is_global: If True, install to ~/.bob/settings/custom_modes.yaml and
            ~/.bob/commands/ so Bob sees the verdict mode and /verify command
            in every project. If False (default), install to .bob/ in the
            current project only.
    """
    try:
        if is_global:
            custom_mode_target = Path.home() / ".bob" / "settings" / "custom_modes.yaml"
            commands_dir = Path.home() / ".bob" / "commands"
            click.echo(f"Installing verdict Custom Mode globally: {custom_mode_target}")
        else:
            project_bob_dir = Path.cwd() / ".bob"
            custom_mode_target = project_bob_dir / "custom_modes.yaml"
            commands_dir = project_bob_dir / "commands"
            click.echo(f"Installing verdict Custom Mode to project: {project_bob_dir}")

        # Create parent dirs (~/.bob/settings or ./.bob)
        custom_mode_target.parent.mkdir(parents=True, exist_ok=True)

        # Get source directory from package
        package_dir = Path(__file__).parent / "bob_integration"
        custom_mode_source = package_dir / "custom_mode.yaml"

        # Copy Custom Mode (non-destructive - preserve if exists)
        if custom_mode_target.exists():
            click.echo(f"Custom Mode already exists: {custom_mode_target}")
            click.echo("Skipping to preserve existing configuration")
        else:
            shutil.copy2(custom_mode_source, custom_mode_target)
            click.echo(f"[OK] Custom Mode installed: {custom_mode_target}")

        # Install slash commands
        commands_dir.mkdir(parents=True, exist_ok=True)

        slash_commands_source = package_dir / "slash_commands"
        if slash_commands_source.exists():
            # Copy all .md files from slash_commands directory
            installed_commands = []
            for md_file in slash_commands_source.glob("*.md"):
                target_file = commands_dir / md_file.name
                if target_file.exists():
                    click.echo(f"Slash command already exists: {target_file.name}")
                else:
                    shutil.copy2(md_file, target_file)
                    installed_commands.append(md_file.stem)

            if installed_commands:
                click.echo(f"[OK] Slash commands installed: {', '.join(f'/{cmd}' for cmd in installed_commands)}")
            else:
                click.echo("All slash commands already installed")
        else:
            click.echo("Warning: No slash commands found in package")

        # Check if MCP server is installed
        mcp_installed = check_mcp_installed()
        if not mcp_installed:
            click.echo("\nNote: Verifier mode works best with the MCP server.")
            flag = " --global" if is_global else ""
            click.echo(f"Run `verdict mcp install{flag}` to enable MCP integration.")

        # Print usage instructions
        click.echo("\nTo use:")
        click.echo("1. Restart Bob to load the new mode and slash commands")
        click.echo('2. Switch to "Verifier" mode after a coding session')
        click.echo("3. Or type /verify in any mode for a one-shot audit")
        if is_global:
            click.echo("\nGlobal install: verdict mode + /verify available in every project.")
        else:
            click.echo("\nProject install: re-run with --global to make it available everywhere.")

    except Exception as e:
        click.echo(f"✗ Installation failed: {e}", err=True)
        sys.exit(1)


def install_mcp_server(is_global: bool = False) -> None:
    """Install the verdict MCP server into Bob's configuration.

    Args:
        is_global: If True, write to ~/.bob/settings/mcp_settings.json so the
            server is available in every project. If False (default), write
            to .bob/mcp.json in the current working directory.
    """
    try:
        if is_global:
            config_path = get_global_mcp_config_path()
            click.echo(f"Installing verdict MCP server globally: {config_path}")
        else:
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
        if is_global:
            click.echo("\nGlobal install: available in every project on this machine.")
        else:
            click.echo("\nProject install: re-run with --global to make it available everywhere.")

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
    per_check_timeout: float | None = None,
) -> Scorecard:
    """Run verdict checks and return scorecard.

    Args:
        repo_path: Path to the git repository to audit
        diff_range: Git diff range to audit (default: "HEAD")
        static_only: If True, run only static checks (no test execution)
        dynamic_only: If True, run only dynamic checks
        per_check_timeout: Wall-clock cap per check in seconds. None means
            no timeout (CLI default). MCP callers should pass a finite value
            so one slow check can't block the whole call.

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
    findings: list[Finding] = []
    checks_failed = 0
    checks_timed_out = 0
    for check in checks_to_run:
        try:
            check_findings = _run_one_check(
                check, repo_path, added_functions, per_check_timeout
            )
            findings.extend(check_findings)
        except concurrent.futures.TimeoutError:
            checks_timed_out += 1
            findings.append(
                {
                    "kind": "check_timed_out",
                    "file": "",
                    "line": 0,
                    "message": (
                        f"check '{check.name}' exceeded {per_check_timeout}s timeout"
                    ),
                    "confidence": 0.5,
                }
            )
            print(
                f"Warning: Check '{check.name}' exceeded {per_check_timeout}s timeout",
                file=sys.stderr,
            )
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
        "checks_timed_out": checks_timed_out,
    }

    # Build and return scorecard
    return build_scorecard(findings, summary)


def _run_one_check(
    check: Check,
    repo_path: str,
    added_functions: list,
    per_check_timeout: float | None,
) -> list[Finding]:
    """Run a single check, optionally bounded by a wall-clock timeout.

    A timed-out thread is not killed (Python can't), but we abandon waiting
    on it and continue. The stuck thread leaks until it eventually returns
    or the process exits, which is acceptable for the MCP server's typical
    lifetime.
    """
    if per_check_timeout is None:
        return check.run(repo_path, added_functions)

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    try:
        future = executor.submit(check.run, repo_path, added_functions)
        return future.result(timeout=per_check_timeout)
    finally:
        executor.shutdown(wait=False)


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
@click.option(
    "--global",
    "is_global",
    is_flag=True,
    help="Install to ~/.bob/settings/mcp_settings.json so every project sees it.",
)
def mcp_install(is_global: bool) -> None:
    """Install the verdict MCP server into Bob's configuration.

    Without --global, writes to .bob/mcp.json in the current project.
    With --global, writes to ~/.bob/settings/mcp_settings.json so the
    server is available to Bob in any project on this machine.
    """
    install_mcp_server(is_global=is_global)


@cli.command()
@click.option(
    "--global",
    "is_global",
    is_flag=True,
    help="Install to ~/.bob/settings + ~/.bob/commands so every project sees it.",
)
def bob_mode_install(is_global: bool) -> None:
    """Install verdict Custom Mode and slash commands into Bob's configuration.

    Without --global, writes to .bob/ in the current project. With --global,
    writes to ~/.bob/settings/custom_modes.yaml + ~/.bob/commands/ so Bob
    sees the verdict mode and /verify command in any project on this machine.
    Both artifacts are non-destructive (preserve existing config).
    """
    install_bob_mode(is_global=is_global)


_CUSTOM = "Custom…"


def _ask_yes_no(message: str, default: bool) -> bool:
    answer = questionary.select(
        message,
        choices=["Yes", "No"],
        default="Yes" if default else "No",
    ).ask()
    if answer is None:
        sys.exit(130)
    return answer == "Yes"


def _ask_count(default: int) -> int:
    presets = [10, 30, 50, 100]
    choices = [str(n) for n in presets] + [_CUSTOM]
    default_choice = str(default) if default in presets else _CUSTOM
    answer = questionary.select(
        "How many commits to score?", choices=choices, default=default_choice
    ).ask()
    if answer is None:
        sys.exit(130)
    if answer == _CUSTOM:
        custom = questionary.text(
            "Enter a number:",
            default=str(default),
            validate=lambda v: v.isdigit() and int(v) > 0 or "Must be a positive integer",
        ).ask()
        if custom is None:
            sys.exit(130)
        return int(custom)
    return int(answer)


def _list_local_branches(repo_path: Path) -> list[str]:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(repo_path), "branch", "--format=%(refname:short)"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]


def _current_branch(repo_path: Path) -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(repo_path), "branch", "--show-current"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    name = out.strip()
    return name or None


def _ask_branch(repo_path: Path, default: str) -> str:
    branches = _list_local_branches(repo_path)
    current = _current_branch(repo_path)

    # Order: current first, then default if different, then the rest, then Custom.
    ordered: list[str] = []
    for b in (current, default):
        if b and b in branches and b not in ordered:
            ordered.append(b)
    for b in branches:
        if b not in ordered:
            ordered.append(b)
    if not ordered:
        ordered = [default]
    choices = ordered + [_CUSTOM]

    default_choice = current if current in ordered else (default if default in ordered else ordered[0])
    answer = questionary.select(
        "Branch to walk?", choices=choices, default=default_choice
    ).ask()
    if answer is None:
        sys.exit(130)
    if answer == _CUSTOM:
        custom = questionary.text("Enter branch name:", default=default).ask()
        if custom is None:
            sys.exit(130)
        return custom.strip() or default
    return answer


@cli.command()
@click.option("--no-backfill", is_flag=True, help="Skip backfill, serve existing data only.")
@click.option("-n", "--count", type=int, default=None, help="How many commits to score.")
@click.option("--branch", default=None, help="Branch to walk with --first-parent.")
@click.option(
    "--static-only/--no-static-only",
    default=None,
    help="Run only static checks. Default: yes (dynamic checks flake on old commits).",
)
@click.option("--force", is_flag=True, help="Re-score commits already cached in data/.")
@click.option("--no-open", is_flag=True, help="Don't auto-open the browser.")
@click.option("--port", type=int, default=8765, help="Port to serve dashboard on.")
def dashboard(
    no_backfill: bool,
    count: int | None,
    branch: str | None,
    static_only: bool | None,
    force: bool,
    no_open: bool,
    port: int,
) -> None:
    """Run backfill and open the verdict analytics dashboard.

    Walks the verdict repo's git history, scores each commit, writes
    dashboard/data/<sha>.json, then serves dashboard/ on a local HTTP
    port and pops it in a browser. Press Ctrl+C to stop.
    """
    from verdict.dashboard_cmd import run_backfill, serve_and_open

    repo_path = Path.cwd()
    dashboard_dir = repo_path / "dashboard"
    data_dir = dashboard_dir / "data"

    if not dashboard_dir.exists():
        click.echo(
            f"Error: {dashboard_dir} does not exist. Run this from the verdict repo root.",
            err=True,
        )
        sys.exit(1)

    backfill_args_passed = (
        count is not None or branch is not None or static_only is not None or force
    )

    interactive = sys.stdin.isatty() and sys.stdout.isatty()

    if no_backfill:
        do_backfill = False
    elif backfill_args_passed:
        do_backfill = True
    elif interactive:
        do_backfill = _ask_yes_no("Backfill commits?", default=True)
    else:
        do_backfill = True

    if do_backfill:
        if count is None:
            count = _ask_count(default=30) if interactive else 30
        if branch is None:
            branch = _ask_branch(repo_path, default="main") if interactive else "main"
        if static_only is None:
            if interactive:
                include_dynamic = _ask_yes_no(
                    "Include dynamic checks (slower, may flake on old commits)?",
                    default=False,
                )
            else:
                include_dynamic = False
            static_only = not include_dynamic
        if not force and data_dir.exists() and any(data_dir.glob("*.json")):
            if interactive:
                force = _ask_yes_no("Re-score commits already in data/?", default=False)
            else:
                force = False

        click.echo(f"\nBackfilling {count} commits from {branch}...")

        def _progress(i: int, total: int, sha: str, subject: str, verdict: str, n: int) -> None:
            short = sha[:7]
            if len(subject) > 60:
                subject = subject[:57] + "..."
            click.echo(
                f"  [{i:>2}/{total}] {short} {subject:<60}  {verdict:<11} {n:>3} findings"
            )

        try:
            run_backfill(
                str(repo_path),
                n=count,
                branch=branch,
                static_only=static_only,
                force=force,
                progress=_progress,
            )
        except RuntimeError as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
    else:
        if not (data_dir.exists() and any(data_dir.glob("*.json"))):
            click.echo(
                "Error: no data in dashboard/data/. Run without --no-backfill first.",
                err=True,
            )
            sys.exit(1)

    serve_and_open(dashboard_dir, port=port, open_browser=not no_open)


if __name__ == "__main__":
    cli()

# Made with Bob
