# verdict-vscode

Bottom-panel tab for the [verdict](https://github.com/nshah271/verdict) AI code auditor. Renders the latest scorecard from `verdict-report.json` as a two-pane Findings view with status persistence, fuzzy search, and a "Fix with Bob" handoff.

Implements the design in [`../handoff.md`](../handoff.md).

## Prerequisites

- **Node.js 20+** (for the TypeScript toolchain and `@vscode/vsce` packager).
- **Bob IDE** (or upstream VS Code 1.85+) for install/use.
- **`verdict` CLI** on `PATH`, or a Python interpreter with `pip install verdict-ai`. The extension shells out to `verdict run …`. If `verdict` is not on `PATH`, set `verdict.pythonPath` in workspace settings to a Python that has the package installed; the extension will fall back to `<python> -m verdict.cli …`.

## Build

```bash
cd verdict-vscode
npm install
npm run compile          # tsc → out/
```

That's enough to run the extension from source (Extension Development Host, F5 in another VS Code window pointing at this folder).

## Package as VSIX

```bash
npx @vscode/vsce package --no-dependencies --allow-missing-repository
```

Produces `verdict-vscode-<version>.vsix` in this directory. The `--no-dependencies` flag is required because we use Node's `child_process` directly and have no runtime deps to bundle.

## Install into Bob (or VS Code)

Pick one:

1. **UI:** Extensions panel → `…` menu → **Install from VSIX…** → pick the `.vsix`. Reload window.
2. **Command Palette:** `Ctrl+Shift+P` → "Extensions: Install from VSIX…".
3. **CLI:** `code --install-extension verdict-vscode-<version>.vsix` (or `bob --install-extension …` for Bob).

Open a git repo, reveal the bottom panel, switch to the **Verdict** tab.

## Develop

```bash
npm run watch            # tsc -w; auto-recompiles src/*.ts
```

While `watch` is running, hit **F5** in this folder to launch an Extension Development Host. Reload that host (`Ctrl+R`) after each change.

For webview changes (`media/*.css`, `media/*.js`), reloading the host is enough — they're not compiled, just loaded at runtime.

## Layout

```
verdict-vscode/
├── package.json                  # extension manifest, commands, view contributions, settings
├── tsconfig.json
├── src/
│   ├── extension.ts              # activate(), command wiring, file watcher, host impl
│   ├── findingsStore.ts          # load report, normalize kinds, enrich with id/title/status
│   ├── statusStore.ts            # .bob/verdict-state.json persistence
│   ├── statusBar.ts              # left status-bar item
│   ├── verdictRunner.ts          # cp.spawn the verdict CLI, log to output channel
│   └── webviewProvider.ts        # WebviewViewProvider — HTML/CSP, host↔webview messages
└── media/
    ├── main.css                  # design tokens + components (handoff §9)
    ├── main.js                   # webview client (toolbar, list, detail, dropdowns)
    └── verdict.svg               # tab icon
```

## Settings (workspace or user)

| Key | Default | Purpose |
|---|---|---|
| `verdict.pythonPath`  | `""` | Python interpreter; empty means use `verdict` on PATH. |
| `verdict.reportPath`  | `"verdict-report.json"` | Report path, relative to workspace root. |
| `verdict.diffRange`   | `"HEAD"` | Git range passed to `verdict run --diff-range …`. |
| `verdict.groupBy`     | `"type"` | `type` / `file` / `severity`. |
| `verdict.sortBy`      | `"severity"` | `severity` / `file` / `title`. |

## Troubleshooting

- **"failed to launch verdict"** — the CLI isn't on PATH. Either `pip install verdict-ai` so the `verdict` console script is available, or set `verdict.pythonPath` to a Python that has the package. See the **Verdict** output channel (View → Output → "Verdict") for the exact invocation, exit code, and stderr.
- **Empty tab / "no findings"** — `verdict-report.json` is missing or its diff range matched no changes. Click the **HEAD** dropdown in the toolbar and try `HEAD~1` or wider; or run `verdict run --diff-range HEAD~1 --json` from a terminal to generate the report.
- **Status changes don't persist across re-runs** — confirm `.bob/verdict-state.json` is writable and the finding's `id` is stable. The id is `sha1(kind\0file\0line\0message).slice(0, 12)`; verdict CLI output changing any of those four invalidates the persisted status.
