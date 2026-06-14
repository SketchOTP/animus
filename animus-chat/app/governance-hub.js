/** Governance hub — BFF-backed Registry / Runs / Goals / Driver views (Command Brief overlay tabs). */

/** @typedef {{ goal_id: string, status?: string, statement?: string }} GoalRow */

const AnimusGovernanceHelpers = {
  parseGoalsList(data) {
    return Array.isArray(data && data.goals) ? data.goals : [];
  },
  formatGoalStatus(goal) {
    return String((goal && (goal.display_status || goal.status)) || 'unknown');
  },
  shouldShowBreakdownApproval(goal) {
    const status = String((goal && (goal.display_status || goal.status)) || '');
    return status === 'pending_approval';
  },
  formatBudgetCaps(tierPolicy) {
    const policy = tierPolicy && tierPolicy.registry_tier_policy ? tierPolicy.registry_tier_policy : {};
    const budgets = policy.budget_defaults && typeof policy.budget_defaults === 'object'
      ? policy.budget_defaults
      : {};
    const runs = budgets.max_run_count != null ? String(budgets.max_run_count) : '—';
    const hours = budgets.max_wall_clock_hours != null ? String(budgets.max_wall_clock_hours) : '—';
    return 'Budget caps: runs ' + runs + ' · wall-clock hours ' + hours;
  },
  parseDriverStatus(data) {
    if (!data || typeof data !== 'object') {
      return { status: 'idle', active_goal_id: null, active_queue_entry_id: null, last_stop_reason: null };
    }
    return {
      status: String(data.status || 'idle'),
      active_goal_id: data.active_goal_id || null,
      active_queue_entry_id: data.active_queue_entry_id || null,
      last_stop_reason: data.last_stop_reason || null,
      last_seq: data.last_seq != null ? data.last_seq : null,
    };
  },
  formatDriverStatus(driver) {
    return String((driver && driver.status) || 'idle');
  },
  formatBudgetHint(driver) {
    const reason = driver && driver.last_stop_reason ? String(driver.last_stop_reason) : '';
    if (reason.indexOf('budget') >= 0 || reason === 'budget_exceeded') {
      return 'Budget cap reached (run count or wall-clock)';
    }
    return 'Budget: registry policy (run count + wall-clock)';
  },
  shouldShowSignOff(goalStatus) {
    return String(goalStatus || '') === 'pending_completion';
  },
  formatResearchLabel(research) {
    const meta = research && typeof research === 'object' ? research : {};
    const enabled = !!meta.include_research;
    const count = meta.finding_count != null ? Number(meta.finding_count) : 0;
    const last = meta.last_scout_at ? String(meta.last_scout_at) : '—';
    const flag = enabled ? 'enabled' : 'disabled (default false)';
    return 'Scout: ' + flag + ' · findings ' + count + ' · last ' + last;
  },
  formatLicenseBadge(license, licenseFlags) {
    const label = String(license || 'UNKNOWN');
    const flags = Array.isArray(licenseFlags) ? licenseFlags : [];
    const referenceOnly = flags.indexOf('reference_only') >= 0;
    return {
      label: label,
      referenceOnly: referenceOnly,
      className: referenceOnly ? 'scout-license scout-license-ref' : 'scout-license',
    };
  },
  formatRelevanceBar(relevance) {
    const value = Number(relevance);
    const pct = Number.isFinite(value) ? Math.max(0, Math.min(100, Math.round(value * 100))) : 0;
    return { pct: pct, label: Number.isFinite(value) ? value.toFixed(2) : '—' };
  },
  buildScoutArtifactPath(repoId, goalId, evidenceRef) {
    if (!repoId || !goalId || !evidenceRef) return '';
    return (
      'repos/' +
      encodeURIComponent(repoId) +
      '/goals/' +
      encodeURIComponent(goalId) +
      '/scout/artifacts/' +
      encodeURIComponent(String(evidenceRef))
    );
  },
  buildFindingRowHtml(finding, repoId, goalId) {
    const row = finding && typeof finding === 'object' ? finding : {};
    const badge = AnimusGovernanceHelpers.formatLicenseBadge(row.license, row.license_flags);
    const rel = AnimusGovernanceHelpers.formatRelevanceBar(row.relevance);
    const evidencePath = AnimusGovernanceHelpers.buildScoutArtifactPath(
      repoId,
      row.goal_id || goalId || '',
      row.evidence_ref,
    );
    const evidenceCell = evidencePath
      ? '<a href="/api/governance/' + evidencePath + '" target="_blank" rel="noopener">evidence</a>'
      : '—';
    return (
      '<tr><td>' +
      (row.source || '') +
      '</td><td><span class="' +
      badge.className +
      '">' +
      badge.label +
      (badge.referenceOnly ? ' · ref-only' : '') +
      '</span></td><td><span class="scout-relevance">' +
      rel.label +
      '</span></td><td>' +
      evidenceCell +
      '</td></tr>'
    );
  },
  buildResearchSectionHtml(goal, findingsPayload) {
    const research = goal && goal.research ? goal.research : {};
    const findings = Array.isArray(findingsPayload && findingsPayload.findings)
      ? findingsPayload.findings
      : [];
    const repoId = goal && goal.repo_id ? String(goal.repo_id) : '';
    const goalId = goal && goal.goal_id ? String(goal.goal_id) : '';
    let body = '';
    if (!findings.length) {
      body =
        '<div class="command-brief-meta">No scout findings indexed for this goal.</div>';
    } else {
      body =
        '<table class="command-brief-table"><thead><tr><th>Source</th><th>License</th><th>Relevance</th><th>Evidence</th></tr></thead><tbody>' +
        findings
          .map(function (item) {
            return AnimusGovernanceHelpers.buildFindingRowHtml(item, repoId, goalId);
          })
          .join('') +
        '</tbody></table>';
    }
    return (
      '<div class="command-brief-card" style="margin-top:12px">' +
      '<div class="command-brief-card-title"><strong>Research</strong></div>' +
      '<div class="command-brief-meta">' +
      AnimusGovernanceHelpers.formatResearchLabel(research) +
      '</div>' +
      body +
      '</div>'
    );
  },
  buildHierarchySummary(milestonesPayload, queuePayload) {
    const milestones = Array.isArray(milestonesPayload && milestonesPayload.milestones)
      ? milestonesPayload.milestones
      : [];
    const phases = Array.isArray(milestonesPayload && milestonesPayload.phases)
      ? milestonesPayload.phases
      : [];
    const queue = Array.isArray(queuePayload && queuePayload.queue_entries)
      ? queuePayload.queue_entries
      : [];
    return {
      milestone_count: milestones.length,
      phase_count: phases.length,
      queue_count: queue.length,
      ready_count: queue.filter((row) => row.materialization === 'ready').length,
      dispatched_count: queue.filter((row) => row.materialization === 'dispatched').length,
      completed_count: queue.filter((row) => row.materialization === 'completed').length,
    };
  },
};

const AnimusGoalRunnerHelpers = {
  ANIMA_LINUX_PROJECT_ID: 'c9eebdd2-a087-5eae-a074-77b5572fe7b5', // anima-linux
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
    'operator_required',
  ],
  RUN_MODE_LABELS: {
    draft_only: 'Research + plan only',
    approve_only: 'Research + plan + approve',
    run: 'Full run',
  },
  validateGoalStatement(statement, projectId, alreadyRunning) {
    const text = String(statement || '').trim();
    if (!projectId) {
      return { ok: false, error: 'Select a project before running a goal.' };
    }
    if (!text) {
      return { ok: false, error: 'Goal statement is required.' };
    }
    if (text.length > AnimusGoalRunnerHelpers.GOAL_STATEMENT_MAX_LEN) {
      return {
        ok: false,
        error: 'Goal statement exceeds maximum length (' + AnimusGoalRunnerHelpers.GOAL_STATEMENT_MAX_LEN + ').',
      };
    }
    if (alreadyRunning) {
      return { ok: false, error: 'A goal run is already in progress.' };
    }
    return { ok: true, statement: text };
  },
  buildGoalRunPayload(form, profile) {
    const projectId = form.projectId;
    const statement = String(form.statement || '').trim();
    const runMode = form.runMode || 'draft_only';
    const researchMode = form.researchMode || (profile && profile.research_mode) || 'light';
    const approvalMode = form.approvalMode || (profile && profile.approval_mode) || 'manual_approval';
    const budgetDefaults =
      profile && profile.budget_defaults && typeof profile.budget_defaults === 'object'
        ? profile.budget_defaults
        : {};
    const maxRunCount = form.maxRunCount != null && form.maxRunCount !== ''
      ? Number(form.maxRunCount)
      : budgetDefaults.max_run_count;
    const maxWallHours = form.maxWallHours != null && form.maxWallHours !== ''
      ? Number(form.maxWallHours)
      : budgetDefaults.max_wall_clock_hours;
    return {
      statement: statement,
      run_mode: runMode,
      goal_size_hint: form.goalSizeHint || 'S',
      research_mode: researchMode,
      approval_mode: approvalMode,
      budget_override: {
        max_run_count: maxRunCount,
        max_wall_clock_hours: maxWallHours,
      },
      _meta: { project_id: projectId },
    };
  },
  goalRunPostPath(projectId) {
    return 'projects/' + encodeURIComponent(projectId) + '/goal-runs';
  },
  shouldShowResearchRequiredWarning(profile, researchMode) {
    return !!(profile && profile.research_required && String(researchMode || '') === 'off');
  },
  shouldShowAutoRunWarning(approvalMode) {
    return String(approvalMode || '') === 'auto_run_if_policy_clean';
  },
  shouldShowRunModeWarning(runMode) {
    return String(runMode || '') === 'run';
  },
  mapTimelineIndex(state, response) {
    const normalized = String(state || '').trim();
    if (normalized === 'pending_approval') {
      return AnimusGoalRunnerHelpers.TIMELINE_STATES.indexOf('awaiting_approval');
    }
    const idx = AnimusGoalRunnerHelpers.TIMELINE_STATES.indexOf(normalized);
    if (idx >= 0) {
      return idx;
    }
    const events = Array.isArray(response && response.events_published) ? response.events_published : [];
    if (events.indexOf('governance.goal_run.preflight.completed') >= 0) {
      return AnimusGoalRunnerHelpers.TIMELINE_STATES.indexOf('preflight_passed');
    }
    return 0;
  },
  buildTimelineHtml(state, response) {
    const activeIndex = AnimusGoalRunnerHelpers.mapTimelineIndex(state, response);
    return (
      '<ul class="command-brief-list goal-runner-timeline">' +
      AnimusGoalRunnerHelpers.TIMELINE_STATES.map(function (item, index) {
        const cls = index <= activeIndex ? 'goal-runner-timeline-active' : 'goal-runner-timeline-pending';
        return '<li class="' + cls + '">' + item + '</li>';
      }).join('') +
      '</ul>'
    );
  },
  buildResearchPanelHtml(response, goalDetail) {
    const research = (response && response.research) || {};
    const goal = goalDetail || {};
    const status = research.status || goal.research_status || '—';
    const mode = research.mode || goal.research_mode || '—';
    const required = goal.research_required != null ? String(goal.research_required) : '—';
    const confidence = research.confidence || goal.research_confidence || '—';
    const strategy = research.recommended_strategy || goal.recommended_strategy || '—';
    const artifactRef = research.artifact_ref || goal.research_artifact_ref || '—';
    return (
      '<div class="command-brief-meta">research_status: ' +
      status +
      ' · mode: ' +
      mode +
      ' · required: ' +
      required +
      '</div>' +
      '<div class="command-brief-meta">confidence: ' +
      confidence +
      ' · strategy: ' +
      strategy +
      '</div>' +
      '<div class="command-brief-meta">artifact: ' +
      artifactRef +
      ' · oracle brief: summary only (expand in evidence)</div>'
    );
  },
  buildBreakdownPanelHtml(response, queuePayload, profile) {
    const breakdown = (response && response.breakdown) || {};
    const queue = Array.isArray(queuePayload && queuePayload.queue_entries) ? queuePayload.queue_entries : [];
    const validator = (profile && profile.default_validator) || '—';
    const first = queue.length ? queue[0] : null;
    const allowed = first && first.allowed_files_hint_json
      ? first.allowed_files_hint_json
      : first && first.allowed_files_hint
        ? JSON.stringify(first.allowed_files_hint)
        : '—';
    return (
      '<div class="command-brief-meta">breakdown_version: ' +
      (breakdown.version || '—') +
      ' · status: ' +
      (breakdown.status || '—') +
      ' · queue entries: ' +
      (breakdown.queue_entry_count != null ? breakdown.queue_entry_count : queue.length) +
      '</div>' +
      '<div class="command-brief-meta">entry tier: ' +
      (first && first.tier ? first.tier : '—') +
      ' · validator: ' +
      validator +
      '</div>' +
      '<div class="command-brief-meta">allowed files: ' +
      allowed +
      '</div>'
    );
  },
  buildExecutionPanelHtml(response, driverPayload, runMode) {
    const driver = (response && response.driver) || {};
    const remote = driverPayload || {};
    const started = !!driver.started;
    const lines = [
      'driver status: ' + (remote.status || 'idle'),
      'driver started: ' + (started ? 'yes' : 'no'),
      'active_goal_id: ' + (remote.active_goal_id || '—'),
      'active_queue_entry_id: ' + (remote.active_queue_entry_id || '—'),
      'run_id: ' + (driver.run_id || '—'),
    ];
    if (runMode === 'draft_only' && !started) {
      lines.push('draft_only: Driver not started (expected)');
    }
    return lines.map(function (line) {
      return '<div class="command-brief-meta">' + line + '</div>';
    }).join('');
  },
  buildBlockerRecoveryPanelHtml(response, goalRunProjection) {
    const blockReason = (response && response.block_reason) || (goalRunProjection && goalRunProjection.block_reason);
    const state = String((response && response.status) || (goalRunProjection && goalRunProjection.state) || '');
    if (!blockReason && state !== 'blocked' && state !== 'operator_required') {
      return '<div class="command-brief-meta">No blocker detected.</div>';
    }
    const operatorRequired = state === 'operator_required';
    const guidance = operatorRequired
      ? 'Operator decision required.'
      : 'Recovery prepared automatically.';
    return (
      '<div class="command-brief-meta">blocker_class: ' +
      (blockReason || '—') +
      ' · failed_layer: orchestrator</div>' +
      '<div class="command-brief-meta">triage decision: pending · operator_required: ' +
      String(operatorRequired) +
      '</div>' +
      '<div class="command-brief-meta">' +
      guidance +
      '</div>'
    );
  },
  buildMemoryPanelHtml(response) {
    const memory = (response && response.memory) || {};
    const mode = memory.mode || memory.memory_mode || 'advisory';
    return (
      '<div class="command-brief-meta">memory mode: ' +
      mode +
      ' · recall: ' +
      (memory.recall_status || 'skipped') +
      ' · record: ' +
      (memory.record_status || 'skipped') +
      '</div>' +
      '<div class="command-brief-meta">memory_refs: ' +
      (Array.isArray(memory.memory_refs) ? memory.memory_refs.join(', ') : '—') +
      '</div>' +
      '<div class="command-brief-meta"><strong>Mimir is advisory memory, not approval authority.</strong></div>'
    );
  },
  buildOutcomePanelHtml(response, goalDetail) {
    const status = String((response && response.status) || (goalDetail && goalDetail.status) || '');
    const displayStatus =
      status === 'pending_completion'
        ? 'Pending final review/sign-off'
        : status || '—';
    const evidence = Array.isArray(response && response.evidence_refs) ? response.evidence_refs : [];
    return (
      '<div class="command-brief-meta">status: ' +
      displayStatus +
      ' · goal_run_id: ' +
      ((response && response.goal_run_id) || '—') +
      ' · goal_id: ' +
      ((response && response.goal_id) || '—') +
      '</div>' +
      '<div class="command-brief-meta">commits: — · tests: — · evidence refs: ' +
      evidence.length +
      '</div>' +
      '<div class="command-brief-meta">No self-sign-off from Goal Runner.</div>'
    );
  },
  formatProjectOptionLabel(project) {
    const row = project || {};
    const name = row.name || row.display_name || row.slug || row.project_id || 'project';
    const dirty =
      row.dirty_tree && row.dirty_tree.blocking
        ? ' · dirty (blocking)'
        : row.dirty_tree && row.dirty_tree.blocking_reason
          ? ' · dirty: ' + row.dirty_tree.blocking_reason
          : '';
    return name + ' · ' + (row.project_id || '') + ' · ' + (row.repo_path || '') + dirty;
  },
};

(function () {
  const PLATFORM_PROJECT_ID = '260c61b1-f774-5493-8ff3-97e0d750f58c';
  const WORKSPACE_ID = 'a6acfd2b-3195-5085-aae8-ccb93fc7a02b';
  const CANONICAL_RUN_ID = 'a1dfc5a6-a1b3-4bc8-86b9-a7910f0aaae1';
  let _cachedRepoPath = null;
  let _goalRunnerState = {
    running: false,
    lastResponse: null,
    selectedProjectId: null,
    selectedProfile: null,
  };

  function $(id) {
    return document.getElementById(id);
  }

  async function govFetch(path, options) {
    const opts = options || {};
    const headers = Object.assign({ Accept: 'application/json' }, opts.headers || {});
    const resp = await fetch('/api/governance/' + path.replace(/^\//, ''), {
      method: opts.method || 'GET',
      headers: headers,
      body: opts.body || undefined,
    });
    const body = await resp.json().catch(() => ({}));
    if (!resp.ok) {
      const detail = body.detail || body.error || resp.statusText;
      throw new Error(String(detail || 'governance_fetch_failed'));
    }
    return body;
  }

  function newRunId() {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
      return crypto.randomUUID();
    }
    return 'run-' + Date.now();
  }

  async function resolveRepoPath() {
    if (_cachedRepoPath) return _cachedRepoPath;
    const data = await govFetch('registry/projects/' + encodeURIComponent(PLATFORM_PROJECT_ID));
    const repos = Array.isArray(data.repos) ? data.repos : [];
    _cachedRepoPath = repos.length && repos[0].repo_path ? String(repos[0].repo_path) : '';
    return _cachedRepoPath;
  }

  async function driverControl(action, goalId) {
    const repoPath = await resolveRepoPath();
    const body = { repo_path: repoPath, run_id: newRunId(), goal_id: goalId || null };
    return govFetch('driver/' + action, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
  }

  async function signOffGoal(goalId) {
    const repoPath = await resolveRepoPath();
    return govFetch('goals/' + encodeURIComponent(goalId) + '/sign-off', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ repo_path: repoPath, request_id: 'ui-sign-off-' + Date.now() }),
    });
  }

  function setGovernanceTab(tab) {
    const tabs = ['brief', 'projects', 'goals', 'goalrunner', 'driver', 'runs'];
    for (const name of tabs) {
      const panel = $('governancePanel' + name.charAt(0).toUpperCase() + name.slice(1));
      const btn = $('governanceTab' + name.charAt(0).toUpperCase() + name.slice(1));
      if (panel) panel.hidden = name !== tab;
      if (btn) btn.classList.toggle('active', name === tab);
    }
    if (tab === 'projects') void renderGovernanceProjects();
    if (tab === 'goals') void renderGovernanceGoals();
    if (tab === 'goalrunner') void renderGoalRunner();
    if (tab === 'queue') void renderGovernanceQueue();
    if (tab === 'driver') void renderGovernanceDriver();
    if (tab === 'runs') void renderGovernanceRuns();
    if (tab === 'brief') void renderGovernanceBriefExtras();
  }

  function ensureQueuePanel() {
    const bar = $('governanceTabBar');
    const scroll = $('commandBriefMainScroll');
    if (!bar || !scroll || $('governanceTabQueue')) return;
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'governance-tab-btn';
    btn.id = 'governanceTabQueue';
    btn.setAttribute('data-governance-tab', 'queue');
    btn.setAttribute('role', 'tab');
    btn.textContent = 'Queue';
    const driverBtn = $('governanceTabDriver');
    if (driverBtn && driverBtn.parentNode) {
      driverBtn.parentNode.insertBefore(btn, driverBtn);
    } else {
      bar.appendChild(btn);
    }
    const panel = document.createElement('div');
    panel.id = 'governancePanelQueue';
    panel.className = 'governance-panel';
    panel.hidden = true;
    panel.innerHTML = '<div id="governanceQueueDetail"></div>';
    scroll.appendChild(panel);
  }

  async function renderGovernanceBriefExtras() {
    const host = $('governanceBriefMemory');
    if (!host) return;
    host.innerHTML = '<div class="command-brief-meta">Loading memory outcomes…</div>';
    try {
      const data = await govFetch(
        'projects/' + encodeURIComponent(PLATFORM_PROJECT_ID) + '/memory?limit=8',
      );
      const events = Array.isArray(data.events) ? data.events : [];
      if (!events.length) {
        host.innerHTML = '<div class="command-brief-meta">No Mimir outcomes recorded yet.</div>';
        return;
      }
      host.innerHTML =
        '<ul class="command-brief-list">' +
        events
          .map(function (ev) {
            return (
              '<li>run ' +
              (ev.run_id || '').slice(0, 8) +
              '… · outcome ' +
              (ev.outcome || '—') +
              ' · ids ' +
              (Array.isArray(ev.memory_ids) ? ev.memory_ids.length : 0) +
              '</li>'
            );
          })
          .join('') +
        '</ul>';
    } catch (err) {
      host.innerHTML = '<div class="command-brief-err">' + String(err.message || err) + '</div>';
    }
  }

  async function renderGovernanceQueue() {
    const host = $('governanceQueueDetail');
    if (!host) return;
    host.innerHTML = '<div class="command-brief-meta">Loading directive queue…</div>';
    try {
      const data = await govFetch('queue?project_id=' + encodeURIComponent(PLATFORM_PROJECT_ID));
      const rows = Array.isArray(data.queue_entries) ? data.queue_entries : [];
      host.innerHTML =
        '<div class="command-brief-card">' +
        '<div class="command-brief-card-title"><strong>Directive queue</strong>' +
        '<span class="command-brief-status">' +
        rows.length +
        ' entries</span></div>' +
        '<table class="command-brief-table"><thead><tr><th>Goal</th><th>#</th><th>Objective</th><th>State</th><th>Tier</th></tr></thead><tbody>' +
        rows
          .map(function (row) {
            return (
              '<tr><td>' +
              (row.goal_id || '').slice(0, 8) +
              '…</td><td>' +
              (row.ordinal || '') +
              '</td><td>' +
              (row.objective || '') +
              '</td><td>' +
              (row.materialization || '') +
              '</td><td>' +
              (row.tier || '') +
              '</td></tr>'
            );
          })
          .join('') +
        '</tbody></table></div>';
    } catch (err) {
      host.innerHTML = '<div class="command-brief-err">' + String(err.message || err) + '</div>';
    }
  }

  function ensureGoalsPanel() {
    const bar = $('governanceTabBar');
    const scroll = $('commandBriefMainScroll');
    if (!bar || !scroll || $('governanceTabGoals')) return;
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'governance-tab-btn';
    btn.id = 'governanceTabGoals';
    btn.setAttribute('data-governance-tab', 'goals');
    btn.setAttribute('role', 'tab');
    btn.textContent = 'Goals';
    const runsBtn = $('governanceTabRuns');
    if (runsBtn && runsBtn.parentNode) {
      runsBtn.parentNode.insertBefore(btn, runsBtn);
    } else {
      bar.appendChild(btn);
    }
    const panel = document.createElement('div');
    panel.id = 'governancePanelGoals';
    panel.className = 'governance-panel';
    panel.hidden = true;
    panel.innerHTML =
      '<div id="governanceGoalsIntake"></div>' +
      '<div class="command-brief-cards" id="governanceGoalsList"></div>' +
      '<div id="governanceGoalsDetail"></div>';
    scroll.appendChild(panel);
  }

  function ensureGoalRunnerPanel() {
    const bar = $('governanceTabBar');
    const scroll = $('commandBriefMainScroll');
    if (!bar || !scroll || $('governanceTabGoalrunner')) return;
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'governance-tab-btn';
    btn.id = 'governanceTabGoalrunner';
    btn.setAttribute('data-governance-tab', 'goalrunner');
    btn.setAttribute('role', 'tab');
    btn.textContent = 'Goal Runner';
    const driverBtn = $('governanceTabDriver');
    if (driverBtn && driverBtn.parentNode) {
      driverBtn.parentNode.insertBefore(btn, driverBtn);
    } else {
      bar.appendChild(btn);
    }
    const panel = document.createElement('div');
    panel.id = 'governancePanelGoalrunner';
    panel.className = 'governance-panel';
    panel.hidden = true;
    panel.innerHTML =
      '<div id="governanceGoalRunnerControls"></div>' +
      '<div id="governanceGoalRunnerSummary"></div>' +
      '<div id="governanceGoalRunnerTimeline"></div>' +
      '<div id="governanceGoalRunnerPanels"></div>';
    scroll.appendChild(panel);
  }

  function ensureDriverPanel() {
    const bar = $('governanceTabBar');
    const scroll = $('commandBriefMainScroll');
    if (!bar || !scroll || $('governanceTabDriver')) return;
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'governance-tab-btn';
    btn.id = 'governanceTabDriver';
    btn.setAttribute('data-governance-tab', 'driver');
    btn.setAttribute('role', 'tab');
    btn.textContent = 'Driver';
    const runsBtn = $('governanceTabRuns');
    if (runsBtn && runsBtn.parentNode) {
      runsBtn.parentNode.insertBefore(btn, runsBtn);
    } else {
      bar.appendChild(btn);
    }
    const panel = document.createElement('div');
    panel.id = 'governancePanelDriver';
    panel.className = 'governance-panel';
    panel.hidden = true;
    panel.innerHTML = '<div id="governanceDriverDetail"></div>';
    scroll.appendChild(panel);
  }

  async function renderGovernanceDriver() {
    const host = $('governanceDriverDetail');
    if (!host) return;
    host.innerHTML = '<div class="command-brief-meta">Loading driver…</div>';
    try {
      const driverRaw = await govFetch(
        'driver/status?workspace_id=' + encodeURIComponent(WORKSPACE_ID),
      );
      const driver = AnimusGovernanceHelpers.parseDriverStatus(driverRaw);
      let goalBlock = '';
      let signOffBtn = '';
      if (driver.active_goal_id) {
        const goal = await govFetch(
          'goals/' +
            encodeURIComponent(driver.active_goal_id) +
            '?project_id=' +
            encodeURIComponent(PLATFORM_PROJECT_ID),
        );
        goalBlock =
          '<div class="command-brief-meta">Active goal: ' +
          driver.active_goal_id +
          ' · ' +
          AnimusGovernanceHelpers.formatGoalStatus(goal) +
          ' · tier ' +
          (goal.tier || '—') +
          '</div>';
        if (AnimusGovernanceHelpers.shouldShowSignOff(goal.status)) {
          signOffBtn =
            '<button type="button" class="btn btn-primary" id="governanceDriverSignOff">Sign off goal completion</button>';
        }
      }
      host.innerHTML =
        '<div class="command-brief-card" id="governanceDriverPanel">' +
        '<div class="command-brief-card-title"><strong>Driver</strong><span class="command-brief-status" id="governanceDriverStatus">' +
        AnimusGovernanceHelpers.formatDriverStatus(driver) +
        '</span></div>' +
        '<div class="command-brief-meta" id="governanceDriverStopReason">Stop reason: ' +
        (driver.last_stop_reason || '—') +
        '</div>' +
        '<div class="command-brief-meta" id="governanceDriverBudget">' +
        AnimusGovernanceHelpers.formatBudgetHint(driver) +
        '</div>' +
        '<div class="command-brief-meta">Active entry: ' +
        (driver.active_queue_entry_id || '—') +
        '</div>' +
        goalBlock +
        '<div style="margin-top:8px;display:flex;flex-wrap:wrap;gap:6px">' +
        '<button type="button" class="btn btn-ghost" data-driver-action="start">Start</button>' +
        '<button type="button" class="btn btn-ghost" data-driver-action="pause">Pause</button>' +
        '<button type="button" class="btn btn-ghost" data-driver-action="resume">Resume</button>' +
        '<button type="button" class="btn btn-ghost" data-driver-action="halt">Halt</button>' +
        '<button type="button" class="btn btn-ghost" data-driver-action="stop">Stop</button>' +
        signOffBtn +
        '</div>' +
        '<div class="command-brief-meta" id="governanceDriverActionResult" style="margin-top:8px"></div>' +
        '</div>';
      host.querySelectorAll('[data-driver-action]').forEach((btn) => {
        btn.addEventListener('click', () =>
          void (async () => {
            const action = btn.getAttribute('data-driver-action') || '';
            const resultHost = $('governanceDriverActionResult');
            if (resultHost) resultHost.textContent = 'Sending ' + action + '…';
            try {
              const resp = await driverControl(action, driver.active_goal_id);
              if (resultHost) {
                resultHost.textContent = (resp.event || action) + ' ok';
              }
              await renderGovernanceDriver();
            } catch (err) {
              if (resultHost) resultHost.textContent = String(err.message || err);
            }
          })(),
        );
      });
      const signOff = $('governanceDriverSignOff');
      if (signOff && driver.active_goal_id) {
        signOff.addEventListener('click', () =>
          void (async () => {
            const resultHost = $('governanceDriverActionResult');
            if (resultHost) resultHost.textContent = 'Publishing sign-off…';
            try {
              const resp = await signOffGoal(driver.active_goal_id);
              if (resultHost) {
                resultHost.textContent = (resp.event || 'governance.goal.completed') + ' ok';
              }
              await renderGovernanceDriver();
            } catch (err) {
              if (resultHost) resultHost.textContent = String(err.message || err);
            }
          })(),
        );
      }
    } catch (err) {
      host.innerHTML = '<div class="command-brief-err">' + String(err.message || err) + '</div>';
    }
  }

  async function submitGoalIntake(formEl) {
    const statement = (formEl.querySelector('[data-intake-field="statement"]') || {}).value || '';
    const repoPath = (formEl.querySelector('[data-intake-field="repo_path"]') || {}).value || '';
    const projectId =
      (formEl.querySelector('[data-intake-field="project_id"]') || {}).value || PLATFORM_PROJECT_ID;
    const includeMemory = !!(formEl.querySelector('[data-intake-field="include_memory"]') || {}).checked;
    const includeResearch = !!(formEl.querySelector('[data-intake-field="include_research"]') || {}).checked;
    const goalSizeHint = (formEl.querySelector('[data-intake-field="goal_size_hint"]') || {}).value || 'M';
    const tierExpectation =
      (formEl.querySelector('[data-intake-field="tier_expectation"]') || {}).value || 'release';
    const maxRunCount = (formEl.querySelector('[data-intake-field="max_run_count"]') || {}).value;
    const maxWallHours = (formEl.querySelector('[data-intake-field="max_wall_clock_hours"]') || {}).value;
    const breakdownAck = !!(formEl.querySelector('[data-intake-field="chk_breakdown"]') || {}).checked;
    const dispatchAck = !!(formEl.querySelector('[data-intake-field="chk_dispatch"]') || {}).checked;
    const signOffAck = !!(formEl.querySelector('[data-intake-field="chk_signoff"]') || {}).checked;
    const payload = {
      statement: String(statement).trim(),
      repo_path: String(repoPath).trim(),
      project_id: String(projectId).trim(),
      include_memory: includeMemory,
      include_research: includeResearch,
      goal_size_hint: goalSizeHint,
      tier_expectation: tierExpectation,
      source: 'human',
      human_checkpoints: {
        breakdown_approval_required: breakdownAck,
        dispatch_opt_in_required: dispatchAck,
        sign_off_required_at_completion: signOffAck,
      },
    };
    const budgetOverride = {};
    if (maxRunCount) budgetOverride.max_run_count = Number(maxRunCount);
    if (maxWallHours) budgetOverride.max_wall_clock_hours = Number(maxWallHours);
    if (Object.keys(budgetOverride).length) payload.budget_override = budgetOverride;
    return govFetch('goals', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
  }

  async function approveGoalBreakdown(goalId, breakdownVersion, repoPath) {
    return govFetch('goals/' + encodeURIComponent(goalId) + '/breakdown/approve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        repo_path: repoPath,
        breakdown_version: breakdownVersion,
        request_id: 'ui-approve-' + Date.now(),
      }),
    });
  }

  async function rejectGoalBreakdown(goalId, breakdownVersion, repoPath, reason) {
    return govFetch('goals/' + encodeURIComponent(goalId) + '/breakdown/reject', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        repo_path: repoPath,
        breakdown_version: breakdownVersion,
        reason: reason,
      }),
    });
  }

  async function renderGoalIntakeForm() {
    const host = $('governanceGoalsIntake');
    if (!host) return;
    host.innerHTML = '<div class="command-brief-meta">Loading intake form…</div>';
    try {
      const project = await govFetch('registry/projects/' + encodeURIComponent(PLATFORM_PROJECT_ID));
      const repos = Array.isArray(project.repos) ? project.repos : [];
      const repoOptions = repos
        .map(function (repo) {
          const path = repo.repo_path || '';
          return '<option value="' + path + '">' + (repo.repo_id || path) + '</option>';
        })
        .join('');
      host.innerHTML =
        '<div class="command-brief-card" id="governanceGoalIntakePanel">' +
        '<div class="command-brief-card-title"><strong>New goal</strong></div>' +
        '<label class="command-brief-meta">Goal statement<br>' +
        '<textarea data-intake-field="statement" rows="3" style="width:100%"></textarea></label>' +
        '<label class="command-brief-meta">Target repo<br>' +
        '<select data-intake-field="repo_path">' +
        repoOptions +
        '</select></label>' +
        '<input type="hidden" data-intake-field="project_id" value="' +
        PLATFORM_PROJECT_ID +
        '">' +
        '<label class="command-brief-meta"><input type="checkbox" data-intake-field="include_memory"> Include memory</label>' +
        '<label class="command-brief-meta"><input type="checkbox" data-intake-field="include_research"> Include research</label>' +
        '<label class="command-brief-meta">Size hint ' +
        '<select data-intake-field="goal_size_hint"><option value="S">S</option><option value="M" selected>M</option><option value="L">L</option></select></label>' +
        '<label class="command-brief-meta">Budget max runs <input data-intake-field="max_run_count" type="number" min="1" placeholder="registry default"></label>' +
        '<label class="command-brief-meta">Budget wall-clock hours <input data-intake-field="max_wall_clock_hours" type="number" min="1" step="0.1" placeholder="registry default"></label>' +
        '<label class="command-brief-meta">Tier expectation ' +
        '<select data-intake-field="tier_expectation"><option value="trivial">trivial</option><option value="standard">standard</option><option value="release" selected>release</option></select></label>' +
        '<div class="command-brief-meta"><strong>Human checkpoints</strong></div>' +
        '<label class="command-brief-meta"><input type="checkbox" data-intake-field="chk_breakdown" checked> Breakdown approval required</label>' +
        '<label class="command-brief-meta"><input type="checkbox" data-intake-field="chk_dispatch" checked> Dispatch opt-in required</label>' +
        '<label class="command-brief-meta"><input type="checkbox" data-intake-field="chk_signoff" checked> Sign-off required at completion</label>' +
        '<button type="button" class="btn btn-primary" id="governanceGoalIntakeSubmit" data-intake-action="submit">Submit goal</button>' +
        '<div class="command-brief-meta" id="governanceGoalIntakeResult" style="margin-top:8px"></div>' +
        '</div>';
      const submitBtn = $('governanceGoalIntakeSubmit');
      const formEl = $('governanceGoalIntakePanel');
      if (submitBtn && formEl) {
        submitBtn.addEventListener('click', () =>
          void (async () => {
            const resultHost = $('governanceGoalIntakeResult');
            if (resultHost) resultHost.textContent = 'Submitting goal…';
            try {
              const resp = await submitGoalIntake(formEl);
              if (resultHost) {
                resultHost.textContent =
                  'Created ' + (resp.goal_id || '').slice(0, 8) + '… · ' + (resp.status || 'pending_approval');
              }
              await renderGovernanceGoals();
              if (resp.goal_id) await showGoalDetail(resp.goal_id);
            } catch (err) {
              if (resultHost) resultHost.textContent = String(err.message || err);
            }
          })(),
        );
      }
    } catch (err) {
      host.innerHTML = '<div class="command-brief-err">' + String(err.message || err) + '</div>';
    }
  }

  async function renderGovernanceGoals() {
    const listHost = $('governanceGoalsList');
    const detailHost = $('governanceGoalsDetail');
    if (!listHost || !detailHost) return;
    await renderGoalIntakeForm();
    listHost.innerHTML = '<div class="command-brief-meta">Loading goals…</div>';
    detailHost.innerHTML = '';
    try {
      const data = await govFetch('goals?project_id=' + encodeURIComponent(PLATFORM_PROJECT_ID));
      const goals = AnimusGovernanceHelpers.parseGoalsList(data);
      listHost.innerHTML = '';
      if (!goals.length) {
        listHost.innerHTML = '<div class="command-brief-meta">No goals for this project.</div>';
        return;
      }
      for (const goal of goals) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'btn btn-ghost';
        btn.style.margin = '4px 0';
        btn.textContent =
          (goal.goal_id || '').slice(0, 8) +
          '… · ' +
          AnimusGovernanceHelpers.formatGoalStatus(goal);
        btn.addEventListener('click', () => void showGoalDetail(goal.goal_id));
        listHost.appendChild(btn);
      }
      await showGoalDetail(goals[0].goal_id);
    } catch (err) {
      listHost.innerHTML = '<div class="command-brief-err">' + String(err.message || err) + '</div>';
    }
  }

  async function showGoalDetail(goalId) {
    const host = $('governanceGoalsDetail');
    if (!host || !goalId) return;
    host.innerHTML = '<div class="command-brief-meta">Loading goal ' + goalId.slice(0, 8) + '…</div>';
    try {
      const q = 'project_id=' + encodeURIComponent(PLATFORM_PROJECT_ID);
      const [goal, milestones, queue, findingsPayload, tierPolicy, releaseGates] = await Promise.all([
        govFetch('goals/' + encodeURIComponent(goalId) + '?' + q),
        govFetch('goals/' + encodeURIComponent(goalId) + '/milestones'),
        govFetch('goals/' + encodeURIComponent(goalId) + '/queue'),
        govFetch('goals/' + encodeURIComponent(goalId) + '/research/findings?' + q).catch(
          function () {
            return null;
          },
        ),
        govFetch(
          'registry/projects/' +
            encodeURIComponent(PLATFORM_PROJECT_ID) +
            '/tier-policy?goal_id=' +
            encodeURIComponent(goalId),
        ).catch(function () { return null; }),
        govFetch('goals/' + encodeURIComponent(goalId) + '/release-gates').catch(function () {
          return null;
        }),
      ]);
      const summary = AnimusGovernanceHelpers.buildHierarchySummary(milestones, queue);
      const queueRows = Array.isArray(queue.queue_entries) ? queue.queue_entries : [];
      const milestoneRows = Array.isArray(milestones.milestones) ? milestones.milestones : [];
      let hierarchyHtml = '';
      milestoneRows.forEach(function (ms) {
        hierarchyHtml +=
          '<div class="command-brief-meta"><strong>M' +
          (ms.ordinal || '') +
          '</strong> ' +
          (ms.title || '') +
          ' · ' +
          (ms.status || '') +
          '</div>';
        const phases = Array.isArray(ms.phases) ? ms.phases : [];
        phases.forEach(function (ph) {
          hierarchyHtml +=
            '<div class="command-brief-meta" style="padding-left:12px">P' +
            (ph.ordinal || '') +
            ' ' +
            (ph.title || '') +
            ' · tier ' +
            (ph.estimated_tier || '—') +
            ' · ' +
            (ph.status || '') +
            '</div>';
        });
      });
      const tierMeta =
        tierPolicy && tierPolicy.registry_tier_policy
          ? 'Profile ' +
            (tierPolicy.registry_tier_policy.governance_profile || '—') +
            ' · goal tier ' +
            (tierPolicy.goal_tier || goal.tier || '—') +
            (tierPolicy.architect_override_visibility
              ? ' · Architect plan ' +
                (tierPolicy.architect_override_visibility.request_id || '—')
              : '')
          : 'Tier policy unavailable';
      const releaseMeta = releaseGates
        ? 'Release gates: approved ' +
          (releaseGates.approved_count || 0) +
          ' · blocked ' +
          (releaseGates.blocked_count || 0) +
          ' · pending ' +
          (releaseGates.pending_count || 0)
        : '';
      const repoMeta =
        (tierPolicy && tierPolicy.repo_path) ||
        (goal.repo_id ? 'repo ' + goal.repo_id : 'repo —');
      const budgetMeta = AnimusGovernanceHelpers.formatBudgetCaps(tierPolicy);
      const memoryFlag = goal.research && goal.research.include_research ? 'enabled' : 'disabled';
      const showApproval = AnimusGovernanceHelpers.shouldShowBreakdownApproval(goal);
      const approvalBlock = showApproval
        ? '<div class="command-brief-card" id="governanceBreakdownReview" style="margin-top:12px">' +
          '<div class="command-brief-card-title"><strong>Review breakdown</strong></div>' +
          '<div style="margin-top:8px;display:flex;flex-wrap:wrap;gap:6px">' +
          '<button type="button" class="btn btn-primary" id="governanceGoalApprove" data-breakdown-action="approve">Approve breakdown</button>' +
          '<button type="button" class="btn btn-ghost" id="governanceGoalReject" data-breakdown-action="reject">Reject breakdown</button>' +
          '</div>' +
          '<div class="command-brief-meta" id="governanceBreakdownActionResult" style="margin-top:8px"></div>' +
          '</div>'
        : '';
      host.innerHTML =
        '<div class="command-brief-card" id="governanceGoalDetailPanel">' +
        '<div class="command-brief-card-title"><strong>Goal</strong><span class="command-brief-status">' +
        AnimusGovernanceHelpers.formatGoalStatus(goal) +
        '</span></div>' +
        '<div class="command-brief-meta">' +
        (goal.statement || '') +
        '</div>' +
        '<div class="command-brief-meta">Repo: ' +
        repoMeta +
        '</div>' +
        '<div class="command-brief-meta">' +
        budgetMeta +
        '</div>' +
        '<div class="command-brief-meta">Memory: opt-in at intake · Research: ' +
        memoryFlag +
        '</div>' +
        '<div class="command-brief-meta">Milestones: ' +
        summary.milestone_count +
        ' · Phases: ' +
        summary.phase_count +
        ' · Queue: ' +
        summary.queue_count +
        ' (ready: ' +
        summary.ready_count +
        ', dispatched: ' +
        summary.dispatched_count +
        ', completed: ' +
        summary.completed_count +
        ')</div>' +
        '<div class="command-brief-meta">' +
        tierMeta +
        ' (read-only)</div>' +
        '<div class="command-brief-meta">' +
        releaseMeta +
        '</div>' +
        hierarchyHtml +
        '<table class="command-brief-table"><thead><tr><th>#</th><th>Objective</th><th>Materialization</th><th>Tier</th></tr></thead><tbody>' +
        queueRows
          .map(
            (row) =>
              '<tr><td>' +
              (row.ordinal || '') +
              '</td><td>' +
              (row.objective || '') +
              '</td><td>' +
              (row.materialization || '') +
              '</td><td>' +
              (row.tier || '') +
              '</td></tr>',
          )
          .join('') +
        '</tbody></table>' +
        AnimusGovernanceHelpers.buildResearchSectionHtml(goal, findingsPayload) +
        approvalBlock +
        '</div>';
      const repoPath =
        (tierPolicy && tierPolicy.repo_path) || (await resolveRepoPath());
      const approveBtn = $('governanceGoalApprove');
      const rejectBtn = $('governanceGoalReject');
      const actionHost = $('governanceBreakdownActionResult');
      if (approveBtn) {
        approveBtn.addEventListener('click', () =>
          void (async () => {
            if (actionHost) actionHost.textContent = 'Approving breakdown…';
            try {
              const resp = await approveGoalBreakdown(
                goalId,
                goal.breakdown_version || 1,
                repoPath,
              );
              if (actionHost) {
                actionHost.textContent = (resp.event || 'governance.goal.breakdown.approved') + ' ok';
              }
              await showGoalDetail(goalId);
            } catch (err) {
              if (actionHost) actionHost.textContent = String(err.message || err);
            }
          })(),
        );
      }
      if (rejectBtn) {
        rejectBtn.addEventListener('click', () =>
          void (async () => {
            const reason = window.prompt('Rejection reason', 'scope drift');
            if (!reason) return;
            if (actionHost) actionHost.textContent = 'Rejecting breakdown…';
            try {
              const resp = await rejectGoalBreakdown(
                goalId,
                goal.breakdown_version || 1,
                repoPath,
                reason,
              );
              if (actionHost) {
                actionHost.textContent = (resp.event || 'governance.goal.breakdown.rejected') + ' ok';
              }
              await showGoalDetail(goalId);
            } catch (err) {
              if (actionHost) actionHost.textContent = String(err.message || err);
            }
          })(),
        );
      }
    } catch (err) {
      host.innerHTML = '<div class="command-brief-err">' + String(err.message || err) + '</div>';
    }
  }

  function formatDriftBadges(driftPayload) {
    const findings = Array.isArray(driftPayload && driftPayload.findings)
      ? driftPayload.findings
      : Array.isArray(driftPayload && driftPayload.drift && driftPayload.drift.findings)
        ? driftPayload.drift.findings
        : [];
    let high = 0;
    let medium = 0;
    let low = 0;
    findings.forEach(function (item) {
      const sev = String((item && item.severity) || '').toUpperCase();
      if (sev === 'HIGH') high += 1;
      else if (sev === 'MEDIUM') medium += 1;
      else low += 1;
    });
    return { high: high, medium: medium, low: low, total: findings.length };
  }

  async function renderGovernanceProjects() {
    const host = $('governanceProjectsList');
    if (!host) return;
    host.innerHTML = '<div class="command-brief-meta">Loading registry projects…</div>';
    try {
      const data = await govFetch('registry/projects');
      const rows = Array.isArray(data.projects) ? data.projects : [];
      if (!rows.length) {
        host.innerHTML = '<div class="command-brief-meta">No registry projects.</div>';
        return;
      }
      host.innerHTML = '';
      for (const p of rows) {
        const card = document.createElement('div');
        card.className = 'command-brief-card';
        const animusId = p.animus_project_id ? ' · animus ' + p.animus_project_id.slice(0, 8) + '…' : '';
        const repos = Array.isArray(p.repos) ? p.repos : [];
        let driftHtml = '';
        if (repos.length && repos[0].repo_id) {
          try {
            const drift = await govFetch('repos/' + encodeURIComponent(repos[0].repo_id) + '/drift');
            const badges = formatDriftBadges(drift.drift || drift);
            driftHtml =
              '<div class="command-brief-meta">Drift (read-only): ' +
              '<span class="scout-license scout-license-ref">HIGH ' +
              badges.high +
              '</span> · MED ' +
              badges.medium +
              ' · LOW ' +
              badges.low +
              ' · total ' +
              badges.total +
              '</div>';
          } catch (_err) {
            driftHtml = '<div class="command-brief-meta">Drift: unavailable</div>';
          }
        }
        card.innerHTML =
          '<div class="command-brief-card-title">' +
          '<strong>' + (p.display_name || p.slug || p.project_id) + '</strong>' +
          '<span class="command-brief-status">' + (p.status || 'active') + '</span></div>' +
          '<div class="command-brief-meta">' + (p.slug || '') + animusId + '</div>' +
          driftHtml +
          '<ul class="command-brief-list">' +
          repos.map(function (r) { return '<li>' + (r.repo_path || r.repo_id) + '</li>'; }).join('') +
          '</ul>';
        host.appendChild(card);
      }
    } catch (err) {
      host.innerHTML = '<div class="command-brief-err">' + String(err.message || err) + '</div>';
    }
  }

  async function renderGovernanceRuns() {
    const host = $('governanceRunsDetail');
    const listHost = $('governanceRunsList');
    if (!listHost || !host) return;
    listHost.innerHTML = '<div class="command-brief-meta">Loading runs…</div>';
    host.innerHTML = '';
    try {
      const data = await govFetch('runs?project_id=' + encodeURIComponent(PLATFORM_PROJECT_ID));
      const runs = Array.isArray(data.runs) ? data.runs : [];
      listHost.innerHTML = '';
      if (!runs.length) {
        listHost.innerHTML = '<div class="command-brief-meta">No governance runs yet.</div>';
        return;
      }
      for (const run of runs) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'btn btn-ghost';
        btn.style.margin = '4px 0';
        btn.textContent = (run.run_id || '').slice(0, 8) + '… · ' + (run.status || '?');
        btn.addEventListener('click', () => void showRunDetail(run.run_id || CANONICAL_RUN_ID));
        listHost.appendChild(btn);
      }
      const canonical = runs.find((r) => r.run_id === CANONICAL_RUN_ID);
      await showRunDetail((canonical && canonical.run_id) || runs[0].run_id);
    } catch (err) {
      listHost.innerHTML = '<div class="command-brief-err">' + String(err.message || err) + '</div>';
    }
  }

  async function showRunDetail(runId) {
    const host = $('governanceRunsDetail');
    if (!host || !runId) return;
    host.innerHTML = '<div class="command-brief-meta">Loading run ' + runId.slice(0, 8) + '…</div>';
    try {
      const q = 'project_id=' + encodeURIComponent(PLATFORM_PROJECT_ID);
      const project = await govFetch('registry/projects/' + encodeURIComponent(PLATFORM_PROJECT_ID));
      const repos = Array.isArray(project.repos) ? project.repos : [];
      const repoId = repos.length ? repos[0].repo_id : '';
      const [timeline, verification, release, evidenceCompleteness, validationAgg] = await Promise.all([
        govFetch('runs/' + encodeURIComponent(runId) + '/timeline'),
        govFetch('runs/' + encodeURIComponent(runId) + '/verification').catch(() => null),
        govFetch('runs/' + encodeURIComponent(runId) + '/release').catch(() => null),
        repoId
          ? govFetch(
              'repos/' +
                encodeURIComponent(repoId) +
                '/runs/' +
                encodeURIComponent(runId) +
                '/evidence-completeness',
            ).catch(() => null)
          : Promise.resolve(null),
        govFetch('projects/' + encodeURIComponent(PLATFORM_PROJECT_ID) + '/validation').catch(
          () => null,
        ),
      ]);
      const events = Array.isArray(timeline.events) ? timeline.events : [];
      host.innerHTML =
        '<div class="command-brief-card">' +
        '<div class="command-brief-card-title"><strong>Run</strong><span class="command-brief-status">' +
        runId +
        '</span></div>' +
        '<div class="command-brief-meta">Timeline events: ' +
        events.length +
        '</div>' +
        '<ul class="command-brief-list">' +
        events
          .map(
            (ev) =>
              '<li>seq ' +
              ev.seq +
              ' · ' +
              (ev.event_type || '') +
              '</li>',
          )
          .join('') +
        '</ul>' +
        (verification
          ? '<div class="command-brief-meta">Verification blocking: ' +
            !!verification.blocking +
            '</div>'
          : '') +
        (release
          ? '<div class="command-brief-meta">Release: ' + (release.status || '—') + '</div>'
          : '') +
        (evidenceCompleteness
          ? '<div class="command-brief-meta">Evidence complete: ' +
            (evidenceCompleteness.complete ? 'yes' : 'no') +
            ' · present ' +
            (Array.isArray(evidenceCompleteness.present)
              ? evidenceCompleteness.present.join(', ')
              : '—') +
            (Array.isArray(evidenceCompleteness.missing) && evidenceCompleteness.missing.length
              ? ' · missing ' + evidenceCompleteness.missing.join(', ')
              : '') +
            '</div>'
          : '') +
        (validationAgg
          ? '<div class="command-brief-meta">Project validation: ' +
            validationAgg.run_count +
            ' runs · blocking ' +
            validationAgg.blocking_count +
            '</div>'
          : '') +
        '</div>';
    } catch (err) {
      host.innerHTML = '<div class="command-brief-err">' + String(err.message || err) + '</div>';
    }
  }

  async function renderGoalRunner() {
    ensureGoalRunnerPanel();
    const controlsHost = $('governanceGoalRunnerControls');
    if (!controlsHost) return;
    controlsHost.innerHTML = '<div class="command-brief-meta">Loading Goal Runner…</div>';
    try {
      const data = await govFetch('projects');
      const projects = Array.isArray(data.projects) ? data.projects : [];
      const options = projects
        .map(function (project) {
          const selected =
            project.project_id ===
            (_goalRunnerState.selectedProjectId || AnimusGoalRunnerHelpers.ANIMA_LINUX_PROJECT_ID)
              ? ' selected'
              : '';
          return (
            '<option value="' +
            project.project_id +
            '"' +
            selected +
            '>' +
            AnimusGoalRunnerHelpers.formatProjectOptionLabel(project) +
            '</option>'
          );
        })
        .join('');
      controlsHost.innerHTML =
        '<div class="command-brief-card" id="governanceGoalRunnerPanel">' +
        '<div class="command-brief-card-title"><strong>Goal Runner</strong></div>' +
        '<label class="command-brief-meta">Project<br>' +
        '<select data-goal-runner-field="project_id" id="governanceGoalRunnerProject">' +
        options +
        '</select></label>' +
        '<div class="command-brief-meta" id="governanceGoalRunnerProjectMeta"></div>' +
        '<label class="command-brief-meta">Goal statement<br>' +
        '<textarea data-goal-runner-field="statement" id="governanceGoalRunnerStatement" rows="4" style="width:100%"></textarea></label>' +
        '<label class="command-brief-meta">Research mode ' +
        '<select data-goal-runner-field="research_mode" id="governanceGoalRunnerResearchMode">' +
        '<option value="off">off</option><option value="light">light</option><option value="standard">standard</option><option value="deep">deep</option>' +
        '</select></label>' +
        '<label class="command-brief-meta">Run mode ' +
        '<select data-goal-runner-field="run_mode" id="governanceGoalRunnerRunMode">' +
        '<option value="draft_only">Research + plan only</option>' +
        '<option value="approve_only">Research + plan + approve</option>' +
        '<option value="run">Full run</option>' +
        '</select></label>' +
        '<label class="command-brief-meta">Approval mode ' +
        '<select data-goal-runner-field="approval_mode" id="governanceGoalRunnerApprovalMode">' +
        '<option value="manual_approval">manual_approval</option>' +
        '<option value="auto_approve_if_policy_clean">auto_approve_if_policy_clean</option>' +
        '<option value="auto_run_if_policy_clean">auto_run_if_policy_clean</option>' +
        '</select></label>' +
        '<label class="command-brief-meta">Budget max runs <input data-goal-runner-field="max_run_count" id="governanceGoalRunnerMaxRuns" type="number" min="1"></label>' +
        '<label class="command-brief-meta">Budget wall-clock hours <input data-goal-runner-field="max_wall_clock_hours" id="governanceGoalRunnerMaxHours" type="number" min="0.1" step="0.1"></label>' +
        '<div class="command-brief-meta" id="governanceGoalRunnerWarnings"></div>' +
        '<div style="margin-top:8px;display:flex;flex-wrap:wrap;gap:6px">' +
        '<button type="button" class="btn btn-primary" id="governanceGoalRunnerRun">Run</button>' +
        '<button type="button" class="btn btn-ghost" id="governanceGoalRunnerRefresh">Refresh</button>' +
        '</div>' +
        '<div class="command-brief-meta" id="governanceGoalRunnerResult" style="margin-top:8px"></div>' +
        '</div>';
      const projectSelect = $('governanceGoalRunnerProject');
      if (projectSelect) {
        projectSelect.addEventListener('change', () =>
          void (async () => {
            await loadGoalRunnerProjectProfile(projectSelect.value);
            updateGoalRunnerWarnings();
          })(),
        );
      }
      ['governanceGoalRunnerResearchMode', 'governanceGoalRunnerRunMode', 'governanceGoalRunnerApprovalMode'].forEach(
        function (id) {
          const el = $(id);
          if (el) {
            el.addEventListener('change', updateGoalRunnerWarnings);
          }
        },
      );
      const initialProject =
        (_goalRunnerState.selectedProjectId || AnimusGoalRunnerHelpers.ANIMA_LINUX_PROJECT_ID);
      await loadGoalRunnerProjectProfile(initialProject);
      updateGoalRunnerWarnings();
      const runBtn = $('governanceGoalRunnerRun');
      if (runBtn) {
        runBtn.addEventListener('click', () => void submitProjectGoalRun());
      }
      const refreshBtn = $('governanceGoalRunnerRefresh');
      if (refreshBtn) {
        refreshBtn.addEventListener('click', () => void refreshGoalRunnerView());
      }
      if (_goalRunnerState.lastResponse) {
        await refreshGoalRunnerView();
      }
    } catch (err) {
      controlsHost.innerHTML = '<div class="command-brief-err">' + String(err.message || err) + '</div>';
    }
  }

  function readGoalRunnerForm() {
    const projectId = ($('governanceGoalRunnerProject') || {}).value || '';
    return {
      projectId: projectId,
      statement: ($('governanceGoalRunnerStatement') || {}).value || '',
      researchMode: ($('governanceGoalRunnerResearchMode') || {}).value || 'light',
      runMode: ($('governanceGoalRunnerRunMode') || {}).value || 'draft_only',
      approvalMode: ($('governanceGoalRunnerApprovalMode') || {}).value || 'manual_approval',
      maxRunCount: ($('governanceGoalRunnerMaxRuns') || {}).value || '',
      maxWallHours: ($('governanceGoalRunnerMaxHours') || {}).value || '',
      goalSizeHint: 'S',
    };
  }

  async function loadGoalRunnerProjectProfile(projectId) {
    if (!projectId) return;
    _goalRunnerState.selectedProjectId = projectId;
    const profile = await govFetch('projects/' + encodeURIComponent(projectId));
    _goalRunnerState.selectedProfile = profile;
    const metaHost = $('governanceGoalRunnerProjectMeta');
    if (metaHost) {
      metaHost.textContent =
        'Profile default research: ' +
        (profile.research_mode || '—') +
        ' · approval: ' +
        (profile.approval_mode || '—') +
        ' · validator: ' +
        (profile.default_validator || '—');
    }
    const researchSelect = $('governanceGoalRunnerResearchMode');
    if (researchSelect && profile.research_mode) {
      researchSelect.value = profile.research_mode;
    }
    const approvalSelect = $('governanceGoalRunnerApprovalMode');
    if (approvalSelect) {
      approvalSelect.value = profile.approval_mode || 'manual_approval';
    }
    const runModeSelect = $('governanceGoalRunnerRunMode');
    if (runModeSelect && !runModeSelect.dataset.userChanged) {
      runModeSelect.value = 'draft_only';
    }
    const maxRuns = $('governanceGoalRunnerMaxRuns');
    if (maxRuns && profile.budget_defaults) {
      maxRuns.value =
        profile.budget_defaults.max_run_count != null
          ? String(profile.budget_defaults.max_run_count)
          : '';
    }
    const maxHours = $('governanceGoalRunnerMaxHours');
    if (maxHours && profile.budget_defaults) {
      maxHours.value =
        profile.budget_defaults.max_wall_clock_hours != null
          ? String(profile.budget_defaults.max_wall_clock_hours)
          : '';
    }
  }

  function updateGoalRunnerWarnings() {
    const host = $('governanceGoalRunnerWarnings');
    if (!host) return;
    const form = readGoalRunnerForm();
    const profile = _goalRunnerState.selectedProfile;
    const warnings = [];
    if (AnimusGoalRunnerHelpers.shouldShowResearchRequiredWarning(profile, form.researchMode)) {
      warnings.push('Research is required for this project unless skip is policy-approved.');
    }
    if (AnimusGoalRunnerHelpers.shouldShowAutoRunWarning(form.approvalMode)) {
      warnings.push('Will start Driver if policy/preflight pass.');
    }
    if (AnimusGoalRunnerHelpers.shouldShowRunModeWarning(form.runMode)) {
      warnings.push('Full run mode may start Driver execution when policy allows.');
    }
    host.innerHTML = warnings.length
      ? warnings.map(function (line) {
          return '<div class="command-brief-meta goal-runner-warning">' + line + '</div>';
        }).join('')
      : '';
  }

  async function submitProjectGoalRun() {
    const resultHost = $('governanceGoalRunnerResult');
    const form = readGoalRunnerForm();
    const validation = AnimusGoalRunnerHelpers.validateGoalStatement(
      form.statement,
      form.projectId,
      _goalRunnerState.running,
    );
    if (!validation.ok) {
      if (resultHost) resultHost.textContent = validation.error;
      return;
    }
    const payload = AnimusGoalRunnerHelpers.buildGoalRunPayload(form, _goalRunnerState.selectedProfile);
    const postBody = {
      statement: payload.statement,
      run_mode: payload.run_mode,
      goal_size_hint: payload.goal_size_hint,
      research_mode: payload.research_mode,
      approval_mode: payload.approval_mode,
      budget_override: payload.budget_override,
    };
    if (resultHost) resultHost.textContent = 'Submitting goal run…';
    _goalRunnerState.running = true;
    try {
      const response = await govFetch(AnimusGoalRunnerHelpers.goalRunPostPath(form.projectId), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(postBody),
      });
      _goalRunnerState.lastResponse = response;
      if (resultHost) {
        resultHost.textContent =
          'goal_run_id ' +
          (response.goal_run_id || '—') +
          ' · goal_id ' +
          (response.goal_id || '—') +
          ' · status ' +
          (response.status || '—');
      }
      await refreshGoalRunnerView();
    } catch (err) {
      if (resultHost) resultHost.textContent = String(err.message || err);
    } finally {
      _goalRunnerState.running = false;
    }
  }

  async function refreshGoalRunnerView() {
    const response = _goalRunnerState.lastResponse;
    const summaryHost = $('governanceGoalRunnerSummary');
    const timelineHost = $('governanceGoalRunnerTimeline');
    const panelsHost = $('governanceGoalRunnerPanels');
    if (!response || !summaryHost || !timelineHost || !panelsHost) {
      if (summaryHost && !response) {
        summaryHost.innerHTML = '<div class="command-brief-meta">Run a goal to see lifecycle output.</div>';
      }
      return;
    }
    const projectId = response.project_id || _goalRunnerState.selectedProjectId;
    const goalId = response.goal_id;
    let goalDetail = null;
    let queuePayload = null;
    let driverPayload = null;
    let goalRunProjection = null;
    try {
      const fetches = [
        govFetch('goals/' + encodeURIComponent(goalId) + '?project_id=' + encodeURIComponent(projectId)),
        govFetch('goals/' + encodeURIComponent(goalId) + '/queue'),
        govFetch('driver/status?workspace_id=' + encodeURIComponent(WORKSPACE_ID)),
      ];
      if (response.goal_run_id) {
        fetches.push(
          govFetch('goal-runs/' + encodeURIComponent(response.goal_run_id)).catch(function () {
            return null;
          }),
        );
      }
      const results = await Promise.all(fetches);
      goalDetail = results[0];
      queuePayload = results[1];
      driverPayload = AnimusGovernanceHelpers.parseDriverStatus(results[2]);
      goalRunProjection = results[3] || null;
    } catch (_err) {
      goalDetail = goalDetail || {};
    }
    summaryHost.innerHTML =
      '<div class="command-brief-card">' +
      '<div class="command-brief-card-title"><strong>Run summary</strong></div>' +
      '<div class="command-brief-meta">goal_run_id: ' +
      (response.goal_run_id || '—') +
      ' · goal_id: ' +
      (goalId || '—') +
      ' · status: ' +
      (response.status || '—') +
      '</div>' +
      '<div class="command-brief-meta">research: ' +
      ((response.research && response.research.status) || '—') +
      ' · breakdown: ' +
      ((response.breakdown && response.breakdown.status) || '—') +
      ' · driver started: ' +
      ((response.driver && response.driver.started) ? 'yes' : 'no') +
      '</div>' +
      '<div class="command-brief-meta">evidence refs: ' +
      (Array.isArray(response.evidence_refs) ? response.evidence_refs.length : 0) +
      '</div></div>';
    const timelineState =
      (goalRunProjection && goalRunProjection.state) || response.status || 'created';
    timelineHost.innerHTML =
      '<div class="command-brief-card"><div class="command-brief-card-title"><strong>Timeline</strong></div>' +
      AnimusGoalRunnerHelpers.buildTimelineHtml(timelineState, response) +
      '</div>';
    panelsHost.innerHTML =
      '<div class="command-brief-card"><div class="command-brief-card-title"><strong>Research</strong></div>' +
      AnimusGoalRunnerHelpers.buildResearchPanelHtml(response, goalDetail) +
      '</div>' +
      '<div class="command-brief-card" style="margin-top:12px"><div class="command-brief-card-title"><strong>Breakdown</strong></div>' +
      AnimusGoalRunnerHelpers.buildBreakdownPanelHtml(
        response,
        queuePayload,
        _goalRunnerState.selectedProfile,
      ) +
      '</div>' +
      '<div class="command-brief-card" style="margin-top:12px"><div class="command-brief-card-title"><strong>Execution</strong></div>' +
      AnimusGoalRunnerHelpers.buildExecutionPanelHtml(
        response,
        driverPayload,
        response.run_mode || readGoalRunnerForm().runMode,
      ) +
      '</div>' +
      '<div class="command-brief-card" style="margin-top:12px"><div class="command-brief-card-title"><strong>Blocker / Recovery</strong></div>' +
      AnimusGoalRunnerHelpers.buildBlockerRecoveryPanelHtml(response, goalRunProjection) +
      '</div>' +
      '<div class="command-brief-card" style="margin-top:12px"><div class="command-brief-card-title"><strong>Memory</strong></div>' +
      AnimusGoalRunnerHelpers.buildMemoryPanelHtml(response) +
      '</div>' +
      '<div class="command-brief-card" style="margin-top:12px"><div class="command-brief-card-title"><strong>Outcome report</strong></div>' +
      AnimusGoalRunnerHelpers.buildOutcomePanelHtml(response, goalDetail) +
      '</div>';
  }

  function wireGovernanceTabsOnce() {
    const bar = $('governanceTabBar');
    if (!bar || bar.dataset.wired) return;
    ensureGoalsPanel();
    ensureGoalRunnerPanel();
    ensureQueuePanel();
    ensureDriverPanel();
    const briefPanel = $('governancePanelBrief');
    if (briefPanel && !$('governanceBriefMemory')) {
      const memoryCard = document.createElement('div');
      memoryCard.className = 'command-brief-card';
      memoryCard.style.marginTop = '12px';
      memoryCard.innerHTML =
        '<div class="command-brief-card-title"><strong>Memory outcomes</strong></div>' +
        '<div id="governanceBriefMemory"></div>';
      briefPanel.appendChild(memoryCard);
    }
    bar.dataset.wired = '1';
    bar.querySelectorAll('[data-governance-tab]').forEach((btn) => {
      btn.addEventListener('click', () => setGovernanceTab(btn.getAttribute('data-governance-tab') || 'brief'));
    });
  }

  window.AnimusGovernanceHub = {
    activateTab: setGovernanceTab,
    refreshProjects: renderGovernanceProjects,
    refreshGoals: renderGovernanceGoals,
    refreshGoalRunner: renderGoalRunner,
    refreshDriver: renderGovernanceDriver,
    refreshRuns: renderGovernanceRuns,
    refreshQueue: renderGovernanceQueue,
    refreshBriefExtras: renderGovernanceBriefExtras,
    wire: wireGovernanceTabsOnce,
    helpers: AnimusGovernanceHelpers,
    goalRunnerHelpers: AnimusGoalRunnerHelpers,
    submitProjectGoalRun: submitProjectGoalRun,
    refreshGoalRunnerView: refreshGoalRunnerView,
    driverControl: driverControl,
    signOffGoal: signOffGoal,
  };

  document.addEventListener('DOMContentLoaded', wireGovernanceTabsOnce);
})();
