# verdict

A lie detector for AI coding agents. Audits an AI-generated diff statically and traces what actually runs when the tests execute, then returns a single scorecard: `PASS`, `SUSPICIOUS`, or `LIED`.

Built for the IBM Bob hackathon (May 2026). Repo bootstrap in progress; the real README lands as part of P3.5.

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
