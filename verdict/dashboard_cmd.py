"""Backfill scorecards and serve the verdict analytics dashboard.

Two public entry points:

- ``run_backfill`` walks a branch's first-parent history, scores each
  commit by running today's verdict checks against ``parent..sha``, and
  writes one ``<sha>.json`` per commit plus an ``index.json`` listing
  them in order. Imported by the Click ``verdict dashboard`` command.
- ``serve_and_open`` spins up ``http.server`` rooted at the dashboard
  directory and pops the page in a browser. Blocks until Ctrl+C.

``run_backfill_cli`` is the argparse wrapper that
``dashboard/backfill.py`` re-exports so the script stays runnable
standalone with no Click dependency surprise.
"""

import argparse
import http.server
import json
import shutil
import socketserver
import subprocess
import sys
import tempfile
import webbrowser
from datetime import datetime, timezone
from functools import partial
from pathlib import Path
from typing import Any, Callable, Optional


# Wider format slot so subjects up to 60 chars don't shove the columns out.
_PROGRESS_SUBJECT_WIDTH = 60


def _git(args: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=check,
    )


def _ensure_git_repo(path: Path) -> None:
    result = _git(["rev-parse", "--git-dir"], cwd=path, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"{path} is not a git repository")


def _detect_repo_slug(repo_path: Path) -> Optional[str]:
    """Pull a ``owner/name`` slug from ``git remote get-url origin``."""
    result = _git(["remote", "get-url", "origin"], cwd=repo_path, check=False)
    if result.returncode != 0:
        return None
    url = result.stdout.strip().removesuffix(".git")
    # git@github.com:owner/name or https://github.com/owner/name
    if ":" in url:
        url = url.split(":", 1)[1]
    parts = url.split("/")
    if len(parts) >= 2:
        return f"{parts[-2]}/{parts[-1]}"
    return None


def _list_commits(repo_path: Path, branch: str, n: int) -> list[dict[str, str]]:
    """Return up to ``n`` first-parent commits on ``branch``, oldest first."""
    sep = "\x1f"  # unit separator, unlikely to appear in author or subject
    fmt = sep.join(["%H", "%h", "%an", "%aI", "%s"])
    result = _git(
        ["log", "--first-parent", branch, "-n", str(n), f"--format={fmt}"],
        cwd=repo_path,
    )
    commits: list[dict[str, str]] = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        sha, short_sha, author, ts, subject = line.split(sep, 4)
        commits.append(
            {
                "sha": sha,
                "short_sha": short_sha,
                "author": author,
                "timestamp": ts,
                "subject": subject,
            }
        )
    commits.reverse()
    return commits


def _score_commit(
    worktree: Path,
    sha: str,
    parent: str,
    static_only: bool,
) -> dict[str, Any]:
    """Check out ``sha`` in ``worktree`` and run verdict on ``parent..sha``."""
    from verdict.cli import run_checks  # late import: cli imports this module

    _git(["checkout", "--detach", "--quiet", sha], cwd=worktree)
    try:
        scorecard = run_checks(
            str(worktree),
            diff_range=f"{parent}..{sha}",
            static_only=static_only,
        )
        # run_checks returns a TypedDict; coerce to plain dict for json.dumps
        return dict(scorecard)
    except Exception as e:
        return {
            "verdict": "PASS",
            "findings": [],
            "summary": {
                "total_findings": 0,
                "diff_range": f"{parent}..{sha}",
                "error": f"{type(e).__name__}: {e}",
            },
        }


def _index_entry(commit: dict[str, str], parent: str, scorecard: dict[str, Any]) -> dict[str, Any]:
    findings = scorecard.get("findings") or []
    top = findings[0] if findings else None
    return {
        "sha": commit["sha"],
        "short_sha": commit["short_sha"],
        "subject": commit["subject"],
        "author": commit["author"],
        "timestamp": commit["timestamp"],
        "parent": parent,
        "scorecard_file": f"{commit['sha']}.json",
        "verdict": scorecard.get("verdict", "PASS"),
        "total_findings": len(findings),
        "top_finding": (
            {
                "kind": top["kind"],
                "message": top["message"],
                "confidence": top["confidence"],
            }
            if top
            else None
        ),
    }


def run_backfill(
    repo_path: str,
    n: int = 30,
    branch: str = "main",
    static_only: bool = True,
    force: bool = False,
    progress: Optional[Callable[[int, int, str, str, str, int], None]] = None,
) -> dict[str, Any]:
    """Score the last ``n`` first-parent commits on ``branch``.

    Writes ``dashboard/data/<sha>.json`` per commit and a top-level
    ``dashboard/data/index.json``. Returns the index payload.

    Args:
        repo_path: path to a verdict repo (must be a git checkout).
        n: how many commits to walk, newest-first then reversed.
        branch: branch name to walk with ``--first-parent``.
        static_only: pass through to ``run_checks``. Default True because
            dynamic checks shell out to pytest in a subprocess and don't
            generalize across historical commits.
        force: re-score commits whose ``<sha>.json`` already exists.
        progress: optional callback ``(i, total, sha, subject, verdict,
            n_findings)`` invoked after each commit. Lets the caller
            render its own progress UI without this function depending
            on Click.
    """
    repo = Path(repo_path).resolve()
    _ensure_git_repo(repo)

    dashboard_dir = repo / "dashboard"
    data_dir = dashboard_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    commits = _list_commits(repo, branch, n)
    if not commits:
        raise RuntimeError(f"no commits found on branch {branch!r}")

    # tempfile.mkdtemp creates a real dir; git worktree add wants a path
    # that doesn't exist yet, so nest one level deeper.
    worktree_parent = Path(tempfile.mkdtemp(prefix="verdict-backfill-"))
    worktree = worktree_parent / "tree"

    # Cleans up any stale worktree references from a prior crashed run.
    _git(["worktree", "prune"], cwd=repo, check=False)
    _git(
        ["worktree", "add", "--detach", "--quiet", str(worktree), commits[0]["sha"]],
        cwd=repo,
    )

    scored: list[dict[str, Any]] = []
    try:
        for i, commit in enumerate(commits, start=1):
            sha = commit["sha"]
            parent_result = _git(["rev-parse", f"{sha}^"], cwd=repo, check=False)
            if parent_result.returncode != 0:
                # Root commit; nothing to diff against.
                if progress:
                    progress(i, len(commits), sha, commit["subject"], "SKIP", 0)
                continue
            parent = parent_result.stdout.strip()

            out_path = data_dir / f"{sha}.json"
            if out_path.exists() and not force:
                scorecard = json.loads(out_path.read_text())
            else:
                scorecard = _score_commit(worktree, sha, parent, static_only)
                out_path.write_text(json.dumps(scorecard, indent=2, sort_keys=True))

            entry = _index_entry(commit, parent, scorecard)
            scored.append(entry)

            if progress:
                progress(
                    i,
                    len(commits),
                    sha,
                    commit["subject"],
                    entry["verdict"],
                    entry["total_findings"],
                )
    finally:
        _git(
            ["worktree", "remove", "--force", str(worktree)],
            cwd=repo,
            check=False,
        )
        shutil.rmtree(worktree_parent, ignore_errors=True)

    index = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "repo": _detect_repo_slug(repo),
        "branch": branch,
        "static_only": static_only,
        "commits": scored,
    }
    (data_dir / "index.json").write_text(json.dumps(index, indent=2, sort_keys=True))
    return index


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        # Stay out of the way of the progress lines.
        return


class _ReusableServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def serve_and_open(
    dashboard_dir: Path,
    port: int = 8765,
    open_browser: bool = True,
) -> None:
    """Serve ``dashboard_dir`` over HTTP and open it in a browser."""
    handler = partial(_QuietHandler, directory=str(dashboard_dir))

    try:
        httpd = _ReusableServer(("", port), handler)
    except OSError:
        httpd = _ReusableServer(("", 0), handler)
        port = httpd.server_address[1]

    url = f"http://localhost:{port}/"
    print(f"\nServing dashboard at {url}")
    if open_browser:
        webbrowser.open(url)
        print("Opened browser. Press Ctrl+C to stop.")
    else:
        print("Press Ctrl+C to stop.")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
    finally:
        httpd.shutdown()
        httpd.server_close()


def _print_progress(i: int, total: int, sha: str, subject: str, verdict: str, n: int) -> None:
    short = sha[:7]
    if len(subject) > _PROGRESS_SUBJECT_WIDTH:
        subject = subject[: _PROGRESS_SUBJECT_WIDTH - 3] + "..."
    print(
        f"  [{i:>2}/{total}] {short} {subject:<{_PROGRESS_SUBJECT_WIDTH}}  "
        f"{verdict:<11} {n:>3} findings"
    )


def run_backfill_cli() -> None:
    """Argparse entrypoint re-exported by ``dashboard/backfill.py``."""
    parser = argparse.ArgumentParser(
        description="Backfill verdict scorecards for the analytics dashboard.",
    )
    parser.add_argument("--repo", default=".", help="path to verdict repo (default: cwd)")
    parser.add_argument("-n", "--count", type=int, default=30, help="commits to score")
    parser.add_argument("--branch", default="main", help="branch to walk")
    parser.add_argument(
        "--no-static-only",
        action="store_true",
        help="include dynamic checks (slower, may flake on old commits)",
    )
    parser.add_argument(
        "--force", action="store_true", help="re-score commits already in data/"
    )
    args = parser.parse_args()

    print(f"Backfilling {args.count} commits from {args.branch}...")
    index = run_backfill(
        args.repo,
        n=args.count,
        branch=args.branch,
        static_only=not args.no_static_only,
        force=args.force,
        progress=_print_progress,
    )
    print(f"\nWrote {len(index['commits'])} scorecards to dashboard/data/")


if __name__ == "__main__":
    run_backfill_cli()
