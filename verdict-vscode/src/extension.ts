import * as vscode from 'vscode';
import {
  EnrichedFinding,
  FindingsStore,
  KIND_META,
  PanelState,
} from './findingsStore';
import { StatusStore } from './statusStore';
import { VerdictStatusBar } from './statusBar';
import { VerdictWebviewProvider, Host } from './webviewProvider';
import { runVerdict } from './verdictRunner';

export function activate(context: vscode.ExtensionContext): void {
  const folder = vscode.workspace.workspaceFolders?.[0];

  const statusStore = folder ? new StatusStore(folder) : undefined;
  const findingsStore = folder && statusStore ? new FindingsStore(folder, statusStore) : undefined;

  const recompute = (): PanelState | undefined => findingsStore?.load();

  const statusBar = new VerdictStatusBar();
  context.subscriptions.push(statusBar);

  const host: Host = {
    getState() {
      return recompute() ?? emptyState();
    },
    setStatus(id, status) {
      if (!statusStore) return;
      statusStore.set(id, status);
      pushAll();
    },
    goto(file, line) {
      if (!folder || !file) return;
      const target = vscode.Uri.joinPath(folder.uri, file);
      const pos = new vscode.Position(Math.max(0, line - 1), 0);
      vscode.window.showTextDocument(target, {
        selection: new vscode.Range(pos, pos),
        preserveFocus: false,
      });
    },
    async setDiffRange(range) {
      await vscode.workspace
        .getConfiguration('verdict')
        .update('diffRange', range, vscode.ConfigurationTarget.Workspace);
      pushAll();
    },
    async pickCustomDiffRange() {
      const cfg = vscode.workspace.getConfiguration('verdict');
      const current = (cfg.get<string>('diffRange') ?? 'HEAD').trim() || 'HEAD';
      return vscode.window.showInputBox({
        title: 'Verdict: custom diff range',
        prompt: 'e.g. HEAD~10, abc123..HEAD, origin/main...HEAD',
        value: current,
      });
    },
    async setGroupBy(value) {
      await vscode.workspace
        .getConfiguration('verdict')
        .update('groupBy', value, vscode.ConfigurationTarget.Workspace);
      pushAll();
    },
    async setSortBy(value) {
      await vscode.workspace
        .getConfiguration('verdict')
        .update('sortBy', value, vscode.ConfigurationTarget.Workspace);
      pushAll();
    },
    async runAudit() {
      await runVerdict({ staticOnly: false });
      pushAll();
    },
    async runStatic() {
      await runVerdict({ staticOnly: true });
      pushAll();
    },
    async fixWithBob(finding) {
      await fixWithBob(finding);
    },
  };

  const provider = folder
    ? new VerdictWebviewProvider(context.extensionUri, host)
    : undefined;

  if (provider) {
    context.subscriptions.push(
      vscode.window.registerWebviewViewProvider(VerdictWebviewProvider.viewType, provider, {
        webviewOptions: { retainContextWhenHidden: true },
      }),
    );
  }

  function pushAll(): void {
    const s = recompute();
    statusBar.update(s);
    provider?.push();
    provider?.setBadge(s?.totals.open ?? 0);
  }

  context.subscriptions.push(
    vscode.commands.registerCommand('verdict.refresh', pushAll),
    vscode.commands.registerCommand('verdict.runAudit', () => host.runAudit()),
    vscode.commands.registerCommand('verdict.runStatic', () => host.runStatic()),
    vscode.commands.registerCommand('verdict.setDiffRange', async () => {
      const range = await pickDiffRange();
      if (range !== undefined) await host.setDiffRange(range);
    }),
    vscode.commands.registerCommand('verdict.goto', (args: { file: string; line: number }) => {
      host.goto(args.file, args.line);
    }),
    vscode.commands.registerCommand('verdict.dismiss', (args: { id: string }) => {
      host.setStatus(args.id, 'ignored');
    }),
    vscode.commands.registerCommand('verdict.resolve', (args: { id: string }) => {
      host.setStatus(args.id, 'resolved');
    }),
    vscode.commands.registerCommand('verdict.fixWithBob', async (args: { id: string }) => {
      const f = host.getState().findings.find((x) => x.id === args.id);
      if (f) await host.fixWithBob(f);
    }),
    vscode.commands.registerCommand('verdict.focusPanel', async () => {
      await vscode.commands.executeCommand('workbench.view.extension.verdict');
      await vscode.commands.executeCommand('verdict.panel.focus');
    }),
  );

  context.subscriptions.push(
    vscode.workspace.onDidChangeConfiguration((e) => {
      if (
        e.affectsConfiguration('verdict.diffRange') ||
        e.affectsConfiguration('verdict.groupBy') ||
        e.affectsConfiguration('verdict.sortBy') ||
        e.affectsConfiguration('verdict.reportPath')
      ) {
        pushAll();
      }
    }),
  );

  if (folder) {
    const reportName =
      vscode.workspace.getConfiguration('verdict').get<string>('reportPath') ?? 'verdict-report.json';
    const watcher = vscode.workspace.createFileSystemWatcher(
      new vscode.RelativePattern(folder, reportName),
    );
    watcher.onDidChange(pushAll);
    watcher.onDidCreate(pushAll);
    watcher.onDidDelete(pushAll);
    context.subscriptions.push(watcher);
  }

  pushAll();
}

export function deactivate(): void {
  // no-op
}

function emptyState(): PanelState {
  return {
    hasReport: false,
    scorecardVerdict: 'PASS',
    effectiveVerdict: 'PASS',
    findings: [],
    totals: { total: 0, open: 0, ignored: 0, resolved: 0 },
    diffRange: 'HEAD',
    reportSummary: {},
  };
}

async function pickDiffRange(): Promise<string | undefined> {
  const cfg = vscode.workspace.getConfiguration('verdict');
  const current = (cfg.get<string>('diffRange') ?? 'HEAD').trim() || 'HEAD';

  interface Item extends vscode.QuickPickItem {
    value?: string;
    custom?: true;
  }

  const presets: Item[] = [
    { label: 'HEAD', description: 'Uncommitted vs HEAD', value: 'HEAD' },
    { label: 'HEAD~1', description: 'Last commit', value: 'HEAD~1' },
    { label: 'HEAD~3', description: 'Last 3 commits', value: 'HEAD~3' },
    { label: 'main..HEAD', description: 'Current branch vs main', value: 'main..HEAD' },
    { label: 'origin/main..', description: 'Ahead of origin/main', value: 'origin/main..' },
    { label: 'Custom…', description: 'Type any git diff range', custom: true },
  ];

  for (const p of presets) {
    if (p.value === current) p.description = `${p.description}  ·  current`;
  }

  const picked = await vscode.window.showQuickPick(presets, {
    title: 'Verdict: diff range',
    placeHolder: `Current: ${current}`,
  });
  if (!picked) return undefined;

  if (picked.custom) {
    return vscode.window.showInputBox({
      title: 'Verdict: custom diff range',
      prompt: 'e.g. HEAD~10, abc123..HEAD, origin/main...HEAD',
      value: current,
    });
  }
  return picked.value;
}

async function fixWithBob(finding: EnrichedFinding): Promise<void> {
  const meta = KIND_META[finding.kind as keyof typeof KIND_META];
  const hint = meta ? meta.hint : '';
  const prompt =
    `You are fixing a Verdict finding flagged by the \`${finding.rawKind || finding.kind}\` check.\n\n` +
    `**Finding:** ${finding.title}\n` +
    `**File:** ${finding.file}:${finding.line}\n` +
    `**Confidence:** ${finding.confidence.toFixed(2)}\n` +
    `**Why it was flagged:** ${hint}\n\n` +
    `**Detail:**\n${finding.message}\n\n` +
    `Please propose a minimal patch that resolves this finding without\n` +
    `introducing new ones. After applying, run \`verdict --diff-range HEAD\`\n` +
    `to confirm.`;

  const choice = await vscode.window.showInformationMessage(
    'Verdict: Fix with Bob',
    {
      modal: true,
      detail:
        'A fix request prompt will be copied to your clipboard so you can paste it into Bob. ' +
        '(Editable prompt UI lands in a follow-up.)\n\n' +
        prompt,
    },
    'Copy & Open Bob',
    'Copy Only',
  );

  if (!choice) return;
  await vscode.env.clipboard.writeText(prompt);

  if (choice === 'Copy & Open Bob') {
    const candidates = [
      'workbench.action.chat.open',
      'workbench.action.chat.openInSidebar',
      'bob.chat.focus',
      'bob.focus',
    ];
    for (const c of candidates) {
      try {
        await vscode.commands.executeCommand(c);
        break;
      } catch {
        // try next
      }
    }
  }
  vscode.window.setStatusBarMessage('Verdict: fix prompt copied to clipboard.', 4000);
}
