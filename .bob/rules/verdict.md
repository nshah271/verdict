# Verdict Audit Rule

You have access to the `verdict` MCP server (`verdict.check_diff`) and the `verdict` CLI (`verdict run`). Use them to audit your own code changes.

## When you MUST run verdict

Call `verdict.check_diff` (preferred) or run `verdict run` in the workspace before calling `attempt_completion` in any of these situations:

1. **After completing a feature or task** that involved writing or editing code — run verdict before reporting the task as done.
2. **After a test suite is written or modified** — run verdict to catch vacuous tests (e.g. tests that assert nothing, tests that never exercise the function under test, mocked-away assertions).
3. **After a multi-file change** — any session where you used `write_to_file`, `apply_diff`, or `insert_content` more than once on source files.
4. **Before declaring a bug fixed** — verdict must show no new SUSPICIOUS/LIED findings on the diff.

You do not need to run verdict for:
- Documentation-only changes (`.md`, `.mdx`, `.txt`)
- Configuration-only changes that touch no executable code
- Read-only exploration or questions

## How to run it

Prefer MCP:
- Call `verdict.check_diff` with `repo_path` set to the current workspace directory.

Fallback to terminal:
- Execute `verdict run` from the workspace root.

## How to handle the result

Parse the Scorecard JSON (`verdict`, `findings`, `summary`).

- **`PASS`** — proceed with `attempt_completion`. Mention in your summary: "Verdict: PASS".
- **`SUSPICIOUS`** or **`LIED`** — do NOT call `attempt_completion` yet. Surface every finding verbatim with `[kind] file:line - message (confidence: X.XX)`. Then either:
  - Fix the underlying issue (dead function, vacuous test, untested code) and re-run verdict, or
  - If the finding is a known false positive, explain why explicitly to the user and ask whether to proceed.

## What NOT to do

- Do not skip verdict because "the change is small" — vacuous tests and dead functions slip in most often on small changes.
- Do not paraphrase, rank, or filter findings. Report them verbatim.
- Do not claim a task is complete while verdict is SUSPICIOUS or LIED without explicit user acknowledgement.
