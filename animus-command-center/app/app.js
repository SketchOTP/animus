(function () {
  'use strict';

  var SECTIONS = [
    { id: 'overview', label: 'Overview', icon: 'overview' },
    { id: 'projects', label: 'Projects', icon: 'projects' },
    { id: 'goals', label: 'Goals', icon: 'goals' },
    { id: 'runs', label: 'Runs', icon: 'runs' },
    { id: 'driver', label: 'Driver', icon: 'driver' },
    { id: 'release', label: 'Release', icon: 'release' }
  ];

  var state = {
    section: 'overview',
    connected: false,
    projects: [],
    goals: [],
    runs: [],
    driver: null,
    meta: null
  };

  function $(id) {
    return document.getElementById(id);
  }

  function escapeHtml(text) {
    return String(text == null ? '' : text)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function statusClass(status) {
    var s = String(status || '').toLowerCase();
    if (/complete|approved|idle|running_ok|ok/.test(s)) return 'cc-status-ok';
    if (/pending|await|review|draft/.test(s)) return 'cc-status-warn';
    if (/block|fail|halt|error/.test(s)) return 'cc-status-bad';
    return '';
  }

  async function govFetch(path) {
    var resp = await fetch('/api/governance/' + String(path).replace(/^\//, ''), {
      headers: { Accept: 'application/json' }
    });
    if (!resp.ok) {
      var detail = resp.statusText;
      try {
        var body = await resp.json();
        detail = body.detail || body.error || detail;
      } catch (_e) { /* ignore */ }
      throw new Error(String(detail || 'governance_fetch_failed'));
    }
    return resp.json();
  }

  function setConnection(ok, detail) {
    state.connected = ok;
    var pill = $('ccConnectionPill');
    if (!pill) return;
    pill.textContent = ok ? 'Live' : 'Offline';
    pill.className = 'cc-pill ' + (ok ? 'cc-pill-ok' : 'cc-pill-warn');
    pill.title = ok ? 'Governance API connected' : (detail || 'API unreachable');
  }

  function buildNav() {
    var nav = $('ccNav');
    if (!nav) return;
    nav.innerHTML = SECTIONS.map(function (sec) {
      var active = sec.id === state.section ? ' cc-nav-active' : '';
      return (
        '<button type="button" class="cc-nav-btn' + active + '" data-section="' + sec.id + '" ' +
        'title="' + escapeHtml(sec.label) + '" aria-label="' + escapeHtml(sec.label) + '" role="tab">' +
        CCIcons.icon(sec.icon) + '</button>'
      );
    }).join('');
    nav.querySelectorAll('[data-section]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        switchSection(btn.getAttribute('data-section'));
      });
    });
  }

  function switchSection(sectionId) {
    state.section = sectionId;
    var title = SECTIONS.find(function (s) { return s.id === sectionId; });
    $('ccSectionTitle').textContent = title ? title.label : 'Overview';
    document.querySelectorAll('.cc-panel').forEach(function (panel) {
      var active = panel.getAttribute('data-section') === sectionId;
      panel.hidden = !active;
      panel.classList.toggle('cc-panel-active', active);
    });
    document.querySelectorAll('.cc-nav-btn').forEach(function (btn) {
      btn.classList.toggle('cc-nav-active', btn.getAttribute('data-section') === sectionId);
    });
  }

  function renderStats() {
    var grid = $('ccStatGrid');
    if (!grid) return;
    var goalCount = state.goals.length;
    var runCount = state.runs.length;
    var projectCount = state.projects.length;
    var driverState = state.driver && state.driver.state ? state.driver.state : 'unknown';
    var pending = state.goals.filter(function (g) {
      return /pending_completion|awaiting|blocked/.test(String(g.status || ''));
    }).length;
    var stats = [
      { icon: 'projects', label: 'Projects', value: projectCount },
      { icon: 'goals', label: 'Goals', value: goalCount },
      { icon: 'runs', label: 'Runs', value: runCount },
      { icon: 'driver', label: 'Driver', value: driverState.replace(/_/g, ' ') }
    ];
    if (pending) stats.push({ icon: 'release', label: 'Needs you', value: pending });
    grid.innerHTML = stats.map(function (stat) {
      return (
        '<article class="cc-stat-card">' +
        '<div class="cc-stat-icon">' + CCIcons.icon(stat.icon) + '</div>' +
        '<div class="cc-stat-value">' + escapeHtml(stat.value) + '</div>' +
        '<div class="cc-stat-label">' + escapeHtml(stat.label) + '</div>' +
        '</article>'
      );
    }).join('');
  }

  function renderCharts() {
    var runCounts = state.runs.slice(0, 12).map(function (_r, i) {
      return Math.max(1, (i % 5) + 1 + (state.runs.length > 3 ? 1 : 0));
    });
    if (!runCounts.length) runCounts = [2, 4, 3, 6, 5, 7, 4, 8, 6, 9, 7, 10];
    CCCharts.drawSparkline($('ccActivityChart'), runCounts);

    var ok = state.runs.filter(function (r) { return /complete|approved/.test(String(r.status || '')); }).length;
    var warn = state.goals.filter(function (g) { return /pending|await/.test(String(g.status || '')); }).length;
    var bad = state.goals.filter(function (g) { return /block|fail/.test(String(g.status || '')); }).length;
    var idle = Math.max(0, state.projects.length - ok - warn - bad);
    CCCharts.drawDonut($('ccHealthDonut'), [
      { value: ok || 1, color: '#34c759' },
      { value: warn, color: '#ff9f0a' },
      { value: bad, color: '#ff3b30' },
      { value: idle, color: 'rgba(110,110,115,0.25)' }
    ]);
    var legend = $('ccHealthLegend');
    if (legend) {
      legend.innerHTML = [
        { label: 'Healthy', color: '#34c759', n: ok },
        { label: 'Pending', color: '#ff9f0a', n: warn },
        { label: 'Blocked', color: '#ff3b30', n: bad }
      ].map(function (item) {
        return '<li><span class="cc-legend-dot" style="background:' + item.color + '"></span>' +
          escapeHtml(item.label) + ' · ' + item.n + '</li>';
      }).join('');
    }
  }

  function renderProjects() {
    var grid = $('ccProjectGrid');
    if (!grid) return;
    if (!state.projects.length) {
      grid.innerHTML = '<div class="cc-empty">No projects — start governance-api or check registry.</div>';
      return;
    }
    grid.innerHTML = state.projects.map(function (p) {
      var repos = (p.repos && p.repos.length) || p.repo_count || 0;
      return (
        '<article class="cc-project-card">' +
        '<div class="cc-project-head">' +
        '<div class="cc-project-avatar">' + CCIcons.icon('folder') + '</div>' +
        '<div><div class="cc-project-name">' + escapeHtml(p.display_name || p.slug || p.project_id) + '</div>' +
        '<div class="cc-project-slug">' + escapeHtml(p.slug || '') + '</div></div></div>' +
        '<div class="cc-chip-row">' +
        '<span class="cc-chip">' + repos + ' repos</span>' +
        '<span class="cc-chip">' + escapeHtml(p.status || 'active') + '</span>' +
        '</div></article>'
      );
    }).join('');
  }

  function renderGoals() {
    var host = $('ccGoalBars');
    if (!host) return;
    if (!state.goals.length) {
      host.innerHTML = '<div class="cc-empty">No goals in projection store.</div>';
      return;
    }
    host.innerHTML = state.goals.slice(0, 20).map(function (g) {
      var pct = Math.min(100, Math.max(8, Number(g.progress_pct || 35)));
      return (
        '<div class="cc-goal-row">' +
        '<div><strong>' + escapeHtml((g.title || g.goal_id || '').slice(0, 28)) + '</strong>' +
        '<div class="cc-project-slug">' + escapeHtml(g.status || '—') + '</div></div>' +
        '<div class="cc-goal-bar-track"><div class="cc-goal-bar-fill" style="width:' + pct + '%"></div></div>' +
        '<div class="' + statusClass(g.status) + '">' + escapeHtml(g.status || '—') + '</div>' +
        '</div>'
      );
    }).join('');
  }

  function renderRuns() {
    var host = $('ccRunTimeline');
    if (!host) return;
    if (!state.runs.length) {
      host.innerHTML = '<div class="cc-empty">No runs recorded yet.</div>';
      return;
    }
    host.innerHTML = state.runs.slice(0, 16).map(function (r) {
      var pct = Math.min(100, Math.max(12, Number(r.progress_pct || 50)));
      var color = /complete|approved/.test(String(r.status || '')) ? '#34c759'
        : /block|fail/.test(String(r.status || '')) ? '#ff3b30' : '#0071e3';
      return (
        '<div class="cc-run-row">' +
        '<div class="cc-project-slug">' + escapeHtml((r.run_id || '').slice(0, 10)) + '</div>' +
        '<div class="cc-run-bar"><span style="width:' + pct + '%;background:' + color + '"></span></div>' +
        '<div class="' + statusClass(r.status) + '">' + escapeHtml(r.status || '—') + '</div>' +
        '</div>'
      );
    }).join('');
  }

  function renderDriver() {
    var d = state.driver || {};
    var stateName = d.state || d.status || 'unknown';
    $('ccDriverStateLabel').textContent = stateName.replace(/_/g, ' ');
    var pct = /running|active/.test(stateName) ? 0.75 : /idle|paused/.test(stateName) ? 0.35 : 0.15;
    var color = /running/.test(stateName) ? '#34c759' : /halt|stop|block/.test(stateName) ? '#ff3b30' : '#0071e3';
    CCCharts.drawRing($('ccDriverRing'), pct, color, Math.round(pct * 100) + '%');

    var controls = [
      { icon: 'driver', label: 'Start', key: 'start' },
      { icon: 'pause', label: 'Pause', key: 'pause' },
      { icon: 'resume', label: 'Resume', key: 'resume' },
      { icon: 'halt', label: 'Halt', key: 'halt' }
    ];
    $('ccDriverControls').innerHTML = controls.map(function (c) {
      return (
        '<button type="button" class="cc-control-btn" disabled title="Read-only shell v1">' +
        CCIcons.icon(c.icon) + '<span>' + escapeHtml(c.label) + '</span></button>'
      );
    }).join('');

    var meta = [
      ['Active goal', d.active_goal_id || '—'],
      ['Run', d.run_id || '—'],
      ['Stop reason', d.stop_reason || '—'],
      ['Budget', d.budget_hint || '—']
    ];
    $('ccDriverMeta').innerHTML = meta.map(function (row) {
      return '<div><dt>' + escapeHtml(row[0]) + '</dt><dd>' + escapeHtml(row[1]) + '</dd></div>';
    }).join('');
  }

  function renderRelease() {
    var host = $('ccReleaseGrid');
    if (!host) return;
    var gates = [
      { label: 'Plan', ok: state.connected },
      { label: 'Diff', ok: state.runs.some(function (r) { return /approved|complete/.test(String(r.status || '')); }) },
      { label: 'Verify', ok: state.runs.length > 0 },
      { label: 'Release', ok: state.goals.some(function (g) { return /complete|approved/.test(String(g.status || '')); }) }
    ];
    host.innerHTML = gates.map(function (g) {
      var cls = g.ok ? 'cc-status-ok' : 'cc-status-warn';
      var sym = g.ok ? '✓' : '…';
      var bg = g.ok ? 'rgba(52,199,89,0.15)' : 'rgba(255,159,10,0.12)';
      return (
        '<article class="cc-release-card">' +
        '<div class="cc-release-ring ' + cls + '" style="background:' + bg + '">' + sym + '</div>' +
        '<strong>' + escapeHtml(g.label) + '</strong>' +
        '<div class="cc-project-slug">' + (g.ok ? 'Ready' : 'Awaiting data') + '</div>' +
        '</article>'
      );
    }).join('');
  }

  function renderAll() {
    renderStats();
    renderCharts();
    renderProjects();
    renderGoals();
    renderRuns();
    renderDriver();
    renderRelease();
  }

  async function refreshData() {
    var shell = $('ccShell');
    if (shell) shell.classList.add('cc-loading');
    try {
      var projectsPayload = await govFetch('projects');
      state.projects = projectsPayload.projects || [];
      var goalsPayload = await govFetch('goals');
      state.goals = goalsPayload.goals || [];
      var runsPayload = await govFetch('runs?limit=24');
      state.runs = runsPayload.runs || [];
      state.driver = await govFetch('driver/status');
      try { state.meta = await govFetch('meta'); } catch (_m) { state.meta = null; }
      setConnection(true);
    } catch (err) {
      state.projects = [];
      state.goals = [];
      state.runs = [];
      state.driver = null;
      setConnection(false, err.message);
    } finally {
      if (shell) shell.classList.remove('cc-loading');
      renderAll();
    }
  }

  function init() {
    CCIcons.mount($('ccRefreshIcon'), 'refresh');
    CCIcons.mount($('ccActivityIcon'), 'activity');
    CCIcons.mount($('ccStatusIcon'), 'health');
    buildNav();
    switchSection('overview');
    $('ccRefreshBtn').addEventListener('click', refreshData);
    refreshData();
    setInterval(refreshData, 30000);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
