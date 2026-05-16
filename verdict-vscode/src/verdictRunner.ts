import * as cp from 'child_process';
import * as vscode from 'vscode';

interface RunOpts {
  staticOnly: boolean;
}

let output: vscode.OutputChannel | undefined;
function log(): vscode.OutputChannel {
  if (!output) {
    output = vscode.window.createOutputChannel('Verdict');
  }
  return output;
}

export async function runVerdict(opts: RunOpts): Promise<void> {
  const folder = vscode.workspace.workspaceFolders?.[0];
  if (!folder) {
    vscode.window.showErrorMessage('Verdict: no workspace folder is open.');
    return;
  }

  const cfg = vscode.workspace.getConfiguration('verdict');
  const pythonPath = (cfg.get<string>('pythonPath') ?? '').trim();
  const diffRange = (cfg.get<string>('diffRange') ?? 'HEAD').trim() || 'HEAD';

  const baseArgs = ['run', folder.uri.fsPath, '--json', '--diff-range', diffRange];
  if (opts.staticOnly) {
    baseArgs.push('--static-only');
  }

  const { cmd, args } = pythonPath
    ? { cmd: pythonPath, args: ['-m', 'verdict.cli', ...baseArgs] }
    : { cmd: 'verdict', args: baseArgs };

  const out = log();
  const header = opts.staticOnly ? 'static audit' : 'full audit';
  out.appendLine(`\n[verdict] ${new Date().toISOString()} starting ${header}`);
  out.appendLine(`[verdict] cwd: ${folder.uri.fsPath}`);
  out.appendLine(`[verdict] cmd: ${cmd} ${args.join(' ')}`);

  await vscode.window.withProgress(
    {
      location: vscode.ProgressLocation.Window,
      title: `Verdict: ${header}…`,
    },
    () =>
      new Promise<void>((resolve) => {
        let stderr = '';
        let stdoutBytes = 0;
        let spawned: cp.ChildProcess;
        try {
          // shell:true so Windows resolves `verdict` -> `verdict.exe` via PATHEXT,
          // and so pythonPath paths with spaces work consistently across platforms.
          spawned = cp.spawn(cmd, args, {
            cwd: folder.uri.fsPath,
            shell: true,
            windowsHide: true,
          });
        } catch (err) {
          handleLaunchFailure(cmd, err);
          resolve();
          return;
        }

        spawned.on('error', (err) => {
          handleLaunchFailure(cmd, err);
          resolve();
        });
        spawned.stdout?.on('data', (d: Buffer) => {
          stdoutBytes += d.length;
        });
        spawned.stderr?.on('data', (d: Buffer) => {
          stderr += d.toString();
        });
        spawned.on('close', (code) => {
          out.appendLine(`[verdict] exit code: ${code}, stdout bytes: ${stdoutBytes}`);
          if (stderr) {
            out.appendLine('[verdict] stderr:');
            out.appendLine(stderr);
          }
          // CLI exits 0 on success and 1 only when --fail-on triggers. Any other
          // non-zero exit (e.g. 127 command not found, 2 click error) means the
          // run actually failed and we should not silently swallow it.
          if (code !== 0 && code !== 1) {
            const tail = stderr.trim().split('\n').slice(-3).join('\n') || '(no stderr)';
            vscode.window
              .showErrorMessage(
                `Verdict: ${header} failed (exit ${code}). ${tail}`,
                'Show Output',
              )
              .then((choice) => {
                if (choice === 'Show Output') out.show(true);
              });
          }
          resolve();
        });
      }),
  );
}

function handleLaunchFailure(cmd: string, err: unknown): void {
  const msg = err instanceof Error ? err.message : String(err);
  const out = log();
  out.appendLine(`[verdict] launch failure: ${msg}`);
  vscode.window
    .showErrorMessage(
      `Verdict: failed to launch "${cmd}" (${msg}). ` +
        'Install verdict (pip install verdict-ai) or set "verdict.pythonPath" in settings.',
      'Show Output',
    )
    .then((choice) => {
      if (choice === 'Show Output') out.show(true);
    });
}
