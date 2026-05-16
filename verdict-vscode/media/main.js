(() => {
  const vscode = acquireVsCodeApi();

  const HEAD_PRESETS = [
    { value: 'HEAD',           desc: 'Uncommitted vs. HEAD' },
    { value: 'HEAD~1',         desc: 'Last commit' },
    { value: 'HEAD~3',         desc: 'Last 3 commits' },
    { value: 'main..HEAD',     desc: 'Current branch vs main' },
    { value: 'origin/main..',  desc: 'Ahead of origin/main' },
  ];

  const GROUP_OPTS = [
    { value: 'type',     label: 'Type' },
    { value: 'file',     label: 'File' },
    { value: 'severity', label: 'Severity' },
  ];

  const SORT_OPTS = [
    { value: 'severity', label: 'Severity' },
    { value: 'file',     label: 'File' },
    { value: 'title',    label: 'Title' },
  ];

  let state = null;
  let kindMeta = {};
  let kindOrder = [];
  let groupBy = 'type';
  let sortBy = 'severity';
  let search = '';
  let collapsed = new Set();
  let selectedId = null;

  const root = document.getElementById('root');

  function send(msg) { vscode.postMessage(msg); }

  function esc(s) {
    return String(s ?? '').replace(/[&<>"']/g, (c) => ({
      '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;',
    })[c]);
  }
  function basename(p) {
    if (!p) return '';
    const ix = Math.max(p.lastIndexOf('/'), p.lastIndexOf('\\'));
    return ix >= 0 ? p.slice(ix + 1) : p;
  }

  function applyFilter(findings) {
    const q = search.trim().toLowerCase();
    if (!q) return findings;
    return findings.filter((f) =>
      f.title.toLowerCase().includes(q) ||
      f.message.toLowerCase().includes(q) ||
      f.file.toLowerCase().includes(q) ||
      f.kind.toLowerCase().includes(q) ||
      (f.rawKind || '').toLowerCase().includes(q),
    );
  }

  function sortFindings(arr) {
    const cp = arr.slice();
    if (sortBy === 'file') {
      cp.sort((a, b) => a.file.localeCompare(b.file) || a.line - b.line);
    } else if (sortBy === 'title') {
      cp.sort((a, b) => a.title.localeCompare(b.title));
    } else {
      cp.sort((a, b) => b.confidence - a.confidence);
    }
    return cp;
  }

  function groupFindings(findings) {
    const filtered = applyFilter(findings);
    if (groupBy === 'file') {
      const map = new Map();
      for (const f of filtered) {
        if (!map.has(f.file)) map.set(f.file, []);
        map.get(f.file).push(f);
      }
      return [...map.entries()]
        .sort((a, b) => a[0].localeCompare(b[0]))
        .map(([file, items]) => ({
          key: `file:${file}`,
          label: file,
          hint: `${items.length} finding(s) in this file`,
          glyph: '📄',
          tileClass: 'kt-unknown',
          items: sortFindings(items),
        }));
    }
    if (groupBy === 'severity') {
      const buckets = [
        { key: 'severity:high', label: 'High confidence', glyph: '🔴', min: 0.8 },
        { key: 'severity:med',  label: 'Medium confidence', glyph: '🟠', min: 0.6 },
        { key: 'severity:low',  label: 'Low confidence', glyph: '🟡', min: 0 },
      ];
      const out = [];
      let remaining = filtered.slice();
      for (const b of buckets) {
        const items = remaining.filter((f) => f.confidence >= b.min);
        remaining = remaining.filter((f) => f.confidence < b.min);
        if (items.length === 0) continue;
        out.push({
          key: b.key,
          label: b.label,
          hint: `${items.length} finding(s)`,
          glyph: b.glyph,
          tileClass: 'kt-unknown',
          items: sortFindings(items),
        });
      }
      return out;
    }
    // group by type (default)
    const out = [];
    for (const k of kindOrder) {
      const items = filtered.filter((f) => f.kind === k);
      if (items.length === 0) continue;
      const meta = kindMeta[k];
      out.push({
        key: `kind:${k}`,
        label: meta.label,
        hint: meta.hint,
        glyph: meta.glyph,
        tileClass: `kt-${k}`,
        items: sortFindings(items),
      });
    }
    const unknownItems = filtered.filter((f) => !kindOrder.includes(f.kind));
    if (unknownItems.length) {
      out.push({
        key: 'kind:unknown',
        label: 'Other',
        hint: 'Unrecognized kind',
        glyph: '❓',
        tileClass: 'kt-unknown',
        items: sortFindings(unknownItems),
      });
    }
    return out;
  }

  function render() {
    if (!state) {
      root.innerHTML = '';
      return;
    }
    const groups = state.hasReport ? groupFindings(state.findings) : [];
    const selected = state.findings.find((f) => f.id === selectedId);

    root.innerHTML = `
      <div class="split">
        <div class="pane left-pane">
          ${renderToolbar()}
          <div class="list">${renderList(groups)}</div>
        </div>
        <div class="pane">
          <div class="detail">
            ${selected ? renderDetail(selected) : renderEmptyDetail()}
          </div>
        </div>
      </div>
      ${renderStatusBar()}
    `;
    wireToolbar();
    wireList();
    wireDetail();
  }

  function renderToolbar() {
    const diffRange = state.diffRange || 'HEAD';
    const gOpt = GROUP_OPTS.find((o) => o.value === groupBy) || GROUP_OPTS[0];
    const sOpt = SORT_OPTS.find((o) => o.value === sortBy) || SORT_OPTS[0];
    return `
      <div class="toolbar">
        <div class="dd" data-dd="head">
          <span class="dd-tag">HEAD</span>
          <span class="dd-val">${esc(diffRange)}</span>
          <span class="dd-caret">▾</span>
        </div>
        <div class="search-wrap">
          <input class="search" id="search" placeholder="fuzzy search…" value="${esc(search)}" />
          ${search ? `<button class="clear" id="clear-search" title="Clear">×</button>` : ''}
        </div>
        <div class="dd" data-dd="group">
          <span class="dd-tag">Group</span>
          <span class="dd-val">${esc(gOpt.label)}</span>
          <span class="dd-caret">▾</span>
        </div>
        <div class="dd" data-dd="sort">
          <span class="dd-tag">Sort</span>
          <span class="dd-val">${esc(sOpt.label)}</span>
          <span class="dd-caret">▾</span>
        </div>
      </div>
    `;
  }

  function renderList(groups) {
    if (!state.hasReport) {
      return `<div class="empty-list">No verdict report yet. Run an audit from the panel toolbar or via <code>verdict run</code>.</div>`;
    }
    if (groups.length === 0) {
      const msg = search
        ? `No findings match "${esc(search)}".`
        : `No findings in this diff range. Try a wider range (e.g. HEAD~1).`;
      return `<div class="empty-list">${msg}</div>`;
    }
    return groups.map((g) => {
      const isCollapsed = collapsed.has(g.key) && !search;
      const rows = isCollapsed
        ? ''
        : g.items.map((f) => renderRow(f)).join('');
      return `
        <div class="group" data-group="${esc(g.key)}">
          <div class="group-head" data-key="${esc(g.key)}">
            <span class="chev">${isCollapsed ? '▸' : '▾'}</span>
            <span class="tile ${g.tileClass}">${g.glyph}</span>
            <span class="label">${esc(g.label)}</span>
            <span class="hint">— ${esc(g.hint)}</span>
            <span class="badge">${g.items.length}</span>
          </div>
          ${rows}
        </div>
      `;
    }).join('');
  }

  function renderRow(f) {
    const sel = f.id === selectedId ? 'selected' : '';
    return `
      <div class="row ${sel}" data-id="${esc(f.id)}">
        <span class="title">${esc(f.title)}</span>
        <span class="loc">${esc(basename(f.file))}:${f.line}</span>
        <span class="status"><span class="st st-${f.status}">${f.status}</span></span>
      </div>
    `;
  }

  function renderEmptyDetail() {
    const v = state.hasReport ? state.effectiveVerdict : 'PASS';
    const total = state.totals.total;
    return `
      <div class="detail-empty">
        <div class="scorecard-banner">
          <span class="tag ${v}">${v}</span>
          <span class="sub">${state.hasReport
            ? `${total} total · ${state.totals.open} open · ${state.totals.ignored} ignored · ${state.totals.resolved} resolved`
            : 'Run an audit to see findings.'}</span>
        </div>
        <div style="color:var(--fg-3);font-size:11.5px">Select a finding to see the full report.</div>
      </div>
    `;
  }

  function renderDetail(f) {
    const meta = kindMeta[f.kind];
    const tileClass = meta ? `kt-${f.kind}` : 'kt-unknown';
    const glyph = meta ? meta.glyph : '❓';
    const label = meta ? meta.label : 'Other';
    const hint = meta ? meta.hint : f.message;
    const pct = Math.round(f.confidence * 100);
    const isIgnored = f.status === 'ignored';
    const isResolved = f.status === 'resolved';
    return `
      <div class="detail-header">
        <div class="kind-tag">
          <span class="tile ${tileClass}">${glyph}</span>
          <span>${esc(label.toUpperCase())} · ${esc(f.rawKind || f.kind)}</span>
        </div>
        <h2>${esc(f.title)}</h2>
        <div class="meta">
          <span class="conf">
            <span class="bar"><span style="width:${pct}%"></span></span>
            <span>${f.confidence.toFixed(2)}</span>
          </span>
          <span>head: ${esc(state.diffRange)}</span>
          <span class="st st-${f.status}">${f.status}</span>
        </div>
      </div>
      <div class="detail-body">
        <p>${esc(f.message)}</p>
        <div class="callout">
          <div class="ch">Why Verdict flagged this</div>
          <div>${esc(hint)}</div>
        </div>
      </div>
      <div class="location">
        <span class="key">Location</span>
        <span>${esc(f.file)}:<span class="ln">${f.line}</span></span>
      </div>
      <div class="actions">
        <button class="btn secondary" data-act="goto">Go To Location</button>
        <button class="btn secondary" data-act="dismiss">${isIgnored ? 'Un-dismiss' : 'Dismiss'}</button>
        <button class="btn primary" data-act="fix">✨ Fix with Bob</button>
        <button class="btn secondary" data-act="resolve">${isResolved ? 'Reopen' : '✓ Mark as Resolved'}</button>
      </div>
    `;
  }

  function renderStatusBar() {
    if (!state.hasReport) {
      return `<div class="statusbar">
        <span class="v-tag PASS">—</span>
        <span class="sep">·</span>
        <span>No report</span>
        <span class="range">${esc(state.diffRange)}</span>
      </div>`;
    }
    const v = state.effectiveVerdict;
    const t = state.totals;
    return `
      <div class="statusbar">
        <span>Verdict</span>
        <span class="v-tag ${v}">${v}</span>
        <span class="sep">·</span>
        <span>${t.total} total</span>
        <span class="sep">·</span>
        <span>${t.open} open</span>
        <span class="sep">·</span>
        <span>${t.ignored} ignored</span>
        <span class="sep">·</span>
        <span>${t.resolved} resolved</span>
        <span class="range">${esc(state.diffRange)}</span>
      </div>
    `;
  }

  /* ─── wiring ─────────────────────────────────────────────── */

  function wireToolbar() {
    const search$ = root.querySelector('#search');
    if (search$) {
      search$.addEventListener('input', (e) => {
        search = e.target.value;
        render();
        const refocus = root.querySelector('#search');
        if (refocus) {
          refocus.focus();
          refocus.setSelectionRange(refocus.value.length, refocus.value.length);
        }
      });
    }
    const clear$ = root.querySelector('#clear-search');
    if (clear$) clear$.addEventListener('click', () => { search = ''; render(); });

    root.querySelectorAll('.dd').forEach((el) => {
      el.addEventListener('click', (e) => {
        const kind = el.getAttribute('data-dd');
        openDropdown(kind, el);
        e.stopPropagation();
      });
    });
  }

  function wireList() {
    root.querySelectorAll('.group-head').forEach((el) => {
      el.addEventListener('click', () => {
        const key = el.getAttribute('data-key');
        if (collapsed.has(key)) collapsed.delete(key); else collapsed.add(key);
        render();
      });
    });
    root.querySelectorAll('.row').forEach((el) => {
      el.addEventListener('click', () => {
        selectedId = el.getAttribute('data-id');
        render();
      });
    });
  }

  function wireDetail() {
    root.querySelectorAll('.actions .btn').forEach((b) => {
      b.addEventListener('click', () => {
        const act = b.getAttribute('data-act');
        const f = state.findings.find((x) => x.id === selectedId);
        if (!f) return;
        if (act === 'goto') {
          send({ type: 'goto', file: f.file, line: f.line });
        } else if (act === 'dismiss') {
          const next = f.status === 'ignored' ? 'open' : 'ignored';
          send({ type: 'setStatus', id: f.id, status: next });
        } else if (act === 'resolve') {
          const next = f.status === 'resolved' ? 'open' : 'resolved';
          send({ type: 'setStatus', id: f.id, status: next });
        } else if (act === 'fix') {
          send({ type: 'fixWithBob', id: f.id });
        }
      });
    });
  }

  /* ─── dropdowns ──────────────────────────────────────────── */

  let openPop = null;
  function closePop() {
    if (openPop && openPop.parentNode) openPop.parentNode.removeChild(openPop);
    openPop = null;
  }
  document.addEventListener('click', () => closePop());

  function openDropdown(kind, anchor) {
    closePop();
    let opts;
    let current;
    let onPick;
    if (kind === 'head') {
      opts = HEAD_PRESETS.map((p) => ({ value: p.value, label: p.value, desc: p.desc }));
      opts.push({ value: '__custom', label: 'Custom…', desc: 'Type any git diff range' });
      current = state.diffRange;
      onPick = (v) => {
        if (v === '__custom') {
          send({ type: 'pickCustomDiffRange' });
        } else {
          send({ type: 'setDiffRange', range: v });
        }
      };
    } else if (kind === 'group') {
      opts = GROUP_OPTS.map((o) => ({ value: o.value, label: o.label }));
      current = groupBy;
      onPick = (v) => send({ type: 'setGroupBy', value: v });
    } else {
      opts = SORT_OPTS.map((o) => ({ value: o.value, label: o.label }));
      current = sortBy;
      onPick = (v) => send({ type: 'setSortBy', value: v });
    }
    const pop = document.createElement('div');
    pop.className = 'dd-popover';
    pop.innerHTML = opts.map((o) => `
      <div class="opt ${o.value === current ? 'active' : ''}" data-v="${esc(o.value)}">
        <span class="v">${esc(o.label)}</span>
        ${o.desc ? `<span class="d">${esc(o.desc)}</span>` : ''}
      </div>
    `).join('');
    pop.addEventListener('click', (e) => e.stopPropagation());
    pop.querySelectorAll('.opt').forEach((el) => {
      el.addEventListener('click', () => {
        const v = el.getAttribute('data-v');
        closePop();
        onPick(v);
      });
    });
    document.body.appendChild(pop);
    const r = anchor.getBoundingClientRect();
    pop.style.left = `${Math.max(4, r.left)}px`;
    pop.style.top = `${r.bottom + 4}px`;
    openPop = pop;
  }

  /* ─── messaging ──────────────────────────────────────────── */

  window.addEventListener('message', (e) => {
    const msg = e.data;
    if (!msg) return;
    if (msg.type === 'state') {
      state = msg.state;
      kindMeta = msg.kindMeta;
      kindOrder = msg.kindOrder;
      groupBy = msg.groupBy || 'type';
      sortBy = msg.sortBy || 'severity';
      if (selectedId && !state.findings.find((f) => f.id === selectedId)) {
        selectedId = null;
      }
      render();
    }
  });

  send({ type: 'ready' });
})();
