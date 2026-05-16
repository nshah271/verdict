# verdict

A lie detector for AI coding agents. Audits an AI-generated diff statically and traces what actually runs when the tests execute, then returns a single scorecard: `PASS`, `SUSPICIOUS`, or `LIED`.

Built for the IBM Bob hackathon (May 2026). Repo bootstrap in progress; the real README lands as part of P3.5.

## Install

```bash
pip install myverdict
```

The PyPI package is named `myverdict` (the shorter `verdict-ai` slot was taken by an unrelated project before we shipped). The Python import is still `import verdict` and the CLI is still `verdict`.

## Quick start with IBM Bob

```bash
# Install verdict's MCP server and Custom Mode globally so Bob sees them
# in every project on this machine:
verdict mcp-install --global
verdict bob-mode-install --global

# Restart Bob, then in any project switch to "Verifier" mode after a
# coding session or type /verify for a one-shot audit.
```

Drop `--global` to install per-project under `.bob/` instead.

## Status

| Priority | Owner | Status |
|----------|-------|--------|
| P0.1 foundation (diff + AST) | Neel | not started |
| P0.2 dead function detection | Jacob | not started |
| P0.3 vacuous test detection | Alexie | not started |
| P0.4 CLI + scorecard | Neel | not started |
| P1.1 execution tracer | Neel | not started |
| P1.2 MCP server | Ben | not started |

See `verdict-spec.md` and `TEAM.md` (local to the team, not in this repo) for the full plan.
