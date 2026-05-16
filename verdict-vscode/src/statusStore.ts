import * as fs from 'fs';
import * as path from 'path';
import * as vscode from 'vscode';
import { FindingStatus } from './findingsStore';

const STATE_REL = path.join('.bob', 'verdict-state.json');

interface StateFile {
  version: 1;
  statuses: Record<string, FindingStatus>;
}

export class StatusStore {
  private cache: Record<string, FindingStatus> | undefined;
  private readonly file: string;

  constructor(private readonly folder: vscode.WorkspaceFolder) {
    this.file = path.join(folder.uri.fsPath, STATE_REL);
  }

  load(): Record<string, FindingStatus> {
    if (this.cache) return this.cache;
    try {
      const raw = fs.readFileSync(this.file, 'utf-8');
      const parsed = JSON.parse(raw) as Partial<StateFile>;
      this.cache = parsed.statuses ?? {};
    } catch {
      this.cache = {};
    }
    return this.cache;
  }

  set(id: string, status: FindingStatus): void {
    const statuses = this.load();
    if (status === 'open') {
      delete statuses[id];
    } else {
      statuses[id] = status;
    }
    this.write();
  }

  prune(currentIds: Set<string>): void {
    const statuses = this.load();
    let changed = false;
    for (const id of Object.keys(statuses)) {
      if (!currentIds.has(id)) {
        delete statuses[id];
        changed = true;
      }
    }
    if (changed) this.write();
  }

  private write(): void {
    try {
      fs.mkdirSync(path.dirname(this.file), { recursive: true });
      const data: StateFile = { version: 1, statuses: this.cache ?? {} };
      fs.writeFileSync(this.file, JSON.stringify(data, null, 2), 'utf-8');
    } catch (e) {
      console.warn('[verdict] failed to persist status:', e);
    }
  }
}
