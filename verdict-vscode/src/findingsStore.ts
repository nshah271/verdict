import * as crypto from 'crypto';
import * as fs from 'fs';
import * as path from 'path';
import * as vscode from 'vscode';
import { StatusStore } from './statusStore';

export type VerdictLevel = 'PASS' | 'SUSPICIOUS' | 'LIED';
export type FindingStatus = 'open' | 'ignored' | 'resolved';

export type CanonicalKind =
  | 'dead_function'
  | 'vacuous_test'
  | 'hallucinated_api'
  | 'phantom_file'
  | 'suppressed_exc'
  | 'trace_not_run'
  | 'coverage_delta';

export interface KindMeta {
  kind: CanonicalKind;
  label: string;
  hint: string;
  swatchHue: number;
  glyph: string;
}

export const KIND_ORDER: CanonicalKind[] = [
  'dead_function',
  'vacuous_test',
  'hallucinated_api',
  'phantom_file',
  'suppressed_exc',
  'trace_not_run',
  'coverage_delta',
];

export const KIND_META: Record<CanonicalKind, KindMeta> = {
  dead_function: {
    kind: 'dead_function',
    label: 'Dead Functions',
    hint: 'Added function is never referenced anywhere in the repo.',
    swatchHue: 25,
    glyph: '☠',
  },
  vacuous_test: {
    kind: 'vacuous_test',
    label: 'Vacuous Tests',
    hint: 'Test runs, but asserts nothing meaningful about behavior.',
    swatchHue: 285,
    glyph: '🧪',
  },
  hallucinated_api: {
    kind: 'hallucinated_api',
    label: 'Hallucinated APIs',
    hint: 'Calls a function, method, or attribute that does not exist.',
    swatchHue: 320,
    glyph: '👻',
  },
  phantom_file: {
    kind: 'phantom_file',
    label: 'Phantom Files',
    hint: 'Imports or references a file that is not present in the repo.',
    swatchHue: 50,
    glyph: '📄',
  },
  suppressed_exc: {
    kind: 'suppressed_exc',
    label: 'Suppressed Exceptions',
    hint: 'Catch-all that swallows exceptions silently.',
    swatchHue: 90,
    glyph: '🛡',
  },
  trace_not_run: {
    kind: 'trace_not_run',
    label: 'Untraced Code',
    hint: 'New code path is never executed when the test suite runs.',
    swatchHue: 200,
    glyph: '🛣',
  },
  coverage_delta: {
    kind: 'coverage_delta',
    label: 'Coverage Regressions',
    hint: 'Coverage of touched files dropped versus the base ref.',
    swatchHue: 152,
    glyph: '📊',
  },
};

const RAW_KIND_MAP: Record<string, CanonicalKind> = {
  dead_function: 'dead_function',
  vacuous_test: 'vacuous_test',
  hallucinated_api: 'hallucinated_api',
  phantom_file: 'phantom_file',
  suppressed_exc: 'suppressed_exc',
  suppressed_exception: 'suppressed_exc',
  trace_not_run: 'trace_not_run',
  never_executed: 'trace_not_run',
  coverage_delta: 'coverage_delta',
  low_coverage_delta: 'coverage_delta',
  coverage_not_run: 'coverage_delta',
};

interface RawFinding {
  kind: string;
  file: string;
  line: number;
  message: string;
  confidence: number;
}

interface RawScorecard {
  verdict: VerdictLevel;
  findings: RawFinding[];
  summary: Record<string, unknown>;
}

export interface EnrichedFinding {
  id: string;
  rawKind: string;
  kind: CanonicalKind | 'unknown';
  file: string;
  line: number;
  title: string;
  message: string;
  confidence: number;
  status: FindingStatus;
}

export interface PanelState {
  hasReport: boolean;
  scorecardVerdict: VerdictLevel;          // raw from CLI
  effectiveVerdict: VerdictLevel;          // recomputed from open findings only
  findings: EnrichedFinding[];
  totals: { total: number; open: number; ignored: number; resolved: number };
  diffRange: string;
  reportSummary: Record<string, unknown>;
}

export class FindingsStore {
  constructor(
    private readonly folder: vscode.WorkspaceFolder,
    private readonly statusStore: StatusStore,
  ) {}

  load(): PanelState {
    const cfg = vscode.workspace.getConfiguration('verdict');
    const diffRange = (cfg.get<string>('diffRange') ?? 'HEAD').trim() || 'HEAD';
    const reportRel = cfg.get<string>('reportPath') ?? 'verdict-report.json';
    const reportFile = path.join(this.folder.uri.fsPath, reportRel);

    const raw = this.readReport(reportFile);
    if (!raw) {
      return {
        hasReport: false,
        scorecardVerdict: 'PASS',
        effectiveVerdict: 'PASS',
        findings: [],
        totals: { total: 0, open: 0, ignored: 0, resolved: 0 },
        diffRange,
        reportSummary: {},
      };
    }

    const persisted = this.statusStore.load();
    const seen = new Set<string>();
    const findings: EnrichedFinding[] = raw.findings.map((f) => {
      const id = makeId(f);
      seen.add(id);
      const kind = (RAW_KIND_MAP[f.kind] ?? 'unknown') as CanonicalKind | 'unknown';
      return {
        id,
        rawKind: f.kind,
        kind,
        file: f.file,
        line: f.line,
        title: firstSentence(f.message),
        message: f.message,
        confidence: f.confidence,
        status: persisted[id] ?? 'open',
      };
    });

    this.statusStore.prune(seen);

    const totals = { total: findings.length, open: 0, ignored: 0, resolved: 0 };
    for (const f of findings) {
      totals[f.status]++;
    }

    return {
      hasReport: true,
      scorecardVerdict: raw.verdict,
      effectiveVerdict: computeEffectiveVerdict(findings),
      findings,
      totals,
      diffRange,
      reportSummary: raw.summary ?? {},
    };
  }

  private readReport(file: string): RawScorecard | undefined {
    try {
      const raw = fs.readFileSync(file, 'utf-8');
      const parsed = JSON.parse(raw) as Partial<RawScorecard>;
      if (!parsed.verdict || !Array.isArray(parsed.findings)) return undefined;
      return parsed as RawScorecard;
    } catch {
      return undefined;
    }
  }
}

function makeId(f: RawFinding): string {
  const h = crypto.createHash('sha1');
  h.update(`${f.kind}\0${f.file}\0${f.line}\0${f.message}`);
  return h.digest('hex').slice(0, 12);
}

function firstSentence(msg: string): string {
  const idx = msg.indexOf('. ');
  if (idx === -1) return msg.trim();
  return msg.slice(0, idx + 1).trim();
}

function computeEffectiveVerdict(findings: EnrichedFinding[]): VerdictLevel {
  const open = findings.filter((f) => f.status === 'open');
  if (open.length === 0) return 'PASS';
  if (open.some((f) => f.confidence > 0.8)) return 'LIED';
  return 'SUSPICIOUS';
}
