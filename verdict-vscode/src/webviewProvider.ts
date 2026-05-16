import * as vscode from 'vscode';
import {
  EnrichedFinding,
  FindingStatus,
  KIND_META,
  KIND_ORDER,
  PanelState,
} from './findingsStore';

export interface Host {
  getState(): PanelState;
  setStatus(id: string, status: FindingStatus): void;
  goto(file: string, line: number): void;
  setDiffRange(range: string): Promise<void>;
  pickCustomDiffRange(): Promise<string | undefined>;
  setGroupBy(value: string): Promise<void>;
  setSortBy(value: string): Promise<void>;
  runAudit(): Promise<void>;
  runStatic(): Promise<void>;
  fixWithBob(finding: EnrichedFinding): Promise<void>;
}

export class VerdictWebviewProvider implements vscode.WebviewViewProvider {
  public static readonly viewType = 'verdict.panel';
  private view?: vscode.WebviewView;

  constructor(
    private readonly extensionUri: vscode.Uri,
    private readonly host: Host,
  ) {}

  resolveWebviewView(view: vscode.WebviewView): void {
    this.view = view;
    view.webview.options = {
      enableScripts: true,
      localResourceRoots: [vscode.Uri.joinPath(this.extensionUri, 'media')],
    };
    view.webview.html = this.renderHtml(view.webview);

    view.webview.onDidReceiveMessage(async (msg) => {
      switch (msg?.type) {
        case 'ready':
          this.push();
          return;
        case 'setStatus':
          this.host.setStatus(msg.id, msg.status);
          return;
        case 'goto':
          this.host.goto(msg.file, msg.line);
          return;
        case 'setDiffRange':
          await this.host.setDiffRange(msg.range);
          return;
        case 'pickCustomDiffRange': {
          const v = await this.host.pickCustomDiffRange();
          if (v) await this.host.setDiffRange(v);
          return;
        }
        case 'setGroupBy':
          await this.host.setGroupBy(msg.value);
          return;
        case 'setSortBy':
          await this.host.setSortBy(msg.value);
          return;
        case 'runAudit':
          await this.host.runAudit();
          return;
        case 'runStatic':
          await this.host.runStatic();
          return;
        case 'fixWithBob': {
          const f = this.host.getState().findings.find((x) => x.id === msg.id);
          if (f) await this.host.fixWithBob(f);
          return;
        }
      }
    });
  }

  push(): void {
    if (!this.view) return;
    const state = this.host.getState();
    const cfg = vscode.workspace.getConfiguration('verdict');
    this.view.webview.postMessage({
      type: 'state',
      state,
      kindMeta: KIND_META,
      kindOrder: KIND_ORDER,
      groupBy: cfg.get<string>('groupBy') ?? 'type',
      sortBy: cfg.get<string>('sortBy') ?? 'severity',
    });
  }

  setBadge(count: number): void {
    if (!this.view) return;
    if (count > 0) {
      this.view.badge = { value: count, tooltip: `${count} open finding(s)` };
    } else {
      this.view.badge = undefined;
    }
  }

  private renderHtml(webview: vscode.Webview): string {
    const nonce = makeNonce();
    const cssUri = webview.asWebviewUri(
      vscode.Uri.joinPath(this.extensionUri, 'media', 'main.css'),
    );
    const jsUri = webview.asWebviewUri(
      vscode.Uri.joinPath(this.extensionUri, 'media', 'main.js'),
    );
    return /* html */ `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta http-equiv="Content-Security-Policy"
    content="default-src 'none';
             style-src ${webview.cspSource} 'unsafe-inline';
             script-src 'nonce-${nonce}';
             font-src ${webview.cspSource};
             img-src ${webview.cspSource} data:;" />
  <link rel="stylesheet" href="${cssUri}" />
  <title>Verdict</title>
</head>
<body>
  <div id="root"></div>
  <script nonce="${nonce}" src="${jsUri}"></script>
</body>
</html>`;
  }
}

function makeNonce(): string {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let s = '';
  for (let i = 0; i < 32; i++) s += chars.charAt(Math.floor(Math.random() * chars.length));
  return s;
}
