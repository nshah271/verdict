# Verdict

**A lie detector for AI coding agents.**

Verdict audits an AI-generated diff — statically *and* by tracing what actually runs when the tests execute — and returns a single scorecard:

> `PASS` &nbsp;·&nbsp; `SUSPICIOUS` &nbsp;·&nbsp; `LIED`

Built for the **IBM Bob hackathon (May 2026)**.

---
## Website
https://myverdict.netlify.app/

---

## Why Verdict exists

AI coding agents are getting good at *looking* right. They produce diffs that compile, pass type-checks, even pass the tests they wrote themselves. But when you actually dig in, you find:

- A "fix" that adds a function nothing ever calls.
- A new test that mocks out everything it was supposed to verify, and asserts on the mocks.
- A call to `requests.get_json()` — a method that does not exist.
- A claim that a file was created, but the file is not on disk.
- A `try/except: pass` that buries the very bug the agent was asked to fix.
- A new code path that pytest covers 0 % of, even though the test suite is "green".

These are not syntax errors. Linters miss them. Type checkers miss them. CI passes. The agent says "done." A human reviewer skims the diff and assumes the green check mark means something.

Verdict catches these by *not trusting the agent's word*. It re-reads the diff, walks the AST, and runs the tests under a tracer to see what code actually executed. If the story the agent told doesn't match what the code does, Verdict says so.

---

## The seven things Verdict looks for

Verdict runs seven independent checks on every diff. Each one targets a distinct class of agent failure. Five are **static** (AST/grep-based, no execution needed) and two are **dynamic** (run the test suite under instrumentation).

| # | Check | Kind | What it catches |
|---|---|---|---|
| 1 | **`dead_function`** | static | A function was added in the diff but is **never referenced** anywhere in the repo (not called, not imported, not exported via `__all__` or `__init__.py`). Classic agent symptom: writes helper functions to "look productive," never wires them up. |
| 2 | **`vacuous_tests`** | static | A test function that doesn't actually test anything. Four heuristics fire: empty body (`pass`/`...`/docstring only), no `assert` statements, mock-only assertions (only checks calls on `Mock()` objects the test itself created), or the test never reaches any newly-added code. Catches "I wrote a test for it" lies. |
| 3 | **`hallucinated_api`** | static | A call to a method or attribute that **does not exist** on the inferred type. `requests.get_json()`, `my_list.add(x)`, `dict.get_or_default()`. Powered by [Jedi](https://github.com/davidhalter/jedi) static type inference, so it doesn't need to execute the code to know the call is bogus. |
| 4 | **`phantom_files`** | static | The agent's transcript or diff claims a file was created, but the file isn't on disk. Scans for patterns like `"created file: path/to/x.py"` and cross-checks against the filesystem. Catches hallucinated file creation. |
| 5 | **`suppressed_exception`** | static | A `try/except` block in newly-added code that **silently swallows** exceptions — bare `except:`, `except Exception: pass`, or `except: logger.error(...)` with no re-raise. Catches the "make the error go away" anti-fix. |
| 6 | **`trace`** | dynamic | Runs the test suite under `sys.settrace` and records every function that actually executes. Any newly-added function whose body never runs gets flagged. Catches agents who add code *and* tests, but the tests never reach the new code. |
| 7 | **`coverage_delta`** | dynamic | Line-level coverage on just the lines the diff added. If a newly-added line is below 50 % covered, it's flagged. Sharper than whole-file coverage because it ignores pre-existing untested code. |

Each finding carries:

```json
{
  "kind": "vacuous_test",
  "file": "tests/test_payment.py",
  "line": 42,
  "message": "test_refund only asserts on mocks created in the test",
  "confidence": 0.85
}
```

The scorecard rule (current, intentionally simple): any finding with `confidence > 0.8` → **`LIED`**; any findings at all → **`SUSPICIOUS`**; otherwise → **`PASS`**. (See `verdict/report.py` for the planned post-hackathon Bayesian-aggregation replacement.)

---

## Architecture at a glance

```
┌────────────────────────────────────────────────────────────────┐
│  You / Bob agent                                                │
└──────────┬────────────────────────┬─────────────────────────────┘
           │                        │
           │ MCP tool call          │ CLI invocation
           │                        │
           ▼                        ▼
   ┌──────────────────┐    ┌──────────────────┐
   │  verdict-mcp     │    │   verdict run    │
   │  (MCP server)    │    │   (Click CLI)    │
   └────────┬─────────┘    └────────┬─────────┘
            │                       │
            └───────────┬───────────┘
                        ▼
         ┌──────────────────────────────┐
         │   Check discovery & runner   │
         │   (pkgutil → 7 checks)       │
         └──────────────┬───────────────┘
                        │
        ┌───────────────┼────────────────┐
        ▼               ▼                ▼
   ┌────────┐     ┌────────┐       ┌──────────┐
   │ static │     │ static │  ...  │ dynamic  │
   │ checks │     │ checks │       │ checks   │
   └────┬───┘     └────┬───┘       └────┬─────┘
        └──────────────┼─────────────────┘
                       ▼
            ┌────────────────────┐
            │  Scorecard JSON    │  ← verdict-report.json
            │  PASS/SUSPICIOUS/  │
            │  LIED + findings   │
            └─────────┬──────────┘
                      │
            ┌─────────┴──────────┐
            ▼                    ▼
     ┌─────────────┐      ┌──────────────┐
     │ Verdict tab │      │  Dashboard   │
     │ (VS Code/   │      │  (git-history│
     │  Bob ext.)  │      │   analytics) │
     └─────────────┘      └──────────────┘
```

Five distinct surfaces, one scorecard format:

1. **`verdict` CLI** — `verdict run` on any git repo, prints a scorecard, writes `verdict-report.json`.
2. **`verdict-mcp` MCP server** — exposes `check_diff` as an MCP tool that Bob (or any MCP client) can call mid-conversation.
3. **Bob Custom Mode + `/verify` slash command** — turns Bob into a read-only auditor that runs Verdict and reports findings without making edits.
4. **Verdict VS Code tab** — a bottom-panel webview inside Bob (or upstream VS Code) that renders the latest scorecard, persists dismiss/resolve status, and offers a "Fix with Bob" handoff.
5. **Verdict dashboard** — backfills the entire git history of a repo, scores each commit, and serves a local web UI for trend analytics.

---

## Use cases

**Reviewing an AI's pull request.** Before you read the diff, run `verdict run` on the branch. If the verdict is `LIED`, start by reading those findings — the agent is probably hiding something. If `PASS`, the diff is at least internally consistent.

**Inside a Bob coding session.** Install the MCP server and the Verifier mode. After Bob finishes a coding task, switch into Verifier mode (or type `/verify`). Bob will audit its own diff and report findings verbatim with file:line citations. Tight feedback loop, no human review needed for trivial diffs.

**As a CI gate.** `verdict run --fail-on lied` exits 1 if any high-confidence lies are detected. Drop it in GitHub Actions after pytest. Catches the "tests are green but the new code never runs" failure mode that test-runners can't see.

**As a quality dashboard.** `verdict dashboard` backfills history and surfaces trends. Useful for spotting when AI-generated commits started slipping past review, or which authors / which areas of the codebase get the most `SUSPICIOUS` verdicts.

**As an editor surface.** Install the Verdict VS Code tab. Hit "Run Audit" in the toolbar, click any finding to jump to the exact line, dismiss false positives, or hand the finding off to Bob with one click to fix.

---

## Installation

### Prerequisites

- **Python 3.10+** (for the CLI and MCP server)
- **Git** (Verdict diffs against `HEAD` by default)
- **Bob IDE** *or* VS Code 1.74+ (for the Verdict tab; CLI works without an editor)
- **Node.js 20+** (only if you want to rebuild the VS Code extension from source)

### TL;DR (the 5-minute demo flow)

On a fresh machine, end-to-end:

```bash
# 1. install the CLI
pip install myverdict
verdict --help

# 2. hook into Bob (one-time, machine-wide)
verdict mcp-install --global
verdict bob-mode-install --global
# restart Bob

# 3. install the editor tab
#    download verdict-vscode-0.2.0.vsix from this repo's
#    verdict-vscode/ folder, drop it in any project folder,
#    right-click → Install Extension VSIX, reload the window.

# 4. try it on a real repo
cd <some-git-repo>
verdict run --diff-range HEAD~1

# 5. add it to a repo's CI (one .github/workflows/verdict.yml file, see below)

# 6. browse history
verdict dashboard
```

Each step is explained in detail below.

### 1. Install the Verdict CLI

From anywhere:

```bash
pip install myverdict
```

Or, if you've cloned this repo and want an editable dev install:

```bash
pip install -e .   # from the repo root
```

Either way, this installs two console scripts:

- `verdict` — the audit CLI
- `verdict-mcp` — the MCP server entry point

Verify:

```bash
verdict --help
verdict run --help
```

<!-- SCREENSHOT 01: terminal after `pip install myverdict` finishes cleanly.
     SCREENSHOT 02: `verdict --help` output showing run / mcp-install /
                   bob-mode-install / dashboard. Drop the PNGs here as
                   `![alt](docs/screenshots/01-*.png)`. -->

### 2. Run an audit

From inside any git repository:

```bash
verdict run                       # audit HEAD vs working tree
verdict run --diff-range HEAD~1   # audit the last commit
verdict run --static-only         # skip dynamic checks (no pytest run)
verdict run --json                # emit JSON to stdout
verdict run --fail-on lied        # CI mode: exit 1 on LIED verdict
```

Output:

```
Verdict: SUSPICIOUS  (3 findings, 12 new functions analyzed)

[dead_function]      verdict/foo.py:42        helper_unused never referenced              (0.90)
[vacuous_test]       tests/test_foo.py:18     test_helper has no assertions               (0.85)
[suppressed_exc]     verdict/foo.py:67        bare except swallows exception              (0.75)
```

Verdict also writes the full report to `verdict-report.json` in the repo root. That's what the VS Code tab reads.

<!-- SCREENSHOT 03: terminal showing a real `verdict run` against a repo
                   with at least one LIED finding. The colored verdict
                   header + per-kind summary are the star of this shot. -->

### 3. Install the Bob MCP integration *(optional)*

If you're using **Bob**, hook Verdict into Bob's tool list so agents can call `verdict.check_diff` mid-conversation. Two scopes:

```bash
# Recommended: install once, available in every project on this machine
verdict mcp-install --global
verdict bob-mode-install --global

# Or, per-project install (writes into ./.bob/)
verdict mcp-install
verdict bob-mode-install
```

`--global` writes to `~/.bob/settings/mcp_settings.json`, `~/.bob/settings/custom_modes.yaml`, and `~/.bob/commands/verify.md`. Drop `--global` to install only into the current project's `.bob/` directory.

Restart Bob. You should now see:

- A **Verifier** mode in Bob's mode picker (read-only auditor).
- A **`/verify`** slash command available in any mode (one-shot audit, doesn't switch modes).
- A `verdict` tool group in Bob's tool list.

Both installers are non-destructive — they preserve existing config and merge.

<!-- SCREENSHOT 04: Bob's chat mode dropdown open, with "Verifier" visible.
     SCREENSHOT 05: Bob's slash-command picker open, with "/verify" visible.
     SCREENSHOT 06: Bob mid-conversation calling verdict.check_diff (tool
                   invocation card). Captures the MCP integration. -->

### 4. Install the Verdict VS Code tab

A prebuilt `.vsix` ships with this repo. Three ways to install it — pick whichever is easiest:

**A. Download → drop in your project → right-click *(easiest, works on a fresh machine without cloning the repo).***

1. Download [`verdict-vscode-0.2.0.vsix`](verdict-vscode/verdict-vscode-0.2.0.vsix) from this repo's `verdict-vscode/` folder. (Right-click the link → Save Link As, or grab it from the GitHub web UI.)
2. Move the `.vsix` into any project folder you have open in Bob / VS Code.
3. In the editor's file explorer (left sidebar), right-click the `.vsix` file → **Install Extension VSIX**.
4. Reload the window when prompted.

**B. Command Palette.** `Ctrl+Shift+P` (or `Cmd+Shift+P`) → **Extensions: Install from VSIX…** → navigate to the `.vsix` → Install. Reload.

**C. Terminal — one-liner.** From wherever the `.vsix` lives (works for both Bob and VS Code — Bob ships the same `code` CLI):

```bash
code --install-extension verdict-vscode-0.2.0.vsix --force
```

The `--force` flag overwrites any previous install of the same version. If you get `command not found: code`, the CLI isn't on PATH — open the editor, hit `Ctrl+Shift+P`, run **Shell Command: Install 'code' command in PATH**, then try again. Or just use method A or B — they don't need the shell command.

After installing by any method, **reload the editor window**, then reveal the bottom panel (`Ctrl+J`) — there will be a new **Verdict** tab. Click **Run Audit** in the toolbar and the panel populates.

<!-- SCREENSHOT 07: the right-click context menu in the file explorer
                   showing "Install Extension VSIX" highlighted on the
                   .vsix file. Optional but very clear for the demo.
     SCREENSHOT 08: the Verdict tab populated with findings in the
                   bottom panel. The two-pane (list + detail) view. -->

If you'd rather build from source:

```bash
cd verdict-vscode
npm install
npm run compile
npx @vscode/vsce package --no-dependencies --allow-missing-repository
```

### 5. Add Verdict to a repo's CI *(optional)*

Drop this file into the repo you want audited:

```yaml
# .github/workflows/verdict.yml
name: Verdict
on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: nshah271/verdict@main
        # Optional inputs (all have defaults):
        #   fail-on: never | suspicious | lied   (default: never)
        #   comment-on-pr: true | false          (default: true)
        #   static-only: true | false            (default: false)
        #   diff-range: <any git range>          (default: origin/main...HEAD)
```

What happens after that:

- Every PR (open + every push) gets a bot comment listing findings, each one a clickable deep link to the exact line.
- Anyone watching the PR gets the comment in their inbox via GitHub's normal notification path — that's the "Verdict emails me my findings" experience, no SMTP setup needed.
- The check stays **green** by default (informational). Flip `fail-on: lied` if you want it to actually block merges on `LIED` verdicts.

<!-- SCREENSHOT 09: a real PR with the verdict bot comment expanded,
                   showing the findings list + clickable file:line links.
                   The "verdict emails me findings" punchline. -->

### 6. Open the analytics dashboard *(optional)*

From the repo root:

```bash
verdict dashboard
```

This walks the git history, scores each commit, writes one JSON per commit into `dashboard/data/`, then serves the dashboard at `http://localhost:8765` and opens your browser. First run prompts for commit count and branch; subsequent runs reuse cached scores.

<!-- SCREENSHOT 10: the dashboard in a browser. Trust panel + donut at
                   top, kind bar in middle, commit timeline at bottom.
                   This is the visual-impact shot. -->

---

## Verdict tab — what's in it

The Verdict tab is a two-pane webview inside the editor's bottom panel:

- **Toolbar:** Run Audit · Run Static Audit · Refresh · diff-range selector · group-by (type / file / severity) · sort-by · fuzzy search.
- **Left pane:** grouped, filterable list of findings.
- **Right pane:** detail view for the selected finding — full message, file:line link, dismiss/resolve buttons, **Fix with Bob** handoff (sends the finding into Bob as a fix prompt).
- **Status bar:** left-side indicator with the current verdict color.

Status (dismissed / resolved / open) persists across runs in `.bob/verdict-state.json`, keyed by a stable SHA-1 of `(kind, file, line, message)` so re-runs of Verdict don't lose your triage state — unless the underlying finding actually changed.

Settings (workspace or user `settings.json`):

| Key | Default | Purpose |
|---|---|---|
| `verdict.pythonPath` | `""` | Python interpreter to run `python -m verdict.cli`. Empty → use `verdict` from PATH. |
| `verdict.reportPath` | `"verdict-report.json"` | Where to read the report from. |
| `verdict.diffRange` | `"HEAD"` | Default `--diff-range` for in-tab runs. |
| `verdict.groupBy` | `"type"` | `type` / `file` / `severity`. |
| `verdict.sortBy` | `"severity"` | `severity` / `file` / `title`. |

---

## Repo layout

```
verdict/
├── verdict/                       # The Python package
│   ├── cli.py                     # `verdict run`, `verdict mcp-install`, `verdict dashboard`
│   ├── diff.py                    # git diff parsing → ChangedFile[]
│   ├── ast_utils.py               # AST walk → AddedFunction[]
│   ├── report.py                  # Scorecard construction, terminal/JSON formatting
│   ├── types.py                   # Shared TypedDicts (the contract between checks)
│   ├── mcp_server.py              # `verdict-mcp` entry point
│   ├── dashboard_cmd.py           # Backfill + local HTTP server
│   ├── _tracer_plugin.py          # pytest plugin: function-execution tracer (dynamic)
│   ├── _coverage_plugin.py        # pytest plugin: line-level coverage (dynamic)
│   ├── bob_integration/
│   │   ├── custom_mode.yaml       # The "Verifier" Custom Mode
│   │   └── slash_commands/
│   │       └── verify.md          # /verify slash command
│   └── checks/                    # The seven checks (auto-discovered via pkgutil)
│       ├── dead_functions.py
│       ├── vacuous_tests.py
│       ├── hallucinated_api.py
│       ├── phantom_files.py
│       ├── suppressed_exc.py
│       ├── trace.py
│       └── coverage_delta.py
│
├── verdict-vscode/                # The VS Code / Bob extension ("Verdict tab")
│   ├── package.json               # Manifest: tab, commands, settings
│   ├── src/
│   │   ├── extension.ts           # activate(), command wiring, file watcher
│   │   ├── findingsStore.ts       # Load + normalize the JSON report
│   │   ├── statusStore.ts         # .bob/verdict-state.json triage persistence
│   │   ├── statusBar.ts           # Left-side status-bar item
│   │   ├── verdictRunner.ts       # Spawns the CLI, streams to output channel
│   │   └── webviewProvider.ts     # Webview host (HTML/CSP, host↔webview messages)
│   ├── media/
│   │   ├── main.css               # Design tokens + components
│   │   ├── main.js                # Webview client (toolbar, list, detail)
│   │   └── verdict.svg            # Tab icon
│   └── verdict-vscode-0.2.0.vsix  # Prebuilt, install directly
│
├── dashboard/                     # Analytics dashboard (static HTML + per-commit JSON)
│   ├── index.html
│   ├── app.js
│   ├── style.css
│   ├── backfill.py
│   └── data/                      # One <sha>.json per scored commit
│
├── tests/                         # Pytest suite for the checks and CLI
├── pyproject.toml                 # Python packaging
├── action.yml                     # GitHub Action wrapper for CI
├── Dockerfile                     # Containerized verdict runner
└── README.md
```

---

## Design choices worth calling out

**Static + dynamic, not just one.** Static-only catches dead code and obvious lies but can't tell you whether the tests actually exercise the new function. Dynamic-only requires a working test suite and is slow. Verdict runs both, so a project with no tests still gets meaningful static findings, and a project with tests gets the deeper dynamic signal.

**Per-check timeout, never a stuck audit.** Dynamic checks run pytest under a tracer. If a project's test suite hangs, the MCP server would hang too. Each check is wrapped in a `ThreadPoolExecutor.result(timeout=…)` so one slow check can't take down the whole audit — it produces a `check_timed_out` finding and Verdict moves on.

**Stable finding IDs.** Triage state (dismissed / resolved) is keyed by `sha1(kind \0 file \0 line \0 message).slice(0, 12)`. Re-running Verdict doesn't lose your triage decisions *unless* the underlying finding genuinely changed.

**Checks are plug-ins, not hardcoded.** `discover_checks()` walks `verdict.checks` via `pkgutil.iter_modules` and pulls each module's top-level `check` attribute. Adding an eighth check is one new file in `verdict/checks/` — no registry, no wiring.

**Bob-first but not Bob-only.** Every Bob-specific integration (MCP, Custom Mode, slash command, .vsix) is optional. The CLI is the primary surface. Anything that works in Bob works in plain VS Code, and the CLI works without any editor.

---

## Roadmap / known gaps

- **Scorecard is a hard threshold.** A 0.80-confidence finding is `SUSPICIOUS`; 0.81 jumps to `LIED`. Replacement plan (Bayesian aggregation with per-check priors, corroboration bonus, soft bands) is sketched in `verdict/report.py`.
- **Python only.** All checks parse Python AST. Adding TypeScript/Go is a straightforward fork of `ast_utils.py` and the static checks, but it's not done.
- **Confidences are uncalibrated guesses.** Each check author picked their own. A small labeled fixture corpus + per-check precision/recall tuning is the path to real probabilities.
- **VS Code extension engine target is high.** Currently `^1.85.0`; lowering it is a one-line fix to broaden Bob/VS Code compatibility.

---

## Made for the IBM Bob hackathon (May 2026)

Verdict is the team's submission. The team:

- **Neel** 
- **Jacob** 
- **Alexie**
- **Ben** 

Built end-to-end on Bob (a lot of Verdict was written *by* the thing it audits).
