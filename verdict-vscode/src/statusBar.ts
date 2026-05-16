import * as vscode from 'vscode';
import { PanelState } from './findingsStore';

export class VerdictStatusBar {
  private readonly item: vscode.StatusBarItem;

  constructor() {
    this.item = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
    this.item.command = 'verdict.focusPanel';
    this.item.show();
    this.update(undefined);
  }

  update(state: PanelState | undefined): void {
    if (!state || !state.hasReport) {
      this.item.text = '$(checklist) Verdict: —';
      this.item.tooltip = 'No verdict report yet. Click to open the Verdict panel.';
      this.item.backgroundColor = undefined;
      return;
    }
    const v = state.effectiveVerdict;
    const open = state.totals.open;
    this.item.text = `$(checklist) Verdict: ${v} · ${open} open`;
    this.item.tooltip =
      `${state.totals.total} total · ${state.totals.open} open · ` +
      `${state.totals.ignored} ignored · ${state.totals.resolved} resolved` +
      `  (diff: ${state.diffRange})`;

    if (v === 'LIED') {
      this.item.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
    } else if (v === 'SUSPICIOUS') {
      this.item.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
    } else {
      this.item.backgroundColor = undefined;
    }
  }

  dispose(): void {
    this.item.dispose();
  }
}
