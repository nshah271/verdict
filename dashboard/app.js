/* verdict analytics dashboard
 *
 * Loads data/index.json + data/<sha>.json, renders the dashboard,
 * and reactively re-aggregates everything when the fixture / test /
 * prod filter chips change.
 *
 * Architecture:
 *   - module-scoped `state` holds the raw data + current filters
 *     + cached Chart.js instances.
 *   - applyFilters() returns the filtered per-commit view, with each
 *     commit's verdict recomputed against the filtered findings.
 *   - rerender() runs after any filter change: updates both Chart.js
 *     instances in place (no destroy/recreate) and rebuilds the two
 *     leaderboard tables and the SVG timeline.
 *   - clicking a timeline dot opens the drilldown <aside> with that
 *     commit's full filtered findings list; GitHub deep links go
 *     wherever a sha+file is known and index.repo is set.
 */

(() => {
  "use strict";

  const css = (name) =>
    getComputedStyle(document.documentElement).getPropertyValue(name).trim();

  const COLORS = {
    PASS: css("--pass"),
    SUSPICIOUS: css("--suspicious"),
    LIED: css("--lied"),
    PASS_DIM: css("--pass-dim"),
    SUSPICIOUS_DIM: css("--suspicious-dim"),
    LIED_DIM: css("--lied-dim"),
    text: css("--text"),
    muted: css("--muted"),
    border: css("--border"),
    accent: css("--accent"),
    surface: css("--surface"),
  };

  const VERDICTS = ["PASS", "SUSPICIOUS", "LIED"];
  const CATEGORIES = ["prod", "test", "fixture"];

  const state = {
    index: null,
    scorecards: {}, // sha -> scorecard
    repoSlug: null,
    filters: { prod: true, test: true, fixture: true },
    charts: { donut: null, kindBar: null },
  };

  const $ = (id) => document.getElementById(id);

  const showError = (msg) => {
    const banner = $("error-banner");
    banner.hidden = false;
    banner.textContent = msg;
  };

  // ------------------------------------------------------------------
  // data loading
  // ------------------------------------------------------------------

  async function loadIndex() {
    const resp = await fetch("data/index.json");
    if (!resp.ok) {
      throw new Error(
        `failed to fetch data/index.json (status ${resp.status}). ` +
          `run \`verdict dashboard\` from the verdict repo root.`,
      );
    }
    return resp.json();
  }

  async function loadAllScorecards(index) {
    const fetches = index.commits.map(async (c) => {
      try {
        const r = await fetch(`data/${c.scorecard_file}`);
        return [c.sha, r.ok ? await r.json() : null];
      } catch {
        return [c.sha, null];
      }
    });
    return Object.fromEntries(await Promise.all(fetches));
  }

  // ------------------------------------------------------------------
  // categorization + filtering
  // ------------------------------------------------------------------

  function categorize(filePath) {
    if (!filePath) return "prod";
    if (filePath.includes("tests/fixtures/")) return "fixture";
    if (filePath.startsWith("tests/")) return "test";
    return "prod";
  }

  function recomputeVerdict(findings) {
    if (findings.length === 0) return "PASS";
    if (findings.some((f) => f.confidence > 0.8)) return "LIED";
    return "SUSPICIOUS";
  }

  function applyFilters() {
    const commits = state.index.commits.map((c) => {
      const sc = state.scorecards[c.sha];
      const findings = (sc?.findings || []).filter(
        (f) => state.filters[categorize(f.file)],
      );
      // scorecards are already confidence-desc sorted; first remains worst
      const top = findings[0] || null;
      return {
        ...c,
        findings,
        verdict: recomputeVerdict(findings),
        total_findings: findings.length,
        top_finding: top
          ? {
              kind: top.kind,
              message: top.message,
              confidence: top.confidence,
              file: top.file,
              line: top.line,
            }
          : null,
      };
    });
    const allFindings = commits.flatMap((c) => c.findings);
    return { commits, allFindings };
  }

  function categoryCounts() {
    const counts = { prod: 0, test: 0, fixture: 0 };
    for (const sc of Object.values(state.scorecards)) {
      for (const f of sc?.findings || []) {
        counts[categorize(f.file)]++;
      }
    }
    return counts;
  }

  // ------------------------------------------------------------------
  // github deep links
  // ------------------------------------------------------------------

  function commitUrl(sha) {
    if (!state.repoSlug) return null;
    return `https://github.com/${state.repoSlug}/commit/${sha}`;
  }

  function fileUrl(sha, path, line) {
    if (!state.repoSlug || !path) return null;
    const frag = line ? `#L${line}` : "";
    return `https://github.com/${state.repoSlug}/blob/${sha}/${path}${frag}`;
  }

  // ------------------------------------------------------------------
  // widget: trust panel
  // ------------------------------------------------------------------

  function initTrustPanel() {
    state.charts.donut = new Chart($("verdict-donut"), {
      type: "doughnut",
      data: {
        labels: VERDICTS,
        datasets: [
          {
            data: [0, 0, 0],
            backgroundColor: VERDICTS.map((v) => COLORS[v]),
            borderColor: COLORS.surface,
            borderWidth: 3,
            hoverOffset: 6,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        cutout: "62%",
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => {
                const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                const pct = total ? ((ctx.parsed / total) * 100).toFixed(0) : 0;
                return ` ${ctx.label}: ${ctx.parsed} commits (${pct}%)`;
              },
            },
          },
        },
      },
    });
  }

  function countByVerdict(commits) {
    const counts = { PASS: 0, SUSPICIOUS: 0, LIED: 0 };
    for (const c of commits) if (c.verdict in counts) counts[c.verdict]++;
    return counts;
  }

  function updateTrustPanel(commits, allFindings) {
    $("total-findings").textContent = allFindings.length.toLocaleString();
    $("total-commits").textContent = commits.length.toString();

    const counts = countByVerdict(commits);
    const chart = state.charts.donut;
    chart.data.datasets[0].data = VERDICTS.map((v) => counts[v]);
    chart.update();

    const legend = $("donut-legend");
    legend.innerHTML = "";
    for (const v of VERDICTS) {
      const item = document.createElement("span");
      item.innerHTML =
        `<span class="swatch" style="background:${COLORS[v]}"></span>` +
        `${v} ${counts[v]}`;
      legend.appendChild(item);
    }
  }

  // ------------------------------------------------------------------
  // widget: lie type bar chart
  // ------------------------------------------------------------------

  function initKindBar() {
    state.charts.kindBar = new Chart($("kind-bar"), {
      type: "bar",
      data: {
        labels: [],
        datasets: [
          {
            data: [],
            backgroundColor: COLORS.accent,
            borderColor: COLORS.accent,
            borderWidth: 0,
            borderRadius: 4,
          },
        ],
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: { label: (ctx) => ` ${ctx.parsed.x} findings` },
          },
        },
        scales: {
          x: {
            beginAtZero: true,
            grid: { color: COLORS.border, drawBorder: false },
            ticks: { color: COLORS.muted, precision: 0 },
          },
          y: {
            grid: { display: false, drawBorder: false },
            ticks: {
              color: COLORS.text,
              font: { family: "ui-monospace, Menlo, monospace", size: 13 },
            },
          },
        },
      },
    });
  }

  function updateKindBar(allFindings) {
    const counts = new Map();
    for (const f of allFindings) {
      counts.set(f.kind, (counts.get(f.kind) || 0) + 1);
    }
    const rows = [...counts.entries()].sort((a, b) => b[1] - a[1]);

    const canvas = $("kind-bar");
    canvas.parentElement.style.height =
      Math.max(120, rows.length * 32 + 40) + "px";

    const chart = state.charts.kindBar;
    chart.data.labels = rows.map(([k]) => k);
    chart.data.datasets[0].data = rows.map(([, n]) => n);
    chart.update();
  }

  // ------------------------------------------------------------------
  // widget: per-check leaderboard
  // ------------------------------------------------------------------

  function updateCheckBoard(allFindings) {
    const groups = new Map();
    for (const f of allFindings) {
      if (!groups.has(f.kind)) groups.set(f.kind, []);
      groups.get(f.kind).push(f);
    }
    const rows = [...groups.entries()]
      .map(([kind, fs]) => {
        const confs = fs.map((f) => f.confidence);
        const avg = confs.reduce((a, b) => a + b, 0) / confs.length;
        const max = Math.max(...confs);
        return { kind, fires: fs.length, avg, max };
      })
      .sort((a, b) => b.fires - a.fires);

    const tbody = $("check-board").querySelector("tbody");
    tbody.innerHTML = "";
    if (rows.length === 0) {
      tbody.innerHTML =
        `<tr><td colspan="4" class="muted">no findings under current filters.</td></tr>`;
      return;
    }
    for (const r of rows) {
      const tr = document.createElement("tr");
      tr.innerHTML =
        `<td class="kind-name">${escapeHtml(r.kind)}</td>` +
        `<td class="num">${r.fires}</td>` +
        `<td class="num">${r.avg.toFixed(2)}</td>` +
        `<td class="num">${r.max.toFixed(2)}</td>`;
      tbody.appendChild(tr);
    }
  }

  // ------------------------------------------------------------------
  // widget: file leaderboard
  // ------------------------------------------------------------------

  function updateFileBoard(allFindings) {
    const groups = new Map();
    for (const f of allFindings) {
      const key = f.file || "(unknown)";
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(f);
    }
    const rows = [...groups.entries()]
      .map(([path, fs]) => ({
        path,
        fires: fs.length,
        maxConf: Math.max(...fs.map((f) => f.confidence)),
        line: fs[0].line,
      }))
      .sort((a, b) => b.fires - a.fires)
      .slice(0, 10);

    // Link file paths to the newest commit's blob so the line numbers
    // are usually still accurate.
    const newestSha = state.index.commits[state.index.commits.length - 1]?.sha;

    const tbody = $("file-board").querySelector("tbody");
    tbody.innerHTML = "";
    if (rows.length === 0) {
      tbody.innerHTML =
        `<tr><td colspan="3" class="muted">no findings under current filters.</td></tr>`;
      return;
    }
    for (const r of rows) {
      const url = fileUrl(newestSha, r.path, r.line);
      const pathHtml = url
        ? `<a href="${url}" target="_blank" rel="noopener">${escapeHtml(r.path)}</a>`
        : escapeHtml(r.path);
      const tr = document.createElement("tr");
      tr.innerHTML =
        `<td class="file-path">${pathHtml}</td>` +
        `<td class="num">${r.fires}</td>` +
        `<td class="num">${r.maxConf.toFixed(2)}</td>`;
      tbody.appendChild(tr);
    }
  }

  // ------------------------------------------------------------------
  // widget: commit timeline (hand-rolled SVG)
  // ------------------------------------------------------------------

  const SVG_NS = "http://www.w3.org/2000/svg";

  function makeSvgEl(tag, attrs) {
    const el = document.createElementNS(SVG_NS, tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      el.setAttribute(k, v);
    }
    return el;
  }

  let timelineResizeObserver = null;

  function renderTimeline(commits) {
    const svg = $("timeline");
    const wrap = $("timeline-wrap");
    const tooltip = $("timeline-tooltip");

    function draw() {
      const width = wrap.clientWidth || 800;
      const height = 140;
      const padX = 48;
      const padY = 24;

      svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
      svg.setAttribute("width", width);
      svg.setAttribute("height", height);
      while (svg.firstChild) svg.removeChild(svg.firstChild);
      if (commits.length === 0) return;

      const times = commits.map((c) => Date.parse(c.timestamp));
      const tMin = Math.min(...times);
      const tMax = Math.max(...times);
      const span = Math.max(tMax - tMin, 1);

      const yFor = (v) =>
        v === "PASS"
          ? padY + 14
          : v === "LIED"
            ? height - padY - 14
            : height / 2;
      const xFor = (t) => padX + ((t - tMin) / span) * (width - 2 * padX);

      svg.appendChild(
        makeSvgEl("line", {
          class: "axis",
          x1: padX,
          x2: width - padX,
          y1: height / 2,
          y2: height / 2,
        }),
      );

      const first = commits[0];
      const last = commits[commits.length - 1];
      const firstLabel = makeSvgEl("text", {
        class: "end-label",
        x: padX,
        y: height - 6,
        "text-anchor": "start",
      });
      firstLabel.textContent = first.short_sha;
      svg.appendChild(firstLabel);

      const lastLabel = makeSvgEl("text", {
        class: "end-label",
        x: width - padX,
        y: height - 6,
        "text-anchor": "end",
      });
      lastLabel.textContent = last.short_sha;
      svg.appendChild(lastLabel);

      for (const c of commits) {
        const cx = xFor(Date.parse(c.timestamp));
        const cy = yFor(c.verdict);
        const fill = COLORS[c.verdict] || COLORS.muted;
        const stroke = COLORS[`${c.verdict}_DIM`] || COLORS.border;
        const dot = makeSvgEl("circle", {
          class: "dot",
          cx,
          cy,
          r: 7,
          fill,
          stroke,
          "stroke-width": 2,
        });
        dot.addEventListener("mouseenter", (e) => showTooltip(e, c));
        dot.addEventListener("mousemove", positionTooltip);
        dot.addEventListener("mouseleave", hideTooltip);
        dot.addEventListener("click", () => {
          hideTooltip();
          openDrilldown(c);
        });
        svg.appendChild(dot);
      }
    }

    function showTooltip(e, commit) {
      tooltip.hidden = false;
      tooltip.innerHTML = renderTooltipHtml(commit);
      positionTooltip(e);
    }
    function positionTooltip(e) {
      const rect = wrap.getBoundingClientRect();
      const x = e.clientX - rect.left + 12;
      const y = e.clientY - rect.top + 12;
      const ttW = tooltip.offsetWidth || 280;
      tooltip.style.left = Math.min(x, Math.max(0, rect.width - ttW - 8)) + "px";
      tooltip.style.top = y + "px";
    }
    function hideTooltip() {
      tooltip.hidden = true;
    }

    function renderTooltipHtml(c) {
      const date = new Date(c.timestamp).toLocaleString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
      const top = c.top_finding;
      const topHtml = top
        ? `<div class="tt-row"><strong>${escapeHtml(top.kind)}</strong> ` +
          `(${top.confidence.toFixed(2)})</div>` +
          `<div class="tt-row muted">${escapeHtml(truncate(top.message, 90))}</div>`
        : `<div class="tt-row muted">no findings.</div>`;
      const gh = commitUrl(c.sha);
      const ghHtml = gh
        ? `<a class="tt-link" href="${gh}" target="_blank" rel="noopener">` +
          `click dot to drill in &middot; open on github &rarr;</a>`
        : `<div class="tt-row muted">click dot to drill in.</div>`;
      return (
        `<div class="tt-sha">${escapeHtml(c.short_sha)} &middot; ` +
          `${escapeHtml(c.author)} &middot; ${escapeHtml(date)}</div>` +
        `<div class="tt-subject">${escapeHtml(truncate(c.subject, 80))}</div>` +
        `<div class="tt-row tt-verdict-${c.verdict}">` +
          `${c.verdict} &middot; ${c.total_findings} findings</div>` +
        topHtml +
        ghHtml
      );
    }

    draw();
    if (timelineResizeObserver) timelineResizeObserver.disconnect();
    timelineResizeObserver = new ResizeObserver(draw);
    timelineResizeObserver.observe(wrap);
  }

  // ------------------------------------------------------------------
  // drilldown side panel
  // ------------------------------------------------------------------

  function openDrilldown(commit) {
    const panel = $("drilldown");
    const backdrop = $("drilldown-backdrop");

    const shaA = $("dd-sha");
    const url = commitUrl(commit.sha);
    if (url) {
      shaA.href = url;
    } else {
      shaA.removeAttribute("href");
    }
    shaA.textContent = commit.short_sha;

    const verdictEl = $("dd-verdict");
    verdictEl.textContent = commit.verdict;
    verdictEl.className = `dd-verdict ${commit.verdict}`;

    $("dd-subject").textContent = commit.subject;
    const date = new Date(commit.timestamp).toLocaleString();
    $("dd-author").textContent = `${commit.author} · ${date}`;
    $("dd-summary").textContent =
      `${commit.total_findings} findings under current filters`;

    const list = $("dd-findings");
    list.innerHTML = "";
    if (commit.findings.length === 0) {
      list.innerHTML = `<li class="dd-empty">no findings under current filters.</li>`;
    } else {
      for (const f of commit.findings) {
        const li = document.createElement("li");
        const confClass =
          f.confidence > 0.8 ? "high" : f.confidence >= 0.5 ? "med" : "low";
        const fileLoc = f.file ? `${f.file}:${f.line}` : "(no location)";
        const fUrl = fileUrl(commit.sha, f.file, f.line);
        const fileHtml = fUrl
          ? `<a href="${fUrl}" target="_blank" rel="noopener">${escapeHtml(fileLoc)}</a>`
          : escapeHtml(fileLoc);
        li.innerHTML =
          `<div class="dd-finding-head">` +
            `<span class="dd-kind">${escapeHtml(f.kind)}</span>` +
            `<span class="dd-conf ${confClass}">conf ${f.confidence.toFixed(2)}</span>` +
          `</div>` +
          `<div class="dd-file">${fileHtml}</div>` +
          `<p class="dd-message">${escapeHtml(f.message)}</p>`;
        list.appendChild(li);
      }
    }

    panel.hidden = false;
    backdrop.hidden = false;
  }

  function closeDrilldown() {
    $("drilldown").hidden = true;
    $("drilldown-backdrop").hidden = true;
  }

  function wireDrilldownChrome() {
    $("dd-close").addEventListener("click", closeDrilldown);
    $("drilldown-backdrop").addEventListener("click", closeDrilldown);
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && !$("drilldown").hidden) closeDrilldown();
    });
  }

  // ------------------------------------------------------------------
  // filter chrome
  // ------------------------------------------------------------------

  function wireFilters() {
    const counts = categoryCounts();
    for (const cat of CATEGORIES) {
      $(`count-${cat}`).textContent = counts[cat].toLocaleString();
      const cb = $(`filter-${cat}`);
      cb.addEventListener("change", () => {
        state.filters[cat] = cb.checked;
        rerender();
      });
    }
  }

  // ------------------------------------------------------------------
  // top-level render
  // ------------------------------------------------------------------

  function rerender() {
    const { commits, allFindings } = applyFilters();
    updateTrustPanel(commits, allFindings);
    updateKindBar(allFindings);
    updateCheckBoard(allFindings);
    updateFileBoard(allFindings);
    renderTimeline(commits);
  }

  // ------------------------------------------------------------------
  // utilities
  // ------------------------------------------------------------------

  function truncate(s, n) {
    if (typeof s !== "string") return "";
    return s.length > n ? s.slice(0, n - 1) + "…" : s;
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    })[c]);
  }

  function renderMeta(index) {
    const repo = index.repo || "(unknown repo)";
    const branch = index.branch || "?";
    const when = index.generated_at
      ? new Date(index.generated_at).toLocaleString()
      : "?";
    const scope = index.static_only ? "static checks only" : "all checks";
    $("meta").textContent =
      `${repo} @ ${branch} | ${index.commits.length} commits | ${scope} | generated ${when}`;
  }

  // ------------------------------------------------------------------
  // boot
  // ------------------------------------------------------------------

  (async function main() {
    try {
      Chart.defaults.color = COLORS.text;
      Chart.defaults.font.family =
        "-apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif";

      const index = await loadIndex();
      if (!index.commits || index.commits.length === 0) {
        throw new Error("data/index.json contains no commits.");
      }

      state.index = index;
      state.repoSlug = index.repo || null;
      state.scorecards = await loadAllScorecards(index);

      renderMeta(index);
      initTrustPanel();
      initKindBar();
      wireDrilldownChrome();
      wireFilters();
      rerender();
    } catch (e) {
      console.error(e);
      showError(e.message || String(e));
    }
  })();
})();
