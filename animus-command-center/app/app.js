/* Dedicated Command Center shell (D-140) + governance API integration (D-141). */
var CCGoalRunnerHelpers = {
  ANIMA_LINUX_PROJECT_ID: 'c9eebdd2-a087-5eae-a074-77b5572fe7b5',
  GOAL_STATEMENT_MAX_LEN: 8000,
  TIMELINE_STATES: [
    'created',
    'preflight_running',
    'preflight_passed',
    'research_running',
    'research_completed',
    'decomposing',
    'breakdown_reviewed',
    'awaiting_approval',
    'approved',
    'driver_starting',
    'running',
    'entry_dispatched',
    'entry_verifying',
    'entry_gating',
    'entry_committing',
    'pending_completion',
    'completed',
    'blocked',
    'operator_required'
  ],
  validateGoalStatement: function (statement, projectId, alreadyRunning) {
    var text = String(statement || '').trim();
    if (!projectId) return { ok: false, error: 'Select a project before running a goal.' };
    if (!text) return { ok: false, error: 'Goal statement is required.' };
    if (text.length > CCGoalRunnerHelpers.GOAL_STATEMENT_MAX_LEN) {
      return {
        ok: false,
        error: 'Goal statement exceeds maximum length (' + CCGoalRunnerHelpers.GOAL_STATEMENT_MAX_LEN + ').'
      };
    }
    if (alreadyRunning) return { ok: false, error: 'A goal run is already in progress.' };
    return { ok: true, statement: text };
  },
  buildGoalRunPayload: function (form, profile) {
    var runMode = form.runMode || 'draft_only';
    var researchMode = form.researchMode || (profile && profile.research_mode) || 'light';
    var approvalMode = form.approvalMode || (profile && profile.approval_mode) || 'manual_approval';
    var budgetDefaults =
      profile && profile.budget_defaults && typeof profile.budget_defaults === 'object'
        ? profile.budget_defaults
        : {};
    var maxRunCount = form.maxRunCount != null && form.maxRunCount !== ''
      ? Number(form.maxRunCount)
      : budgetDefaults.max_run_count;
    var maxWallHours = form.maxWallHours != null && form.maxWallHours !== ''
      ? Number(form.maxWallHours)
      : budgetDefaults.max_wall_clock_hours;
    return {
      statement: String(form.statement || '').trim(),
      run_mode: runMode,
      goal_size_hint: form.goalSizeHint || 'S',
      research_mode: researchMode,
      approval_mode: approvalMode,
      budget_override: {
        max_run_count: maxRunCount,
        max_wall_clock_hours: maxWallHours
      }
    };
  },
  goalRunPostPath: function (projectId) {
    return 'projects/' + encodeURIComponent(projectId) + '/goal-runs';
  },
  shouldShowResearchRequiredWarning: function (profile, researchMode) {
    return !!(profile && profile.research_required && String(researchMode || '') === 'off');
  },
  shouldShowAutoRunWarning: function (approvalMode) {
    return String(approvalMode || '') === 'auto_run_if_policy_clean';
  },
  shouldShowRunModeWarning: function (runMode) {
    return String(runMode || '') === 'run';
  },
  mapTimelineIndex: function (state, response) {
    var normalized = String(state || '').trim();
    if (normalized === 'pending_approval') {
      return CCGoalRunnerHelpers.TIMELINE_STATES.indexOf('awaiting_approval');
    }
    var idx = CCGoalRunnerHelpers.TIMELINE_STATES.indexOf(normalized);
    if (idx >= 0) return idx;
    var events = Array.isArray(response && response.events_published) ? response.events_published : [];
    if (events.indexOf('governance.goal_run.preflight.completed') >= 0) {
      return CCGoalRunnerHelpers.TIMELINE_STATES.indexOf('preflight_passed');
    }
    return 0;
  },
  buildTimelineHtml: function (state, response) {
    var activeIndex = CCGoalRunnerHelpers.mapTimelineIndex(state, response);
    return (
      '<ul class="cc-timeline-list">' +
      CCGoalRunnerHelpers.TIMELINE_STATES.map(function (item, index) {
        var cls = index <= activeIndex ? 'cc-timeline-active' : 'cc-timeline-pending';
        return '<li class="' + cls + '">' + item + '</li>';
      }).join('') +
      '</ul>'
    );
  },
  buildResearchPanelHtml: function (response, goalDetail) {
    var research = (response && response.research) || {};
    var goal = goalDetail || {};
    var status = research.status || goal.research_status || '—';
    var mode = research.mode || goal.research_mode || '—';
    var required = goal.research_required != null ? String(goal.research_required) : '—';
    var confidence = research.confidence || goal.research_confidence || '—';
    var strategy = research.recommended_strategy || goal.recommended_strategy || '—';
    var artifactRef = research.artifact_ref || goal.research_artifact_ref || '—';
    return (
      '<div class="cc-meta-line">research_status: ' + status + ' · mode: ' + mode + ' · required: ' + required + '</div>' +
      '<div class="cc-meta-line">confidence: ' + confidence + ' · strategy: ' + strategy + '</div>' +
      '<div class="cc-meta-line">artifact: ' + artifactRef + '</div>'
    );
  },
  buildBreakdownPanelHtml: function (response, queuePayload, profile) {
    var breakdown = (response && response.breakdown) || {};
    var queue = Array.isArray(queuePayload && queuePayload.queue_entries) ? queuePayload.queue_entries : [];
    var validator = (profile && profile.default_validator) || '—';
    var first = queue.length ? queue[0] : null;
    var allowed = first && first.allowed_files_hint_json
      ? first.allowed_files_hint_json
      : first && first.allowed_files_hint
        ? JSON.stringify(first.allowed_files_hint)
        : '—';
    return (
      '<div class="cc-meta-line">breakdown_version: ' + (breakdown.version || '—') +
      ' · status: ' + (breakdown.status || '—') +
      ' · queue entries: ' + (breakdown.queue_entry_count != null ? breakdown.queue_entry_count : queue.length) + '</div>' +
      '<div class="cc-meta-line">entry tier: ' + (first && first.tier ? first.tier : '—') +
      ' · validator: ' + validator + '</div>' +
      '<div class="cc-meta-line">allowed files: ' + allowed + '</div>'
    );
  },
  buildExecutionPanelHtml: function (response, driverPayload, runMode) {
    var driver = (response && response.driver) || {};
    var remote = driverPayload || {};
    var started = !!driver.started;
    var lines = [
      'driver status: ' + (remote.status || remote.state || 'idle'),
      'driver started: ' + (started ? 'yes' : 'no'),
      'active_goal_id: ' + (remote.active_goal_id || '—'),
      'run_id: ' + (driver.run_id || '—')
    ];
    if (runMode === 'draft_only' && !started) {
      lines.push('draft_only: Driver not started (expected)');
    }
    return lines.map(function (line) {
      return '<div class="cc-meta-line">' + line + '</div>';
    }).join('');
  },
  buildBlockerRecoveryPanelHtml: function (response, goalRunProjection) {
    var blockReason = (response && response.block_reason) || (goalRunProjection && goalRunProjection.block_reason);
    var state = String((response && response.status) || (goalRunProjection && goalRunProjection.state) || '');
    if (!blockReason && state !== 'blocked' && state !== 'operator_required') {
      return '<div class="cc-meta-line">No blocker detected.</div>';
    }
    var operatorRequired = state === 'operator_required';
    var guidance = operatorRequired ? 'Operator decision required.' : 'Recovery prepared automatically.';
    return (
      '<div class="cc-meta-line">blocker_class: ' + (blockReason || '—') + '</div>' +
      '<div class="cc-meta-line">operator_required: ' + String(operatorRequired) + '</div>' +
      '<div class="cc-meta-line">' + guidance + '</div>'
    );
  },
  buildMemoryPanelHtml: function (response) {
    var memory = (response && response.memory) || {};
    var mode = memory.mode || memory.memory_mode || 'advisory';
    return (
      '<div class="cc-meta-line">memory mode: ' + mode +
      ' · recall: ' + (memory.recall_status || 'skipped') +
      ' · record: ' + (memory.record_status || 'skipped') + '</div>' +
      '<div class="cc-meta-line">memory_refs: ' +
      (Array.isArray(memory.memory_refs) ? memory.memory_refs.join(', ') : '—') + '</div>' +
      '<div class="cc-meta-line"><strong>Mimir is advisory memory, not approval authority.</strong></div>'
    );
  },
  buildOutcomePanelHtml: function (response, goalDetail) {
    var status = String((response && response.status) || (goalDetail && goalDetail.status) || '');
    var displayStatus = status === 'pending_completion' ? 'Pending final review/sign-off' : status || '—';
    var evidence = Array.isArray(response && response.evidence_refs) ? response.evidence_refs : [];
    var evidenceLinks = evidence.length
      ? evidence.map(function (ref, i) {
          return '<a class="cc-evidence-link" href="' + String(ref) + '" target="_blank" rel="noopener">Evidence ' + (i + 1) + '</a>';
        }).join(' ')
      : '—';
    return (
      '<div class="cc-meta-line">status: ' + displayStatus +
      ' · goal_run_id: ' + ((response && response.goal_run_id) || '—') +
      ' · goal_id: ' + ((response && response.goal_id) || '—') + '</div>' +
      '<div class="cc-meta-line">evidence refs: ' + evidence.length + ' · ' + evidenceLinks + '</div>' +
      '<div class="cc-meta-line">No self-sign-off from Goal Runner.</div>'
    );
  },
  formatProjectOptionLabel: function (project) {
    var row = project || {};
    var name = row.name || row.display_name || row.slug || row.project_id || 'project';
    var dirty = row.dirty_tree && row.dirty_tree.blocking
      ? ' · dirty (blocking)'
      : row.dirty_tree && row.dirty_tree.blocking_reason
        ? ' · dirty: ' + row.dirty_tree.blocking_reason
        : '';
    return name + ' · ' + (row.project_id || '') + ' · ' + (row.repo_path || '') + dirty;
  },
  formatProjectRegistryMeta: function (profile) {
    var p = profile || {};
    var dirty = p.dirty_tree || {};
    var preflight = p.preflight_status || p.preflight || (dirty.blocking ? 'blocked' : '—');
    return [
      ['Repo path', p.repo_path || '—'],
      ['Profile status', p.status || p.profile_status || '—'],
      ['Default validator', p.default_validator || '—'],
      ['Research mode', p.research_mode || '—'],
      ['Memory mode', p.memory_mode || 'advisory'],
      ['Architect import', p.architect_import_status || '—'],
      ['Dirty tree', dirty.blocking ? 'blocking' : dirty.blocking_reason || 'clean'],
      ['Preflight', preflight]
    ];
  }
};

(function () {
  'use strict';

  var SECTIONS = [
    { id: 'overview', label: 'Overview', icon: 'overview' },
    { id: 'projects', label: 'Projects', icon: 'projects' },
    { id: 'goals', label: 'Goal Runner', icon: 'goals' },
    { id: 'runs', label: 'Runs', icon: 'runs' },
    { id: 'driver', label: 'Driver', icon: 'driver' },
    { id: 'release', label: 'Release', icon: 'release' }
  ];

  var state = {
    section: 'overview',
    connected: false,
    workspaceId: null,
    projects: [],
    projectDetails: {},
    goals: [],
    runs: [],
    driver: null,
    meta: null,
    goalRunner: {
      selectedProjectId: CCGoalRunnerHelpers.ANIMA_LINUX_PROJECT_ID,
      selectedProfile: null,
      lastResponse: null,
      running: false,
      wired: false
    }
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

  async function govFetch(path, options) {
    var opts = options || {};
    var resp = await fetch('/api/governance/' + String(path).replace(/^\//, ''), Object.assign({
      headers: { Accept: 'application/json' }
    }, opts));
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

  function resolveWorkspaceId() {
    if (state.workspaceId) return state.workspaceId;
    for (var i = 0; i < state.projects.length; i += 1) {
      if (state.projects[i] && state.projects[i].workspace_id) {
        state.workspaceId = state.projects[i].workspace_id;
        return state.workspaceId;
      }
    }
    return null;
  }

  function driverStatusPath() {
    var workspaceId = resolveWorkspaceId();
    return workspaceId
      ? 'driver/status?workspace_id=' + encodeURIComponent(workspaceId)
      : 'driver/status';
  }

  async function loadGoalsAndRunsAcrossProjects() {
    state.goals = [];
    state.runs = [];
    for (var i = 0; i < state.projects.length; i += 1) {
      var project = state.projects[i];
      var projectId = project && project.project_id;
      if (!projectId) continue;
      try {
        var goalsPayload = await govFetch(
          'goals?project_id=' + encodeURIComponent(projectId)
        );
        state.goals = state.goals.concat(goalsPayload.goals || []);
      } catch (_goalsErr) { /* per-project goals optional */ }
      try {
        var runsPayload = await govFetch(
          'runs?limit=24&project_id=' + encodeURIComponent(projectId)
        );
        state.runs = state.runs.concat(runsPayload.runs || []);
      } catch (_runsErr) { /* per-project runs optional */ }
    }
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
    if (sectionId === 'goals' && !state.goalRunner.wired) {
      void renderGoalRunnerForm();
    }
  }

  function renderStats() {
    var grid = $('ccStatGrid');
    if (!grid) return;
    var stats = [
      { icon: 'projects', label: 'Projects', value: state.projects.length },
      { icon: 'goals', label: 'Goals', value: state.goals.length },
      { icon: 'runs', label: 'Runs', value: state.runs.length },
      { icon: 'driver', label: 'Driver', value: ((state.driver && state.driver.state) || 'unknown').replace(/_/g, ' ') }
    ];
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

  function renderProjectCard(project, detail) {
    var p = detail || project || {};
    var name = p.display_name || p.name || p.slug || p.project_id || 'project';
    var metaRows = CCGoalRunnerHelpers.formatProjectRegistryMeta(p);
    return (
      '<article class="cc-project-card" data-project-id="' + escapeHtml(p.project_id || project.project_id || '') + '">' +
      '<div class="cc-project-head">' +
      '<div class="cc-project-avatar">' + CCIcons.icon('folder') + '</div>' +
      '<div><div class="cc-project-name">' + escapeHtml(name) + '</div>' +
      '<div class="cc-project-slug">' + escapeHtml(p.slug || '') + '</div></div></div>' +
      '<dl class="cc-project-meta">' +
      metaRows.map(function (row) {
        return '<div><dt>' + escapeHtml(row[0]) + '</dt><dd>' + escapeHtml(row[1]) + '</dd></div>';
      }).join('') +
      '</dl></article>'
    );
  }

  function renderProjects() {
    var grid = $('ccProjectGrid');
    var metaHost = $('ccProjectRegistryMeta');
    if (!grid) return;
    if (!state.projects.length) {
      grid.innerHTML = '<div class="cc-empty">No projects — start governance-api or check registry.</div>';
      if (metaHost) metaHost.textContent = '';
      return;
    }
    if (metaHost) {
      metaHost.textContent = state.projects.length + ' project(s) from GET /api/governance/projects';
    }
    grid.innerHTML = state.projects.map(function (project) {
      var detail = state.projectDetails[project.project_id] || project;
      return renderProjectCard(project, detail);
    }).join('');
  }

  async function loadProjectDetails() {
    state.projectDetails = {};
    await Promise.all(state.projects.map(async function (project) {
      if (!project.project_id) return;
      try {
        state.projectDetails[project.project_id] = await govFetch(
          'projects/' + encodeURIComponent(project.project_id)
        );
      } catch (_err) {
        state.projectDetails[project.project_id] = project;
      }
    }));
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
        '<button type="button" class="cc-control-btn" disabled title="Read-only shell v1 — Driver controls disabled in command center">' +
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

  function readGoalRunnerForm() {
    return {
      projectId: ($('ccGoalRunnerProject') || {}).value || '',
      statement: ($('ccGoalRunnerStatement') || {}).value || '',
      researchMode: ($('ccGoalRunnerResearchMode') || {}).value || 'light',
      runMode: ($('ccGoalRunnerRunMode') || {}).value || 'draft_only',
      approvalMode: ($('ccGoalRunnerApprovalMode') || {}).value || 'manual_approval',
      maxRunCount: ($('ccGoalRunnerMaxRuns') || {}).value || '',
      maxWallHours: ($('ccGoalRunnerMaxHours') || {}).value || '',
      goalSizeHint: 'S'
    };
  }

  function updateGoalRunnerWarnings() {
    var host = $('ccGoalRunnerWarnings');
    if (!host) return;
    var form = readGoalRunnerForm();
    var profile = state.goalRunner.selectedProfile;
    var warnings = [];
    if (CCGoalRunnerHelpers.shouldShowResearchRequiredWarning(profile, form.researchMode)) {
      warnings.push('Research is required for this project unless skip is policy-approved.');
    }
    if (CCGoalRunnerHelpers.shouldShowAutoRunWarning(form.approvalMode)) {
      warnings.push('Will start Driver if policy/preflight pass.');
    }
    if (CCGoalRunnerHelpers.shouldShowRunModeWarning(form.runMode)) {
      warnings.push('Full run mode may start Driver execution when policy allows.');
    }
    host.innerHTML = warnings.length
      ? warnings.map(function (line) {
          return '<div class="cc-meta-line cc-goal-runner-warning">' + escapeHtml(line) + '</div>';
        }).join('')
      : '';
  }

  async function loadGoalRunnerProjectProfile(projectId) {
    if (!projectId) return;
    state.goalRunner.selectedProjectId = projectId;
    var profile = await govFetch('projects/' + encodeURIComponent(projectId));
    state.goalRunner.selectedProfile = profile;
    state.projectDetails[projectId] = profile;
    var metaHost = $('ccGoalRunnerProjectMeta');
    if (metaHost) {
      metaHost.textContent =
        'Profile default research: ' + (profile.research_mode || '—') +
        ' · approval: ' + (profile.approval_mode || '—') +
        ' · validator: ' + (profile.default_validator || '—');
    }
    var researchSelect = $('ccGoalRunnerResearchMode');
    if (researchSelect && profile.research_mode) researchSelect.value = profile.research_mode;
    var approvalSelect = $('ccGoalRunnerApprovalMode');
    if (approvalSelect) approvalSelect.value = profile.approval_mode || 'manual_approval';
    var runModeSelect = $('ccGoalRunnerRunMode');
    if (runModeSelect) runModeSelect.value = 'draft_only';
    var maxRuns = $('ccGoalRunnerMaxRuns');
    if (maxRuns && profile.budget_defaults && profile.budget_defaults.max_run_count != null) {
      maxRuns.value = String(profile.budget_defaults.max_run_count);
    }
    var maxHours = $('ccGoalRunnerMaxHours');
    if (maxHours && profile.budget_defaults && profile.budget_defaults.max_wall_clock_hours != null) {
      maxHours.value = String(profile.budget_defaults.max_wall_clock_hours);
    }
    updateGoalRunnerWarnings();
  }

  async function renderGoalRunnerForm() {
    var controlsHost = $('ccGoalRunnerControls');
    if (!controlsHost) return;
    controlsHost.innerHTML = '<div class="cc-meta-line">Loading Goal Runner…</div>';
    try {
      if (!state.projects.length) {
        var data = await govFetch('projects');
        state.projects = data.projects || [];
      }
      var options = state.projects.map(function (project) {
        var selected = project.project_id === state.goalRunner.selectedProjectId ? ' selected' : '';
        return (
          '<option value="' + escapeHtml(project.project_id) + '"' + selected + '>' +
          escapeHtml(CCGoalRunnerHelpers.formatProjectOptionLabel(project)) +
          '</option>'
        );
      }).join('');
      controlsHost.innerHTML =
        '<article class="cc-card" id="ccGoalRunnerPanel">' +
        '<header class="cc-card-head"><span>' + CCIcons.icon('goals') + '</span><h2>Goal Runner</h2></header>' +
        '<label class="cc-form-label">Project<select data-goal-runner-field="project_id" id="ccGoalRunnerProject">' +
        options + '</select></label>' +
        '<div class="cc-meta-line" id="ccGoalRunnerProjectMeta"></div>' +
        '<label class="cc-form-label">Goal statement<textarea data-goal-runner-field="statement" id="ccGoalRunnerStatement" rows="4"></textarea></label>' +
        '<div class="cc-form-row">' +
        '<label class="cc-form-label">Research mode<select data-goal-runner-field="research_mode" id="ccGoalRunnerResearchMode">' +
        '<option value="off">off</option><option value="light" selected>light</option>' +
        '<option value="standard">standard</option><option value="deep">deep</option></select></label>' +
        '<label class="cc-form-label">Run mode<select data-goal-runner-field="run_mode" id="ccGoalRunnerRunMode">' +
        '<option value="draft_only" selected>Research + plan only</option>' +
        '<option value="approve_only">Research + plan + approve</option>' +
        '<option value="run">Full run</option></select></label>' +
        '<label class="cc-form-label">Approval mode<select data-goal-runner-field="approval_mode" id="ccGoalRunnerApprovalMode">' +
        '<option value="manual_approval" selected>manual_approval</option>' +
        '<option value="auto_approve_if_policy_clean">auto_approve_if_policy_clean</option>' +
        '<option value="auto_run_if_policy_clean">auto_run_if_policy_clean</option></select></label>' +
        '</div>' +
        '<div class="cc-form-row">' +
        '<label class="cc-form-label">Budget max runs<input data-goal-runner-field="max_run_count" id="ccGoalRunnerMaxRuns" type="number" min="1"></label>' +
        '<label class="cc-form-label">Budget wall-clock hours<input data-goal-runner-field="max_wall_clock_hours" id="ccGoalRunnerMaxHours" type="number" min="0.1" step="0.1"></label>' +
        '</div>' +
        '<div id="ccGoalRunnerWarnings"></div>' +
        '<div class="cc-form-actions">' +
        '<button type="button" class="cc-primary-btn" id="ccGoalRunnerRun">Run draft_only</button>' +
        '<button type="button" class="cc-ghost-btn" id="ccGoalRunnerRefresh">Refresh</button>' +
        '</div>' +
        '<div class="cc-meta-line" id="ccGoalRunnerResult"></div>' +
        '</article>';

      $('ccGoalRunnerProject').addEventListener('change', function () {
        void loadGoalRunnerProjectProfile($('ccGoalRunnerProject').value);
      });
      ['ccGoalRunnerResearchMode', 'ccGoalRunnerRunMode', 'ccGoalRunnerApprovalMode'].forEach(function (id) {
        var el = $(id);
        if (el) el.addEventListener('change', updateGoalRunnerWarnings);
      });
      $('ccGoalRunnerRun').addEventListener('click', function () { void submitProjectGoalRun(); });
      $('ccGoalRunnerRefresh').addEventListener('click', function () { void refreshGoalRunnerView(); });

      await loadGoalRunnerProjectProfile(
        state.goalRunner.selectedProjectId || CCGoalRunnerHelpers.ANIMA_LINUX_PROJECT_ID
      );
      state.goalRunner.wired = true;
      if (state.goalRunner.lastResponse) await refreshGoalRunnerView();
    } catch (err) {
      controlsHost.innerHTML = '<div class="cc-empty">' + escapeHtml(err.message) + '</div>';
    }
  }

  async function submitProjectGoalRun() {
    var resultHost = $('ccGoalRunnerResult');
    var form = readGoalRunnerForm();
    var validation = CCGoalRunnerHelpers.validateGoalStatement(
      form.statement,
      form.projectId,
      state.goalRunner.running
    );
    if (!validation.ok) {
      if (resultHost) resultHost.textContent = validation.error;
      return;
    }
    var payload = CCGoalRunnerHelpers.buildGoalRunPayload(form, state.goalRunner.selectedProfile);
    if (resultHost) resultHost.textContent = 'Submitting goal run…';
    state.goalRunner.running = true;
    try {
      var response = await govFetch(CCGoalRunnerHelpers.goalRunPostPath(form.projectId), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      state.goalRunner.lastResponse = response;
      if (resultHost) {
        resultHost.textContent =
          'goal_run_id ' + (response.goal_run_id || '—') +
          ' · goal_id ' + (response.goal_id || '—') +
          ' · status ' + (response.status || '—');
      }
      await refreshGoalRunnerView();
    } catch (err) {
      if (resultHost) resultHost.textContent = String(err.message || err);
    } finally {
      state.goalRunner.running = false;
    }
  }

  async function refreshGoalRunnerView() {
    var response = state.goalRunner.lastResponse;
    var summaryHost = $('ccGoalRunnerSummary');
    var timelineHost = $('ccGoalRunnerTimeline');
    var panelsHost = $('ccGoalRunnerPanels');
    if (!response || !summaryHost || !timelineHost || !panelsHost) {
      if (summaryHost && !response) {
        summaryHost.innerHTML = '<div class="cc-empty">Run a goal to see lifecycle output.</div>';
      }
      return;
    }
    var projectId = response.project_id || state.goalRunner.selectedProjectId;
    var goalId = response.goal_id;
    var goalDetail = null;
    var queuePayload = null;
    var driverPayload = null;
    var goalRunProjection = null;
    try {
      var fetches = [
        govFetch('goals/' + encodeURIComponent(goalId) + '?project_id=' + encodeURIComponent(projectId)),
        govFetch('goals/' + encodeURIComponent(goalId) + '/queue'),
        govFetch(driverStatusPath())
      ];
      if (response.goal_run_id) {
        fetches.push(
          govFetch('goal-runs/' + encodeURIComponent(response.goal_run_id)).catch(function () { return null; })
        );
      }
      var results = await Promise.all(fetches);
      goalDetail = results[0];
      queuePayload = results[1];
      driverPayload = results[2];
      goalRunProjection = results[3] || null;
    } catch (_err) {
      goalDetail = goalDetail || {};
    }
    summaryHost.innerHTML =
      '<article class="cc-card"><header class="cc-card-head"><h2>Run summary</h2></header>' +
      '<div class="cc-meta-line">goal_run_id: ' + escapeHtml(response.goal_run_id || '—') +
      ' · goal_id: ' + escapeHtml(goalId || '—') +
      ' · status: ' + escapeHtml(response.status || '—') + '</div>' +
      '<div class="cc-meta-line">research: ' + escapeHtml((response.research && response.research.status) || '—') +
      ' · breakdown: ' + escapeHtml((response.breakdown && response.breakdown.status) || '—') +
      ' · driver started: ' + ((response.driver && response.driver.started) ? 'yes' : 'no') + '</div></article>';

    var timelineState = (goalRunProjection && goalRunProjection.state) || response.status || 'created';
    timelineHost.innerHTML =
      '<article class="cc-card"><header class="cc-card-head"><h2>Timeline</h2></header>' +
      CCGoalRunnerHelpers.buildTimelineHtml(timelineState, response) +
      '</article>';

    panelsHost.innerHTML =
      '<article class="cc-card"><header class="cc-card-head"><h2>Research</h2></header>' +
      CCGoalRunnerHelpers.buildResearchPanelHtml(response, goalDetail) + '</article>' +
      '<article class="cc-card"><header class="cc-card-head"><h2>Breakdown</h2></header>' +
      CCGoalRunnerHelpers.buildBreakdownPanelHtml(response, queuePayload, state.goalRunner.selectedProfile) + '</article>' +
      '<article class="cc-card"><header class="cc-card-head"><h2>Execution</h2></header>' +
      CCGoalRunnerHelpers.buildExecutionPanelHtml(response, driverPayload, response.run_mode || readGoalRunnerForm().runMode) + '</article>' +
      '<article class="cc-card"><header class="cc-card-head"><h2>Blocker / Recovery</h2></header>' +
      CCGoalRunnerHelpers.buildBlockerRecoveryPanelHtml(response, goalRunProjection) + '</article>' +
      '<article class="cc-card"><header class="cc-card-head"><h2>Memory</h2></header>' +
      CCGoalRunnerHelpers.buildMemoryPanelHtml(response) + '</article>' +
      '<article class="cc-card"><header class="cc-card-head"><h2>Outcome report</h2></header>' +
      CCGoalRunnerHelpers.buildOutcomePanelHtml(response, goalDetail) + '</article>';
  }

  function renderAll() {
    renderStats();
    renderCharts();
    renderProjects();
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
      await loadProjectDetails();
      await loadGoalsAndRunsAcrossProjects();
      state.driver = await govFetch(driverStatusPath());
      try { state.meta = await govFetch('meta'); } catch (_m) { state.meta = null; }
      setConnection(true);
    } catch (err) {
      state.projects = [];
      state.projectDetails = {};
      state.goals = [];
      state.runs = [];
      state.driver = null;
      setConnection(false, err.message);
    } finally {
      if (shell) shell.classList.remove('cc-loading');
      renderAll();
      if (state.section === 'goals' && state.goalRunner.wired) {
        renderProjects();
      }
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
