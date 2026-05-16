# Verdict Tab — Implementation Handoff

**Target:** A new bottom-panel tab in the Bob IDE (VSCode fork), peer of PROBLEMS / OUTPUT / DEBUG CONSOLE / TERMINAL / PORTS. Modeled on the Bob Findings tab pattern.

**Source of truth for the data:** the `verdict` CLI in [`nshah271/verdict`](https://github.com/nshah271/verdict) — specifically `verdict/types.py` (`Finding`, `Scorecard`, `VerdictLevel`) and `verdict/report.py` (`build_scorecard`). The 7 issue groups map 1:1 to the 7 check modules in `verdict/checks/`.

**Companion prototype:** `Verdict Tab.html` in this project (React + Babel). Use it as the visual reference. The locked-in user choices are encoded below — do **not** ship the other tweak variants.

---

## 1. Locked-in design choices

| Token | Value |
|---|---|
| **Accent (`--accent`)** | `oklch(0.66 0.13 152)` (justice green, hex ≈ `#2f9466`) |
| **Accent hover (`--accent-2`)** | `oklch(0.58 0.13 152)` |
| **Row density** | Compact — 22 px row height (not 26 px) |
| **Status indicator style** | **Text** — colored word ("open" / "ignored" / "resolved"), no pill chip, no dot |
| **Grouping** | By **Type** (the 7 check kinds), user-toggleable to File / Severity |
| **Sort within group** | Severity (confidence desc) by default; user-toggleable to File / Title |

The other tweak axes (status pill/dot style, comfortable density, other accent colors, group-by File/Severity) were explored and discarded — implement only the locked-in defaults, but keep Group-by and Sort as live dropdowns since they're useful at runtime.

---

## 2. The 7 issue groups

Each group's `kind` matches `Finding.kind` emitted by the corresponding check module.

| # | `kind` value | Group label | One-line hint shown next to label |
|---|---|---|---|
| 1 | `dead_function`     | Dead Functions         | Added function is never referenced anywhere in the repo. |
| 2 | `vacuous_test`      | Vacuous Tests          | Test runs, but asserts nothing meaningful about behavior. |
| 3 | `hallucinated_api`  | Hallucinated APIs      | Calls a function, method, or attribute that does not exist. |
| 4 | `phantom_file`      | Phantom Files          | Imports or references a file that is not present in the repo. |
| 5 | `suppressed_exc`    | Suppressed Exceptions  | Catch-all that swallows exceptions silently. |
| 6 | `trace_not_run`     | Untraced Code          | New code path is never executed when the test suite runs. |
| 7 | `coverage_delta`    | Coverage Regressions   | Coverage of touched files dropped versus the base ref. |

Each group also has a per-kind icon and a per-kind accent (used for the small square icon swatch only — does not override the global green accent). Render groups in the order above. Hide groups whose filtered item list is empty.

---

## 3. Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ PROBLEMS | OUTPUT | DEBUG CONSOLE | TERMINAL | PORTS | VERDICT (count) ...  │  ← panel tab bar
├──────────────────────────────────┬──────────────────────────────────────────┤
│ ┌HEAD ▼┐ ┌🔍 fuzzy search──────┐ │  [kind tag] [kind label]                 │
│ └──────┘ └─────────────────────┘ │  Title of Issue                          │
│ ┌Group▼┐ ┌Sort ▼┐                │  confidence ▓▓▓▓░░ 0.92  head:HEAD  open │
│ └──────┘ └──────┘                ├──────────────────────────────────────────┤
├──────────────────────────────────┤  Description paragraph...                │
│ ▼ ☠ Dead Functions — hint    (3) │                                          │
│     issue 1 title       file:42  │  ┌─ Why Verdict flagged this ─────────┐  │
│     issue 2 title …     file:88  │  │ Per-kind hint from §2              │  │
│     issue 3 title …     file:120 │  └────────────────────────────────────┘  │
│ ▼ 🧪 Vacuous Tests — hint   (3)  │                                          │
│     …                            ├──────────────────────────────────────────┤
│ ▼ 👻 Hallucinated APIs — hint(2) │  Location  /abs/path/to/file.py:142      │
│ ▼ 📄 Phantom Files — hint   (2)  ├──────────────────────────────────────────┤
│ ▼ 🛡 Suppressed Excs — hint (3)  │  [Go To Location] [Dismiss]              │
│ ▼ 🛣 Untraced Code — hint  (3)   │  [✨ Fix with Bob] [✓ Mark as Resolved]  │
│ ▼ 📊 Coverage Regr — hint  (2)   │                                          │
├──────────────────────────────────┴──────────────────────────────────────────┤
│ Verdict [SUSPICIOUS]  19 total  9 open  2 ignored  2 resolved  main..HEAD   │  ← status bar
└─────────────────────────────────────────────────────────────────────────────┘
```

Two-pane split inside the tab. Left ~48 %, right ~52 %. Both panes scroll independently. When nothing is selected, the right pane shows the aggregate Verdict scorecard banner ("PASS" / "SUSPICIOUS" / "LIED" per `report.py`'s rule) + a "Select a finding to see the full report" hint.

---

## 4. Toolbar (top of left pane)

Left → right, single row, 8 px gap:

1. **HEAD-range dropdown.** Label tag "HEAD" in uppercase 10 px, then a monospace value. Options:
   - `HEAD` — uncommitted vs. HEAD (default)
   - `HEAD~1` — last commit
   - `HEAD~3` — last 3 commits
   - `main..HEAD` — current branch vs. main
   - `origin/main..` — ahead of origin/main
   - `PR #<n>` — when a Bob PR session is active, populate from the PR's `--diff-range`
   Changing this re-runs `verdict --diff-range <value> --json` and replaces the findings list.
2. **Fuzzy search.** Filters across `title`, `message`, `file`, `kind`. Clear-X button on the right when populated. Search auto-expands all groups so matches are visible.
3. **Group dropdown.** Type (default) / File / Severity. Value persists per workspace.
4. **Sort dropdown.** Severity (default) / File / Title.

---

## 5. List rows (compact)

- Row height **22 px**. Single visual line.
- Columns, left → right: 2 px selection indicator · 12 px chevron column (only on group headers) · 18 px kind icon (group headers only) · title (truncated with `…`) · short filename + line in monospace dim gray · status text.
- Status indicator is **text only** — no chip, no dot. Colors:
  - `open`    → `oklch(0.74 0.16 55)` (warm amber), text "open"
  - `ignored` → `oklch(0.62 0.02 280)` (neutral gray), text "ignored"
  - `resolved`→ `oklch(0.72 0.16 152)` (green), text "resolved"
  - Text is lowercase, 10.5 px, weight 600, letter-spacing 0.04 em.
- Selected row: 2 px green left bar, `--bg-active` background (`#34343d`).
- Hover: `--bg-hover` (`#2a2a31`).
- Clicking anywhere on the row opens the detail pane and selects that finding. Clicking the chevron on a group header toggles collapse.
- Group count badge: small pill on the right of the header, current count of items in that group **after** filtering.

---

## 6. Detail pane

Four stacked sections, top → bottom:

1. **Header** (border-bottom).
   - Tiny kind tag: `[colored icon swatch] DEAD FUNCTIONS · dead_function` (kind enum dim).
   - `<h2>` of `finding.title`. 17 px / 600 / line-height 1.35.
   - Meta row, 11.5 px monospace, dim: confidence bar (`bar` filled to `confidence * 100 %`, accent green) + numeric value · `head: <range>` · status word (text style).
2. **Body** (scrolls).
   - `<p>` of `finding.message`.
   - "Why Verdict flagged this" callout — left-border accent (green), small uppercase heading, the per-kind hint string from §2.
3. **Location card.** Single line, monospace.
   `Location <repo_root>/<finding.file>:<finding.line>`
   The line number is rendered in the accent green and bold. Card itself is `--bg` background, 1 px `--border` outline.
4. **Action bar** (border-top, `--bg-2` background, 12 px / 18 px padding).
   Four buttons in one row, wrap on narrow viewports:
   - **Go To Location** — secondary. Invokes the VSCode command `vscode.open` on `file://<absolute>` with `selection: new Range(line-1, 0, line-1, 0)`.
   - **Dismiss** — secondary. Sets `status = "ignored"` (or back to "open" if already ignored — button text flips to "Un-dismiss"). Persists the change (see §8).
   - **Fix with Bob** — **primary** (green accent, dark text). Hands the finding to Bob via the MCP server's fix-handoff. See §7.
   - **Mark as Resolved** — secondary. Sets `status = "resolved"` (or back to "open" — text flips to "Reopen").

Buttons are 32 px tall, 12.5 px font, 4 px radius. Primary uses `--accent` background with `#0d0d11` text. Secondary uses `--bg-3` with 1 px `--border-2` outline.

---

## 7. "Fix with Bob" handoff

The Verdict tab is a thin client. Clicking **Fix with Bob** must:

1. Build a structured prompt from the finding (see template below).
2. Call Bob's "fix-with-context" entry point — refer to `bob.ibm.com/docs/` for the canonical command name and payload schema. The likely shape is to post a chat-thread message with the finding rendered as a Markdown system block plus the file pinned as an attachment.
3. Switch focus to the Bob chat view (`bob.focus` or equivalent) so the user sees the proposed fix.
4. Leave the finding's status as `open` — Bob's PR / accepted-fix flow is responsible for transitioning it to `resolved` (see §8).

**Prompt template** (markdown, fill in `{…}`):

```
You are fixing a Verdict finding flagged by the `{kind}` check.

**Finding:** {title}
**File:** {file}:{line}
**Confidence:** {confidence}
**Why it was flagged:** {kind_hint_from_§2}

**Detail:**
{message}

Please propose a minimal patch that resolves this finding without
introducing new ones. After applying, run `verdict --diff-range HEAD`
to confirm.
```

Per the whiteboard note "Auto gen prompt based on Issue type, can be edited" — this prompt should be **shown to the user in an editable text area before sending**. Default to the template above; let the user tweak and confirm.

---

## 8. State model

```ts
type Finding = {
  id: string;        // stable hash of (kind, file, line, message)
  kind: "dead_function" | "vacuous_test" | "hallucinated_api"
      | "phantom_file" | "suppressed_exc" | "trace_not_run" | "coverage_delta";
  file: string;      // repo-relative
  line: number;      // 1-indexed
  title: string;     // short one-liner (≈ verdict's `Finding.message` first sentence)
  message: string;   // full explanation
  confidence: number; // 0..1
  status: "open" | "ignored" | "resolved";
};
```

`verdict.types.Finding` does **not** currently carry `id` / `title` / `status`. The IDE side must derive:

- **`id`**: `sha1(kind + "\0" + file + "\0" + line + "\0" + message).slice(0, 12)` — stable across re-runs of the same diff.
- **`title`**: first sentence of `message` (split on `. `).
- **`status`**: stored locally per workspace. Persistence options:
  1. `verdict status` workspace state file (e.g. `.bob/verdict-state.json`) keyed by `id`.
  2. VSCode `Memento` (`context.workspaceState.get("verdict.findingStatus")`).
  Either works; the file-on-disk option lets `verdict` itself respect dismissed findings on subsequent runs.

When `verdict` re-runs, merge the fresh findings list with persisted statuses by `id`. Findings whose `id` disappears between runs are dropped (the underlying issue went away — the user's "resolved" decision is no longer relevant). Findings whose `id` reappears retain their stored status.

Aggregate scorecard (status-bar Verdict tag) uses **only `status === "open"`** findings:
- 0 open → **PASS** (green)
- any open → **SUSPICIOUS** (amber)
- any open with `confidence > 0.8` → **LIED** (red)

This is `report.build_scorecard`'s rule, but applied after filtering out ignored/resolved.

---

## 9. Visual tokens (CSS custom properties)

Drop these into the VSCode theme contribution / extension styles. Names mirror the prototype so the diff against `verdict.css` is mechanical.

```css
:root {
  /* Surfaces — neutral cool-dark, sit on top of whatever Bob theme is active */
  --bg:          var(--vscode-editor-background, #1b1b1f);
  --bg-2:        #202024;
  --bg-3:        #26262c;
  --bg-4:        #2d2d34;
  --bg-hover:    #2a2a31;
  --bg-active:   #34343d;
  --border:      #34343c;
  --border-2:    #41414a;

  /* Text */
  --fg:   #e6e6ea;
  --fg-2: #b8b8c0;
  --fg-3: #82828c;
  --fg-4: #5a5a64;

  /* Accent — justice green (locked) */
  --accent:    oklch(0.66 0.13 152);
  --accent-2:  oklch(0.58 0.13 152);
  --accent-fg: #0d0d11;

  /* Status text colors */
  --st-open:     oklch(0.74 0.16 55);
  --st-ignored:  oklch(0.62 0.02 280);
  --st-resolved: oklch(0.72 0.16 152);

  /* Scorecard tag colors */
  --v-pass:       oklch(0.74 0.16 152);
  --v-suspicious: oklch(0.78 0.16 90);
  --v-lied:       oklch(0.70 0.18 25);

  /* Type */
  --font-ui:   var(--vscode-font-family, "Segoe UI", system-ui, sans-serif);
  --font-mono: var(--vscode-editor-font-family, "JetBrains Mono", Consolas, monospace);

  --row-h: 22px;  /* compact */
}
```

Per-kind icon swatches (used only on the 18 × 18 px icon tile, not anywhere else):

```css
.kt-dead_function    { background: oklch(0.45 0.08 25  / .4); color: oklch(0.82 0.14 25);  }
.kt-vacuous_test     { background: oklch(0.45 0.08 285 / .4); color: oklch(0.82 0.14 285); }
.kt-hallucinated_api { background: oklch(0.45 0.08 320 / .4); color: oklch(0.82 0.14 320); }
.kt-phantom_file     { background: oklch(0.45 0.08 50  / .4); color: oklch(0.82 0.14 50);  }
.kt-suppressed_exc   { background: oklch(0.45 0.08 90  / .4); color: oklch(0.82 0.14 90);  }
.kt-trace_not_run    { background: oklch(0.45 0.08 200 / .4); color: oklch(0.82 0.14 200); }
.kt-coverage_delta   { background: oklch(0.45 0.08 152 / .4); color: oklch(0.82 0.14 152); }
```

Icon names (Codicon equivalents, pick the closest):
- `dead_function` → `circle-slash` or skull-equivalent
- `vacuous_test` → `beaker`
- `hallucinated_api` → `question` / ghost-equivalent
- `phantom_file` → `file-warning`
- `suppressed_exc` → `shield`
- `trace_not_run` → `git-fork` or `circuit-board`
- `coverage_delta` → `graph`

---

## 10. Wiring on the extension side

The Bob IDE is a VSCode fork, so this is a standard webview-or-tree-view extension. Two viable architectures — pick based on what the existing Bob Findings tab uses:

**(a) Native TreeView + custom WebviewView for the detail pane.** Cheap, theme-coherent. The list pane is a `TreeDataProvider` whose nodes are group headers and finding leaves; the detail pane is a `WebviewView` registered in the same `viewsContainer`. Buttons in the detail webview post messages back to the extension host (`vscode.postMessage({command: "dismiss" | "resolve" | "goto" | "fix"})`).

**(b) Pure webview (two-pane layout inside one `<iframe>`).** Closer to the prototype. More layout control, but inherits the cost of re-implementing keyboard nav, virtualization for long lists, and theme tokens. Only worth it if Bob Findings does this.

Either way:

1. **Data source.** Spawn `verdict --diff-range <range> --json` (via `child_process.execFile` or Bob's existing python runner). Parse `scorecard.findings`. Compute `id` / `title` per §8.
2. **Watch.** Re-run on file save in tracked files, on git HEAD change, and when the user picks a new range from the dropdown. Debounce 400 ms.
3. **Persist status.** Write `.bob/verdict-state.json` (gitignored) on every status change.
4. **Commands to register:**
   - `verdict.refresh` — re-run the CLI.
   - `verdict.goto` (args: `{file, line}`) — `vscode.open` + reveal range.
   - `verdict.dismiss` (args: `{id}`) — flip status to `ignored`.
   - `verdict.resolve` (args: `{id}`) — flip status to `resolved`.
   - `verdict.fixWithBob` (args: `{id}`) — build prompt, open Bob, send.
   - `verdict.setHeadRange` (args: `{range}`) — write to workspace state + refresh.
5. **Status-bar item.** Register a `StatusBarItem` (left, priority 100) showing the aggregate verdict tag from §8. Click handler: `workbench.action.togglePanel` + focus the Verdict view.

---

## 11. Files in the prototype to mine

When pulling design code over, the useful files in this project are:

- `verdict.css` — full token + component CSS. Already uses the locked-in green accent and `--row-h: 22px`.
- `verdict-tab.jsx` — React components. The ones worth porting verbatim (or near-verbatim) to whichever webview framework Bob extensions use:
  - `Icon` — inline SVG set
  - `Dropdown` — toolbar dropdown with popover
  - `StatusPill` — handles all three variants; you only need `variant="text"`
  - `IssueRow`, `GroupHead` — list rendering
  - `VerdictTab` — top-level layout, filter/group/sort logic, selection state
- `data.js` — sample findings. Replace with real CLI output; the shape (after enrichment per §8) is identical.

Ignore `tweaks-panel.jsx` and the surrounding IDE chrome (`titlebar`, `editor-mock`, `panel-tabs`, `statusbar`) — they exist only to give the prototype context. The real implementation lives inside the host IDE's chrome.

---

## 12. Out of scope for this ticket

- The auto-generated, editable Bob prompt UI (§7 step 2). Stub it for now: show a confirm dialog with the prompt preview; full editor lands in a follow-up.
- "Hallucinations" as a top-level grouping. The whiteboard mentions it; it's covered by `hallucinated_api`.
- Search-bar advanced filters (the funnel icon in the Bob Findings reference). Defer.
- Keyboard shortcuts beyond the VSCode defaults inherited from the TreeView / webview. Defer.

---

## 13. Acceptance checklist

- [ ] Verdict tab appears in the bottom panel tab strip with a count badge.
- [ ] Selecting the tab shows the two-pane layout; left pane has toolbar + 7 collapsible groups; right pane shows the empty-state scorecard banner.
- [ ] HEAD range dropdown triggers a fresh `verdict` run; results replace the list.
- [ ] Fuzzy search filters across title/message/file/kind; auto-expands groups on input.
- [ ] Group dropdown toggles between Type / File / Severity; Sort dropdown toggles Severity / File / Title.
- [ ] Row height is 22 px; status indicator is colored text only (no pill, no dot).
- [ ] Clicking a row opens the detail pane with header, body, why-flagged callout, location card, and 4 action buttons.
- [ ] **Fix with Bob** is the only primary (green) button in the action bar.
- [ ] **Go To Location** opens the file at the correct line.
- [ ] **Dismiss** / **Mark as Resolved** flip status, persist, and update the row's text + the status-bar aggregate verdict tag.
- [ ] Re-running `verdict` preserves dismissed/resolved status for findings with the same `id`.
- [ ] Status-bar verdict tag matches `report.build_scorecard`'s rule applied to `status === "open"` findings only.
