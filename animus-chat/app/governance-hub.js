/** Governance hub — BFF-backed Registry / Runs / Goals / Driver views (Command Brief overlay tabs). */

/** @typedef {{ goal_id: string, status?: string, statement?: string }} GoalRow */

const AnimusGovernanceHelpers = {
  parseGoalsList(data) {
    return Array.isArray(data && data.goals) ? data.goals : [];
  },
  formatGoalStatus(goal) {
    return String((goal && goal.status) || 'unknown');
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

(function () {
  const PLATFORM_PROJECT_ID = '260c61b1-f774-5493-8ff3-97e0d750f58c';
  const WORKSPACE_ID = 'a6acfd2b-3195-5085-aae8-ccb93fc7a02b';
  const CANONICAL_RUN_ID = 'a1dfc5a6-a1b3-4bc8-86b9-a7910f0aaae1';
  let _cachedRepoPath = null;

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
    const tabs = ['brief', 'projects', 'goals', 'driver', 'runs'];
    for (const name of tabs) {
      const panel = $('governancePanel' + name.charAt(0).toUpperCase() + name.slice(1));
      const btn = $('governanceTab' + name.charAt(0).toUpperCase() + name.slice(1));
      if (panel) panel.hidden = name !== tab;
      if (btn) btn.classList.toggle('active', name === tab);
    }
    if (tab === 'projects') void renderGovernanceProjects();
    if (tab === 'goals') void renderGovernanceGoals();
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
      '<div class="command-brief-cards" id="governanceGoalsList"></div>' +
      '<div id="governanceGoalsDetail"></div>';
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

  async function renderGovernanceGoals() {
    const listHost = $('governanceGoalsList');
    const detailHost = $('governanceGoalsDetail');
    if (!listHost || !detailHost) return;
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
      host.innerHTML =
        '<div class="command-brief-card">' +
        '<div class="command-brief-card-title"><strong>Goal</strong><span class="command-brief-status">' +
        AnimusGovernanceHelpers.formatGoalStatus(goal) +
        '</span></div>' +
        '<div class="command-brief-meta">' +
        (goal.statement || '') +
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
        '</div>';
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

  function wireGovernanceTabsOnce() {
    const bar = $('governanceTabBar');
    if (!bar || bar.dataset.wired) return;
    ensureGoalsPanel();
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
    refreshDriver: renderGovernanceDriver,
    refreshRuns: renderGovernanceRuns,
    refreshQueue: renderGovernanceQueue,
    refreshBriefExtras: renderGovernanceBriefExtras,
    wire: wireGovernanceTabsOnce,
    helpers: AnimusGovernanceHelpers,
    driverControl: driverControl,
    signOffGoal: signOffGoal,
  };

  document.addEventListener('DOMContentLoaded', wireGovernanceTabsOnce);
})();
