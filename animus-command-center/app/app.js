/* Dedicated Command Center shell (D-140) + governance API integration (D-141). */
var CCGoalRunnerHelpers = {
  ANIMA_LINUX_PROJECT_ID: 'c9eebdd2-a087-5eae-a074-77b5572fe7b5',
  GOAL_STATEMENT_MAX_LEN: 8000,
  GOAL_STATEMENT_HELP:
    'Describe the outcome you want — not implementation steps. Example: ' +
    '"Add retry logic to the intake API with tests." Scout research and Oracle ' +
    'breakdown use this statement; artifacts are stored under the target repo ' +
    '.evidence/goals/{goal_id}/.',
  RUN_MODE_LABELS: {
    draft_only: 'Plan only (research + breakdown)',
    approve_only: 'Plan + approve breakdown',
    run: 'Full run (plan through Driver execution)'
  },
  RUN_MODE_BUTTON: {
    draft_only: 'Run plan only',
    approve_only: 'Run plan + approve',
    run: 'Run full goal'
  },
  APPROVAL_HELP:
    'Manual: you approve the breakdown here when status is pending approval. ' +
    'Auto-approve: policy-clean breakdowns approve automatically. ' +
    'Auto-run: also starts Driver when idle and policy allows.',
  RESEARCH_HELP:
    'Scout writes scout_research_v1.json under the target repo. Oracle reads it ' +
    'when decomposing. Draft/plan runs persist research for a later full run on ' +
    'the same goal.',
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
  USER_WORKFLOW: [
    {
      id: 'project',
      label: 'Pick a project',
      hint: 'Choose which registered codebase this work applies to.'
    },
    {
      id: 'goal',
      label: 'Describe your goal',
      hint: 'State the outcome you want — not step-by-step instructions.'
    },
    {
      id: 'approve',
      label: 'Approve the plan',
      hint: 'Review the generated breakdown and approve when it looks right.'
    },
    {
      id: 'execute',
      label: 'Driver executes',
      hint: 'The autonomous agent works through approved tasks in your repo.'
    },
    {
      id: 'signoff',
      label: 'Sign off',
      hint: 'Confirm the work is complete when results look good.'
    }
  ],
  USER_PHASES: [
    { label: 'Submitted', match: /^(created|preflight)/ },
    { label: 'Researching', match: /research|decompos/ },
    { label: 'Awaiting your approval', match: /pending_approval|awaiting_approval|breakdown_review/ },
    { label: 'Running', match: /approved|running|dispatch|entry_|driver_start/ },
    { label: 'Ready to sign off', match: /pending_completion/ },
    { label: 'Complete', match: /completed|released/ },
    { label: 'Needs attention', match: /blocked|operator_required|fail|halt|error/ }
  ],
  mapUserPhaseIndex: function (state) {
    var normalized = String(state || '').trim().toLowerCase();
    if (normalized === 'pending_approval') normalized = 'awaiting_approval';
    var i;
    for (i = 0; i < CCGoalRunnerHelpers.USER_PHASES.length; i += 1) {
      if (CCGoalRunnerHelpers.USER_PHASES[i].match.test(normalized)) return i;
    }
    return 0;
  },
  buildSimpleProgressHtml: function (state) {
    var activeIndex = CCGoalRunnerHelpers.mapUserPhaseIndex(state);
    return (
      '<ol class="cc-progress-steps">' +
      CCGoalRunnerHelpers.USER_PHASES.map(function (phase, index) {
        var cls = index < activeIndex ? ' cc-progress-done'
          : index === activeIndex ? ' cc-progress-active' : ' cc-progress-next';
        return '<li class="cc-progress-step' + cls + '">' +
          '<span class="cc-progress-dot" aria-hidden="true"></span>' +
          '<span class="cc-progress-label">' + phase.label + '</span></li>';
      }).join('') +
      '</ol>'
    );
  },
  inferWorkflowStep: function (ctx) {
    ctx = ctx || {};
    var goals = ctx.goals || [];
    var selectedGoal = ctx.selectedGoal;
    var status = selectedGoal
      ? String(selectedGoal.display_status || selectedGoal.status || '').toLowerCase()
      : '';
    if (/pending_approval|awaiting_approval/.test(status)) return 2;
    if (/pending_completion/.test(status)) return 4;
    if (/running|approved|dispatch|entry_/.test(status)) return 3;
    if (selectedGoal) return 1;
    if (goals.some(function (g) {
      return /pending_approval|pending_completion/.test(String(g.status || ''));
    })) return 2;
    if (!ctx.projectId) return 0;
    return 1;
  },
  GOAL_FILTER_TABS: [
    { id: 'pending_review', label: 'Pending review' },
    { id: 'pending_completion', label: 'Pending completion' },
    { id: 'active', label: 'Active' },
    { id: 'stale', label: 'Stale' },
    { id: 'complete', label: 'Complete' }
  ],
  isGoalHidden: function (goal) {
    var s = String((goal && (goal.display_status || goal.status)) || '').toLowerCase();
    return /cancelled|canceled|rejected|removed|archived/.test(s);
  },
  goalFilterBucket: function (goal) {
    if (goal && goal.freshness === 'stale') return 'stale';
    var s = String((goal && (goal.display_status || goal.status)) || '').toLowerCase();
    if (/pending_approval|awaiting_approval/.test(s)) return 'pending_review';
    if (s === 'pending_completion') return 'pending_completion';
    if (/completed|released|halted|failed|blocked/.test(s)) return 'complete';
    return 'active';
  },
  goalProgressPct: function (goal) {
    var s = String((goal && (goal.display_status || goal.status)) || '').toLowerCase();
    if (/completed|released/.test(s)) return 100;
    if (/pending_completion/.test(s)) return 90;
    if (/running|dispatch|entry_|approved|active/.test(s)) return 65;
    if (/pending_approval|awaiting_approval/.test(s)) return 45;
    if (/research|decompos|preflight/.test(s)) return 30;
    if (/blocked|halt|fail|error|operator/.test(s)) return 100;
    return 15;
  },
  goalProgressColor: function (goal) {
    var s = String((goal && (goal.display_status || goal.status)) || '').toLowerCase();
    if (/completed|released/.test(s)) return '#22c55e';
    if (/blocked|halt|fail|error|operator/.test(s)) return '#ef4444';
    if (/pending_approval|pending_completion/.test(s)) return '#f59e0b';
    return '#7c3aed';
  },
  runsForGoal: function (goalId, runs, goals) {
    var gid = String(goalId || '');
    if (!gid) return [];
    var goalRow = (goals || []).find(function (g) {
      return String(g.goal_id || '') === gid;
    });
    var goalCorrelation = goalRow && goalRow.correlation_id ? String(goalRow.correlation_id) : '';
    return (runs || []).filter(function (r) {
      if (r.goal_id && String(r.goal_id) === gid) return true;
      var correlation = String(r.correlation_id || '');
      var requestId = String(r.request_id || '');
      var runId = String(r.run_id || '');
      if (correlation === gid || requestId === gid || runId === gid) return true;
      if (correlation.indexOf(gid) >= 0 || requestId.indexOf(gid) >= 0) return true;
      if (goalCorrelation && (correlation === goalCorrelation || requestId === goalCorrelation)) {
        return true;
      }
      return false;
    });
  },
  validateGoalStatement: function (statement, projectId, alreadyRunning, projectGoals) {
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
    var normalized = text.toLowerCase().replace(/\s+/g, ' ');
    var duplicate = (projectGoals || []).find(function (g) {
      if (CCGoalRunnerHelpers.isGoalHidden(g)) return false;
      var gs = String(g.statement || '').trim().toLowerCase().replace(/\s+/g, ' ');
      if (gs !== normalized) return false;
      var status = String(g.display_status || g.status || '').toLowerCase();
      return /pending|active|approved|decompos|proposed/.test(status);
    });
    if (duplicate) {
      return {
        ok: false,
        error: 'An open goal with this statement already exists. Open it from the list instead of creating a duplicate.',
        existingGoalId: duplicate.goal_id
      };
    }
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
  buildGoalIntakePayload: function (form, profile, projectId, repoPath) {
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
      repo_path: repoPath,
      project_id: projectId,
      include_memory: !!form.includeMemory,
      include_research: !!form.includeResearch,
      goal_size_hint: form.goalSizeHint || 'S',
      tier_expectation: 'release',
      source: 'human',
      budget_override: {
        max_run_count: maxRunCount,
        max_wall_clock_hours: maxWallHours
      },
      human_checkpoints: {
        breakdown_approval_required: true,
        dispatch_opt_in_required: true,
        sign_off_required_at_completion: true
      }
    };
  },
  goalIntakePostPath: function () {
    return 'goals';
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
  buildBreakdownPanelHtml: function (response, queuePayload, profile, milestonesPayload, goalDetail) {
    var breakdown = (response && response.breakdown) || {};
    var goal = goalDetail || {};
    var queue = Array.isArray(queuePayload && queuePayload.queue_entries) ? queuePayload.queue_entries : [];
    var validator = (profile && profile.default_validator) || '—';
    var approvalState = goal.approval_state || (queuePayload && queuePayload.approval_state) || '—';
    var dispatchable = goal.dispatchable != null ? String(goal.dispatchable) : (
      queuePayload && queuePayload.dispatchable != null ? String(queuePayload.dispatchable) : '—'
    );
    var nonDispatch = goal.non_dispatch_reason || (queuePayload && queuePayload.non_dispatch_reason) || '—';
    var tiers = goal.proposed_tiers || (queuePayload && queuePayload.proposed_tiers) || [];
    var version = goal.breakdown_version || breakdown.version || '—';
    var hierarchy = CCGoalRunnerHelpers.buildBreakdownHierarchyHtml(milestonesPayload, queue);
    return (
      '<div class="cc-meta-line">breakdown_version: ' + version +
      ' · approval: ' + approvalState +
      ' · dispatchable: ' + dispatchable +
      (nonDispatch && nonDispatch !== '—' ? ' · blocked: ' + nonDispatch : '') + '</div>' +
      '<div class="cc-meta-line">proposed tiers: ' +
      (tiers.length ? tiers.join(', ') : '—') +
      ' · queue entries: ' + queue.length + ' · validator: ' + validator + '</div>' +
      hierarchy
    );
  },
  buildBreakdownHierarchyHtml: function (milestonesPayload, queueEntries) {
    var milestones = (milestonesPayload && milestonesPayload.milestones) || [];
    var queue = queueEntries || [];
    if (!milestones.length && !queue.length) {
      return '<div class="cc-meta-line">No breakdown hierarchy projected yet.</div>';
    }
    var milestoneHtml = milestones.length
      ? '<ul class="cc-breakdown-tree">' + milestones.map(function (m) {
          var phases = m.phases || [];
          return (
            '<li><strong>M' + (m.ordinal != null ? m.ordinal : '—') + ': ' +
            String(m.title || 'milestone') + '</strong> (' + String(m.status || '—') + ')' +
            (phases.length
              ? '<ul>' + phases.map(function (p) {
                  return '<li>P' + (p.ordinal != null ? p.ordinal : '—') + ': ' +
                    String(p.title || p.scope_summary || 'phase') +
                    ' · tier ' + String(p.estimated_tier || '—') +
                    ' · ' + String(p.status || '—') + '</li>';
                }).join('') + '</ul>'
              : '') +
            '</li>'
          );
        }).join('') + '</ul>'
      : '';
    var queueHtml = queue.length
      ? '<div class="cc-meta-line cc-breakdown-queue-head">Queue entries</div><ul class="cc-breakdown-tree">' +
        queue.map(function (entry) {
          var releaseLine = entry.release_status ? ' · release: ' + entry.release_status : '';
          var commitLine = entry.commit_sha ? ' · commit: ' + String(entry.commit_sha).slice(0, 12) : '';
          var runLine = entry.run_id ? ' · run: ' + String(entry.run_id).slice(0, 12) + '…' : '';
          return '<li>#' + String(entry.ordinal != null ? entry.ordinal : '—') +
            ' · tier ' + String(entry.tier || '—') +
            ' · ' + String(entry.materialization || '—') +
            runLine + releaseLine + commitLine +
            ' · ' + String(entry.objective || '').slice(0, 120) + '</li>';
        }).join('') + '</ul>'
      : '';
    return milestoneHtml + queueHtml;
  },
  computeDriverLaunchGate: function (ctx) {
    ctx = ctx || {};
    var readiness = ctx.readiness || null;
    if (readiness && readiness.ready === false) {
      return {
        ok: false,
        reason: readiness.display_reason ||
          (readiness.blocking_reason ? String(readiness.blocking_reason).replace(/_/g, ' ') : 'Launch blocked')
      };
    }
    if (readiness && readiness.ready === true) {
      return { ok: true, reason: '' };
    }
    var goalDetail = ctx.goalDetail || {};
    var profile = ctx.profile || {};
    var connected = ctx.connected !== false;
    var dirty = profile.dirty_tree || {};
    var status = String(goalDetail.display_status || goalDetail.status || '').toLowerCase();
    if (!connected) {
      return { ok: false, reason: 'Governance API offline — refresh and retry.' };
    }
    if (/rejected|cancelled|canceled/.test(status)) {
      return { ok: false, reason: 'Breakdown rejected — goal is not dispatchable.' };
    }
    if (/pending_approval|awaiting_approval|proposed|decompos/.test(status)) {
      return { ok: false, reason: 'Approve the breakdown before starting the Driver.' };
    }
    if (goalDetail.dispatchable === false) {
      return {
        ok: false,
        reason: goalDetail.non_dispatch_reason
          ? String(goalDetail.non_dispatch_reason).replace(/_/g, ' ')
          : 'Goal is not dispatchable yet.'
      };
    }
    if (dirty.blocking) {
      return {
        ok: false,
        reason: 'Repo has a blocking dirty tree — clean or classify before dispatch.'
      };
    }
    return { ok: true, reason: '' };
  },
  computeSignOffGate: function (ctx) {
    ctx = ctx || {};
    var readiness = ctx.readiness || null;
    if (readiness && readiness.ready === false) {
      return {
        ok: false,
        reason: readiness.display_reason ||
          (readiness.blocking_reason ? String(readiness.blocking_reason).replace(/_/g, ' ') : 'Sign-off blocked')
      };
    }
    if (readiness && readiness.ready === true) {
      return { ok: true, reason: '' };
    }
    var goalDetail = ctx.goalDetail || {};
    var status = String(goalDetail.display_status || goalDetail.status || '').toLowerCase();
    if (status !== 'pending_completion') {
      return { ok: false, reason: 'Goal is not pending completion.' };
    }
    return { ok: false, reason: 'Sign-off readiness not loaded — refresh and retry.' };
  },
  buildSignOffReadinessPanelHtml: function (readiness, queueDetail) {
    if (!readiness) {
      return '<div class="cc-meta-line">Sign-off readiness: not loaded</div>';
    }
    var ready = readiness.ready === true;
    var reason = readiness.display_reason ||
      (readiness.blocking_reason ? String(readiness.blocking_reason).replace(/_/g, ' ') : '—');
    var lines = [
      'sign-off ready: ' + (ready ? 'yes' : 'no'),
      'blocking reason: ' + reason
    ];
    var entries = (queueDetail && queueDetail.queue_entries) || [];
    if (entries.length) {
      lines.push('completed entries: ' + entries.filter(function (e) {
        return e.materialization === 'completed';
      }).length + ' / ' + entries.length);
    }
    return lines.map(function (line) {
      return '<div class="cc-meta-line cc-signoff-readiness-line">' + line + '</div>';
    }).join('');
  },
  buildCompletionMetadataHtml: function (goalDetail) {
    var completion = (goalDetail && goalDetail.completion) || null;
    if (!completion) {
      return '';
    }
    var commits = Array.isArray(completion.commits) ? completion.commits : [];
    var commitLine = commits.length
      ? commits.map(function (row) {
          return String(row.commit_sha || '').slice(0, 12);
        }).join(', ')
      : '—';
    return (
      '<div class="cc-meta-line">signed off by ' + escapeHtml(String(completion.sign_off_actor || '—')) +
      ' · ' + escapeHtml(String(completion.sign_off_at || '—')) + '</div>' +
      '<div class="cc-meta-line">entries: ' + escapeHtml(String(completion.entry_count || '—')) +
      ' · commits: ' + escapeHtml(commitLine) + '</div>'
    );
  },
  buildLaunchReadinessPanelHtml: function (readiness) {
    if (!readiness) {
      return '<div class="cc-meta-line">Launch readiness: not loaded</div>';
    }
    var ready = readiness.ready === true;
    var reason = readiness.display_reason ||
      (readiness.blocking_reason ? String(readiness.blocking_reason).replace(/_/g, ' ') : '—');
    var lines = [
      'launch ready: ' + (ready ? 'yes' : 'no'),
      'blocking reason: ' + reason
    ];
    var dirty = readiness.dirty_path_classification || {};
    var stray = dirty.stray_unexpected || [];
    if (stray.length) {
      lines.push('unexpected dirty paths: ' + stray.map(function (row) { return row.path; }).join(', '));
    }
    return lines.map(function (line) {
      return '<div class="cc-meta-line cc-launch-readiness-line">' + line + '</div>';
    }).join('');
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
      '<div class="cc-meta-line">Governance actions (approve breakdown, sign-off) appear in the panel above when required.</div>'
    );
  },
  formatProjectDisplayName: function (project) {
    var row = project || {};
    return row.display_name || row.name || row.slug || row.project_id || 'project';
  },
  formatProjectOptionLabel: function (project) {
    return CCGoalRunnerHelpers.formatProjectDisplayName(project);
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
    { id: 'overview', label: 'Overview', eyebrow: 'Platform pulse', icon: 'overview' },
    { id: 'projects', label: 'Projects', eyebrow: 'Registry', icon: 'projects' },
    { id: 'goals', label: 'Goals', eyebrow: 'Governance workflow', icon: 'goals' },
    { id: 'history', label: 'History', eyebrow: 'Execution audit', icon: 'runs' }
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
    projectById: {},
    projectEditor: {
      open: false,
      mode: 'create',
      projectId: null,
      saving: false
    },
    goalRunner: {
      selectedProjectId: CCGoalRunnerHelpers.ANIMA_LINUX_PROJECT_ID,
      selectedGoalId: null,
      selectedProfile: null,
      projectGoals: [],
      projectRuns: [],
      lastResponse: null,
      running: false,
      wired: false,
      filterTab: 'active',
      goalDetailsCache: {},
      launchReadinessCache: {},
      signOffReadinessCache: {},
      queueDetailsCache: {}
    },
    history: {
      selectedProjectId: CCGoalRunnerHelpers.ANIMA_LINUX_PROJECT_ID
    },
    historyRuns: []
  };

  var AUTO_REFRESH_MS = 60000;
  var refreshInFlight = false;
  var governanceActionInFlight = false;
  var projectLoadSeq = 0;
  var refreshTimerId = null;
  var initialized = false;

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
        var raw = body.detail != null ? body.detail : (body.error || detail);
        if (raw && typeof raw === 'object') {
          detail = raw.message || raw.error || JSON.stringify(raw);
        } else {
          detail = raw || detail;
        }
      } catch (_e) { /* ignore */ }
      var err = new Error(String(detail || 'governance_fetch_failed'));
      err.status = resp.status;
      throw err;
    }
    return resp.json();
  }

  function setConnection(ok, detail) {
    state.connected = ok;
    var pill = $('ccConnectionPill');
    if (!pill) return;
    pill.innerHTML = ok
      ? '<span class="cc-live-dot" aria-hidden="true"></span> Live'
      : 'Offline';
    pill.className = 'cc-pill ' + (ok ? 'cc-pill-ok cc-pill-live' : 'cc-pill-warn');
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

  async function mergeProjectGoalsAndRuns(projectId) {
    var project = state.projectById[projectId] ||
      state.projects.find(function (p) { return p.project_id === projectId; });
    if (!project) return;
    var goals = [];
    var runs = [];
    try {
      var goalsPayload = await govFetch(
        'goals?project_id=' + encodeURIComponent(projectId)
      );
      goals = goalsPayload.goals || [];
    } catch (_goalsErr) { /* per-project goals optional */ }
    try {
      var runsPayload = await govFetch(
        'runs?limit=24&project_id=' + encodeURIComponent(projectId)
      );
      runs = runsPayload.runs || [];
    } catch (_runsErr) { /* per-project runs optional */ }
    syncGoalsRunsForProject(projectId, goals, runs);
  }

  async function loadGoalsAndRunsAcrossProjects() {
    var results = await Promise.all(state.projects.map(async function (project) {
      var projectId = project && project.project_id;
      if (!projectId) return { goals: [], runs: [] };
      var goals = [];
      var runs = [];
      try {
        var goalsPayload = await govFetch(
          'goals?project_id=' + encodeURIComponent(projectId)
        );
        goals = (goalsPayload.goals || []).map(function (g) {
          return Object.assign({}, g, {
            project_id: projectId,
            _project_name: CCGoalRunnerHelpers.formatProjectDisplayName(project)
          });
        });
      } catch (_goalsErr) { /* per-project goals optional */ }
      try {
        var runsPayload = await govFetch(
          'runs?limit=24&project_id=' + encodeURIComponent(projectId)
        );
        runs = (runsPayload.runs || []).map(function (r) {
          return Object.assign({}, r, {
            project_id: projectId,
            _project_name: CCGoalRunnerHelpers.formatProjectDisplayName(project)
          });
        });
      } catch (_runsErr) { /* per-project runs optional */ }
      return { goals: goals, runs: runs };
    }));
    state.goals = [];
    state.runs = [];
    results.forEach(function (item) {
      state.goals = state.goals.concat(item.goals);
      state.runs = state.runs.concat(item.runs);
    });
  }

  function rebuildProjectIndex() {
    state.projectById = {};
    state.projects.forEach(function (project) {
      if (project && project.project_id) state.projectById[project.project_id] = project;
    });
  }

  function projectLabel(projectId) {
    var p = state.projectById[projectId] || {};
    return CCGoalRunnerHelpers.formatProjectDisplayName(p) || projectId || '—';
  }

  function driverStatusLabel() {
    var d = state.driver || {};
    var raw = d.status || d.state || 'unknown';
    return String(raw).replace(/_/g, ' ');
  }

  function goalStatusBuckets() {
    var completed = 0;
    var pending = 0;
    var blocked = 0;
    visiblePlatformGoals().forEach(function (g) {
      var s = String(g.display_status || g.status || '').toLowerCase();
      if (/complete|approved|released/.test(s)) completed += 1;
      else if (/block|fail|halt|error|rejected/.test(s)) blocked += 1;
      else pending += 1;
    });
    return { completed: completed, pending: pending, blocked: blocked };
  }

  function visiblePlatformGoals() {
    return (state.goals || []).filter(function (g) {
      if (CCGoalRunnerHelpers.isGoalHidden(g)) return false;
      if (g.freshness === 'stale') return false;
      return true;
    });
  }

  function platformStaleGoalCount() {
    return (state.goals || []).filter(function (g) {
      return g.freshness === 'stale' && !CCGoalRunnerHelpers.isGoalHidden(g);
    }).length;
  }

  function syncGoalsRunsForProject(projectId, goals, runs) {
    var project = state.projectById[projectId] ||
      state.projects.find(function (p) { return p.project_id === projectId; });
    if (!project) return;
    var projectName = CCGoalRunnerHelpers.formatProjectDisplayName(project);
    var enrichedGoals = (goals || []).map(function (g) {
      return Object.assign({}, g, {
        project_id: projectId,
        _project_name: projectName
      });
    });
    var enrichedRuns = (runs || []).map(function (r) {
      return Object.assign({}, r, {
        project_id: projectId,
        _project_name: projectName
      });
    });
    state.goals = state.goals.filter(function (g) {
      return g.project_id !== projectId;
    }).concat(enrichedGoals);
    state.runs = state.runs.filter(function (r) {
      return r.project_id !== projectId;
    }).concat(enrichedRuns);
    renderStats();
    renderActionInbox();
    if (state.section === 'overview') renderOverviewBody();
  }

  function resolveProjectProfile(projectId) {
    var cached = state.projectDetails[projectId] || state.projectById[projectId];
    if (!cached) return null;
    var repoPath = cached.repo_path;
    if (!repoPath && cached.repos && cached.repos.length) {
      repoPath = cached.repos[0].repo_path;
    }
    return Object.assign({}, cached, { repo_path: repoPath || cached.repo_path || '' });
  }

  function runProgressPct(run) {
    var s = String(run.status || '').toLowerCase();
    if (/complete|approved|released/.test(s)) return 100;
    if (/block|fail|halt|error/.test(s)) return 100;
    if (/running|active|dispatch|execut/.test(s)) return 60;
    if (/pending|await|review|draft/.test(s)) return 30;
    return 20;
  }

  function runBarColor(run) {
    var s = String(run.status || '').toLowerCase();
    if (/complete|approved|released/.test(s)) return '#22c55e';
    if (/block|fail|halt|error/.test(s)) return '#ef4444';
    return '#7c3aed';
  }

  function seedProjectDetailsFromList() {
    state.projects.forEach(function (project) {
      if (!project || !project.project_id) return;
      state.projectDetails[project.project_id] = project;
    });
  }

  function buildNav() {
    var nav = $('ccNav');
    if (!nav) return;
    nav.innerHTML = SECTIONS.map(function (sec) {
      var active = sec.id === state.section ? ' cc-nav-active' : '';
      return (
        '<button type="button" class="cc-nav-btn' + active + '" data-section="' + sec.id + '" ' +
        'title="' + escapeHtml(sec.label) + '" aria-label="' + escapeHtml(sec.label) + '" role="tab">' +
        '<span class="cc-nav-icon">' + CCIcons.icon(sec.icon) + '</span>' +
        '<span class="cc-nav-link-label">' + escapeHtml(sec.label) + '</span></button>'
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
    var titleEl = $('ccSectionTitle');
    var eyebrowEl = $('ccSectionEyebrow');
    if (titleEl) titleEl.textContent = title ? title.label : 'Overview';
    if (eyebrowEl) eyebrowEl.textContent = title && title.eyebrow ? title.eyebrow : 'Command Center';
    var badge = $('ccTopbarBadge');
    if (badge) {
      if (sectionId === 'overview') {
        badge.hidden = false;
        badge.textContent = state.projects.length + ' projects · ' + visiblePlatformGoals().length + ' active goals';
      } else {
        badge.hidden = true;
        badge.textContent = '';
      }
    }
    document.querySelectorAll('.cc-panel').forEach(function (panel) {
      var active = panel.getAttribute('data-section') === sectionId;
      panel.hidden = !active;
      panel.classList.toggle('cc-panel-active', active);
    });
    document.querySelectorAll('.cc-nav-btn').forEach(function (btn) {
      btn.classList.toggle('cc-nav-active', btn.getAttribute('data-section') === sectionId);
    });
    if (sectionId === 'goals') {
      if (!state.goalRunner.wired) {
        void initGoalsTab();
      } else {
        renderGoalsProjectSelect();
        renderGoalFilterTabs();
        renderGoalList();
      }
    }
    if (sectionId === 'history') {
      renderHistoryProjectSelect();
      void loadHistoryForProject(
        state.history.selectedProjectId || state.goalRunner.selectedProjectId
      );
    }
  }

  function syncGoalProjectSelectors(projectId) {
    if (!projectId) return;
    var goalsSelect = $('ccGoalsProjectSelect');
    if (goalsSelect && goalsSelect.value !== projectId) {
      goalsSelect.value = projectId;
    }
    var hiddenProject = $('ccGoalRunnerProject');
    if (hiddenProject) {
      hiddenProject.value = projectId;
    }
  }

  async function postGoalReject(goalId, projectId, breakdownVersion, reason) {
    var repoPath = await resolveDriverRepoPath(projectId, goalId);
    return govFetch('goals/' + encodeURIComponent(goalId) + '/breakdown/reject', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        repo_path: repoPath,
        breakdown_version: breakdownVersion || 1,
        reason: reason || 'removed_by_operator'
      })
    });
  }

  function visibleProjectGoals() {
    return (state.goalRunner.projectGoals || []).filter(function (g) {
      return !CCGoalRunnerHelpers.isGoalHidden(g);
    });
  }

  function filteredProjectGoals() {
    var tab = state.goalRunner.filterTab || 'active';
    return visibleProjectGoals().filter(function (g) {
      return CCGoalRunnerHelpers.goalFilterBucket(g) === tab;
    }).sort(function (a, b) {
      return (b.last_seq || 0) - (a.last_seq || 0);
    });
  }

  function buildGoalQuickActionsHtml(goalId, projectId, goalDetail) {
    var attrs = ' data-goal-id="' + escapeHtml(goalId) + '" data-project-id="' + escapeHtml(projectId) + '"';
    var launchGate = CCGoalRunnerHelpers.computeDriverLaunchGate({
      goalDetail: goalDetail,
      profile: state.goalRunner.selectedProfile,
      connected: state.connected,
      readiness: state.goalRunner.launchReadinessCache[goalId]
    });
    var startDisabled = !launchGate.ok ? ' disabled title="' + escapeHtml(launchGate.reason) + '"' : '';
    function actionBtn(action, icon, label, extraAttrs) {
      return (
        '<button type="button" class="cc-icon-action cc-icon-action-labeled" title="' + escapeHtml(label) + '" ' +
        'aria-label="' + escapeHtml(label) + '"' + attrs + (extraAttrs || '') +
        ' data-driver-action="' + action + '">' +
        CCIcons.icon(icon) + '<span class="cc-icon-action-label">' + escapeHtml(label) + '</span></button>'
      );
    }
    function goalBtn(action, icon, label) {
      return (
        '<button type="button" class="cc-icon-action cc-icon-action-labeled" title="' + escapeHtml(label) + '" ' +
        'aria-label="' + escapeHtml(label) + '"' + attrs + ' data-goal-action="' + action + '">' +
        CCIcons.icon(icon) + '<span class="cc-icon-action-label">' + escapeHtml(label) + '</span></button>'
      );
    }
    return (
      '<div class="cc-goal-quick-actions">' +
      actionBtn('start', 'play', 'Start', startDisabled) +
      actionBtn('pause', 'pause', 'Pause') +
      actionBtn('resume', 'resume', 'Resume') +
      actionBtn('halt', 'halt', 'Halt') +
      actionBtn('stop', 'stop', 'Stop') +
      goalBtn('edit', 'edit', 'Edit') +
      goalBtn('remove', 'trash', 'Remove').replace('cc-icon-action-labeled', 'cc-icon-action-labeled cc-icon-action-danger') +
      (launchGate.ok ? '' : '<div class="cc-meta-line cc-driver-launch-block cc-launch-readiness-block" data-launch-readiness="' + escapeHtml(goalId) + '">' + escapeHtml(launchGate.reason) + '</div>') +
      '</div>'
    );
  }

  function buildInlineApprovalHtml(goal, goalDetail) {
    var gid = escapeHtml(goal.goal_id);
    var pid = escapeHtml(goal.project_id || state.goalRunner.selectedProjectId);
    var baseAttrs = ' data-goal-id="' + gid + '" data-project-id="' + pid + '"';
    if (shouldShowBreakdownApproval(goalDetail || goal)) {
      var bVersion = (goalDetail && goalDetail.breakdown_version) ||
        (goal && goal.breakdown_version) || 1;
      return (
        '<div class="cc-goal-inline-approval">' +
        '<span>Plan ready — approve to enable dispatch.</span>' +
        '<button type="button" class="cc-primary-btn cc-btn-sm" data-goal-action="approve-breakdown"' + baseAttrs +
        ' data-breakdown-version="' + escapeHtml(String(bVersion)) + '">Approve</button>' +
        '<button type="button" class="cc-ghost-btn cc-btn-sm" data-goal-action="reject-breakdown"' + baseAttrs +
        ' data-breakdown-version="' + escapeHtml(String(bVersion)) + '">Reject</button></div>'
      );
    }
    if (shouldShowGoalSignOff(goalDetail || goal)) {
      var signOffGate = CCGoalRunnerHelpers.computeSignOffGate({
        goalDetail: goalDetail || goal,
        readiness: state.goalRunner.signOffReadinessCache[goal.goal_id]
      });
      return (
        '<div class="cc-goal-inline-approval">' +
        '<span>Work finished — sign off when ready.</span>' +
        (signOffGate.ok
          ? '<button type="button" class="cc-primary-btn cc-btn-sm" data-goal-action="sign-off"' + baseAttrs +
            '>Sign off</button>'
          : '<span class="cc-meta-line">' + escapeHtml(signOffGate.reason) + '</span>') +
        '</div>'
      );
    }
    return '';
  }

  function buildGoalRunsHtml(goalId, runs, goals) {
    var goalRuns = CCGoalRunnerHelpers.runsForGoal(goalId, runs, goals);
    if (!goalRuns.length) {
      return '<div class="cc-meta-line cc-goal-runs-empty">No runs linked yet.</div>';
    }
    return (
      '<div class="cc-goal-runs">' +
      goalRuns.slice(0, 6).map(function (r) {
        var pct = runProgressPct(r);
        return (
          '<div class="cc-run-row cc-run-row-compact">' +
          '<div class="cc-run-meta"><strong>' + escapeHtml(String(r.run_id || '').slice(0, 10)) + '…</strong>' +
          '<div class="cc-run-summary">' + escapeHtml(goalStatusLabel(r.status)) + '</div></div>' +
          '<div class="cc-run-bar"><span style="width:' + pct + '%;background:' + runBarColor(r) + '"></span></div>' +
          '</div>'
        );
      }).join('') +
      '</div>'
    );
  }

  function buildGoalCardHtml(goal, options) {
    options = options || {};
    var goalId = goal.goal_id;
    var projectId = goal.project_id || state.goalRunner.selectedProjectId;
    var isExpanded = state.goalRunner.selectedGoalId === goalId;
    var detail = state.goalRunner.goalDetailsCache[goalId] || goal;
    var status = goalStatusLabel(detail.display_status || detail.status || goal.status);
    var freshness = goal.freshness ? String(goal.freshness) : '';
    var freshnessBadge = freshness === 'stale'
      ? '<span class="cc-goal-freshness cc-goal-freshness-stale">Stale duplicate</span>'
      : (freshness === 'fresh' && goal.duplicate_group_size > 1
        ? '<span class="cc-goal-freshness cc-goal-freshness-fresh">Current</span>'
        : '');
    var pct = CCGoalRunnerHelpers.goalProgressPct(goal);
    var color = CCGoalRunnerHelpers.goalProgressColor(goal);
    var runs = state.goalRunner.projectRuns || [];
    var goals = state.goalRunner.projectGoals || [];
    var expandedCls = isExpanded ? ' cc-goal-card-expanded' : '';
    var expandedBody = '';
    if (isExpanded && options.expandedHtml) {
      expandedBody = options.expandedHtml;
    }
    return (
      '<article class="cc-goal-card' + expandedCls + '" data-goal-card="' + escapeHtml(goalId) + '">' +
      '<div class="cc-goal-card-head">' +
      '<button type="button" class="cc-goal-card-main" data-goal-select="' + escapeHtml(goalId) + '">' +
      '<div class="cc-goal-card-title">' +
      '<span class="' + statusClass(detail.display_status || detail.status) + '">' + escapeHtml(status) + '</span>' +
      freshnessBadge +
      '<strong>' + escapeHtml(truncate(goal.statement, 120)) + '</strong></div>' +
      '<div class="cc-run-bar cc-goal-progress-bar"><span style="width:' + pct + '%;background:' + color + '"></span></div>' +
      '</button>' +
      buildGoalQuickActionsHtml(goalId, projectId, detail) +
      '</div>' +
      buildInlineApprovalHtml(goal, detail) +
      buildGoalRunsHtml(goalId, runs, goals) +
      expandedBody +
      '</article>'
    );
  }

  function renderGoalsProjectSelect() {
    var select = $('ccGoalsProjectSelect');
    if (!select) return;
    var current = state.goalRunner.selectedProjectId;
    select.innerHTML = state.projects.map(function (p) {
      var sel = p.project_id === current ? ' selected' : '';
      return '<option value="' + escapeHtml(p.project_id) + '"' + sel + '>' +
        escapeHtml(CCGoalRunnerHelpers.formatProjectDisplayName(p)) + '</option>';
    }).join('');
    if (!select.dataset.wired) {
      select.dataset.wired = '1';
      select.addEventListener('change', function () {
        state.goalRunner.selectedGoalId = null;
        state.goalRunner.goalDetailsCache = {};
        var listHost = $('ccGoalList');
        if (listHost) listHost.innerHTML = '<div class="cc-meta-line cc-goals-loading">Loading goals…</div>';
        void loadGoalRunnerProjectProfile(select.value);
      });
    }
  }

  function renderHistoryProjectSelect() {
    var select = $('ccHistoryProjectSelect');
    if (!select) return;
    if (!state.history.selectedProjectId) {
      state.history.selectedProjectId = state.goalRunner.selectedProjectId;
    }
    var current = state.history.selectedProjectId;
    select.innerHTML = state.projects.map(function (p) {
      var sel = p.project_id === current ? ' selected' : '';
      return '<option value="' + escapeHtml(p.project_id) + '"' + sel + '>' +
        escapeHtml(CCGoalRunnerHelpers.formatProjectDisplayName(p)) + '</option>';
    }).join('');
    if (!select.dataset.wired) {
      select.dataset.wired = '1';
      select.addEventListener('change', function () {
        state.history.selectedProjectId = select.value;
        void loadHistoryForProject(select.value);
      });
    }
  }

  function renderGoalFilterTabs() {
    var host = $('ccGoalFilterTabs');
    if (!host) return;
    var tab = state.goalRunner.filterTab || 'active';
    var counts = { pending_review: 0, pending_completion: 0, active: 0, stale: 0, complete: 0 };
    visibleProjectGoals().forEach(function (g) {
      var bucket = CCGoalRunnerHelpers.goalFilterBucket(g);
      if (counts[bucket] != null) counts[bucket] += 1;
    });
    host.innerHTML = CCGoalRunnerHelpers.GOAL_FILTER_TABS.map(function (item) {
      var active = item.id === tab ? ' cc-filter-tab-active' : '';
      return (
        '<button type="button" class="cc-filter-tab' + active + '" data-goal-filter="' + item.id + '">' +
        escapeHtml(item.label) + ' <span class="cc-filter-count">' + (counts[item.id] || 0) + '</span></button>'
      );
    }).join('');
    if (!host.dataset.wired) {
      host.dataset.wired = '1';
      host.addEventListener('click', function (ev) {
        var btn = ev.target.closest('[data-goal-filter]');
        if (!btn) return;
        state.goalRunner.filterTab = btn.getAttribute('data-goal-filter');
        renderGoalFilterTabs();
        renderGoalList();
      });
    }
  }

  function renderGoalList() {
    var host = $('ccGoalList');
    if (!host) return;
    var goals = filteredProjectGoals();
    if (!goals.length) {
      host.innerHTML = '<div class="cc-empty">No goals in this tab for the selected project.</div>';
      return;
    }
    host.innerHTML = goals.map(function (g) {
      return buildGoalCardHtml(g, {});
    }).join('');
    if (!host.dataset.wired) {
      host.dataset.wired = '1';
      host.addEventListener('click', function (ev) {
        var selectBtn = ev.target.closest('[data-goal-select]');
        if (selectBtn) {
          var gid = selectBtn.getAttribute('data-goal-select');
          if (state.goalRunner.selectedGoalId === gid) {
            state.goalRunner.selectedGoalId = null;
          } else {
            state.goalRunner.selectedGoalId = gid;
          }
          renderGoalList();
          if (state.goalRunner.selectedGoalId) {
            void expandGoalCard(state.goalRunner.selectedGoalId, state.goalRunner.selectedProjectId);
          }
          return;
        }
        var editBtn = ev.target.closest('[data-goal-action="edit"]');
        if (editBtn) {
          var goal = state.goalRunner.projectGoals.find(function (g) {
            return g.goal_id === editBtn.getAttribute('data-goal-id');
          });
          if (goal && $('ccGoalRunnerStatement')) {
            $('ccGoalRunnerStatement').value = goal.statement || '';
            var collapsible = $('ccGoalNewGoalCollapsible');
            if (collapsible) collapsible.open = true;
          }
        }
      });
    }
  }

  async function expandGoalCard(goalId, projectId) {
    var card = document.querySelector('[data-goal-card="' + goalId + '"]');
    if (!card) return;
    var existing = card.querySelector('.cc-goal-card-detail');
    if (existing) return;
    try {
      var detail = await govFetch(
        'goals/' + encodeURIComponent(goalId) + '?project_id=' + encodeURIComponent(projectId)
      );
      state.goalRunner.goalDetailsCache[goalId] = detail;
      var detailHost = document.createElement('div');
      detailHost.className = 'cc-goal-card-detail';
      detailHost.innerHTML =
        '<div class="cc-goal-card-detail-inner">' +
        CCGoalRunnerHelpers.buildSimpleProgressHtml(detail.display_status || detail.status) +
        '<details class="cc-technical-details"><summary>Technical details</summary>' +
        '<div id="ccGoalDetailPanels-' + escapeHtml(goalId) + '">Loading…</div></details></div>';
      card.appendChild(detailHost);
      card.classList.add('cc-goal-card-expanded');
      var panelsTarget = $('ccGoalDetailPanels-' + goalId);
      await refreshGoalRunnerView({
        projectId: projectId,
        goalId: goalId,
        panelsTarget: panelsTarget
      });
      renderGoalFilterTabs();
    } catch (err) {
      if (card) {
        var errEl = document.createElement('div');
        errEl.className = 'cc-form-error';
        errEl.textContent = String(err.message || err);
        card.appendChild(errEl);
      }
    }
  }

  async function loadHistoryForProject(projectId) {
    if (!projectId) return;
    try {
      var payload = await govFetch('runs?limit=48&project_id=' + encodeURIComponent(projectId));
      state.historyRuns = payload.runs || [];
    } catch (_err) {
      state.historyRuns = [];
    }
    renderHistoryList();
  }

  function renderHistoryList() {
    var host = $('ccHistoryList');
    if (!host) return;
    var projectId = state.history.selectedProjectId || state.goalRunner.selectedProjectId;
    var runs = state.historyRuns || [];
    if (!projectId) {
      host.innerHTML = '<div class="cc-empty">Select a project to view run history.</div>';
      return;
    }
    if (!runs.length) {
      host.innerHTML = '<div class="cc-empty">No runs recorded for this project yet.</div>';
      return;
    }
    var sorted = runs.slice().sort(function (a, b) {
      return (b.last_seq || b.started_seq || 0) - (a.last_seq || a.started_seq || 0);
    });
    host.innerHTML = sorted.map(function (r, index) {
      var pct = runProgressPct(r);
      var color = runBarColor(r);
      var summary = /complete|approved|released/.test(String(r.status || ''))
        ? 'Finished · ' + goalStatusLabel(r.status)
        : 'Tier ' + (r.tier || '—');
      return (
        '<details class="cc-history-item"' + (index === 0 ? '' : '') + '>' +
        '<summary class="cc-history-summary">' +
        '<span class="cc-history-run-id">' + escapeHtml(String(r.run_id || '').slice(0, 14)) + '…</span>' +
        '<span class="' + statusClass(r.status) + '">' + escapeHtml(goalStatusLabel(r.status)) + '</span>' +
        '<span class="cc-history-run-meta">' + escapeHtml(summary) + '</span>' +
        '<span class="cc-run-bar cc-history-bar"><span style="width:' + pct + '%;background:' + color + '"></span></span>' +
        '</summary>' +
        '<div class="cc-history-body">' +
        (r.goal_id
          ? '<div class="cc-meta-line">goal: ' + escapeHtml(truncate(r.goal_id, 28)) + '</div>'
          : '') +
        '<div class="cc-meta-line">correlation: ' + escapeHtml(truncate(r.correlation_id || r.request_id || '—', 40)) + '</div>' +
        '<div class="cc-meta-line">tier: ' + escapeHtml(r.tier || '—') + ' · seq: ' + escapeHtml(String(r.last_seq || r.started_seq || '—')) + '</div>' +
        '</div></details>'
      );
    }).join('');
  }

  function renderNewGoalForm() {
    var host = $('ccGoalNewGoalHost');
    if (!host) return;
    var panel = $('ccGoalRunnerPanel');
    if (panel && panel.parentNode !== host) {
      host.appendChild(panel);
    }
  }

  async function initGoalsTab() {
    renderGoalsProjectSelect();
    var controlsHost = $('ccGoalRunnerControls');
    if (controlsHost && !state.goalRunner.wired) {
      await renderGoalRunnerForm();
    }
    renderNewGoalForm();
    renderGoalFilterTabs();
    await loadGoalRunnerProjectProfile(state.goalRunner.selectedProjectId);
  }

  function collectActionInboxItems() {
    return visiblePlatformGoals().filter(function (g) {
      var s = String(g.display_status || g.status || '').toLowerCase();
      return s === 'pending_approval' || s === 'pending_completion';
    }).map(function (g) {
      var s = String(g.display_status || g.status || '').toLowerCase();
      return {
        goalId: g.goal_id,
        projectId: g.project_id,
        projectName: g._project_name || projectLabel(g.project_id),
        statement: g.statement || '',
        kind: s === 'pending_approval' ? 'approve' : 'signoff',
        label: s === 'pending_approval' ? 'Approve plan' : 'Sign off completion'
      };
    });
  }

  function renderWorkflowStrip() {
    var host = $('ccWorkflowStrip');
    if (!host) return;
    var selectedGoal = state.goalRunner.projectGoals.find(function (g) {
      return g.goal_id === state.goalRunner.selectedGoalId;
    }) || state.goals.find(function (g) {
      return g.goal_id === state.goalRunner.selectedGoalId;
    }) || null;
    var activeStep = CCGoalRunnerHelpers.inferWorkflowStep({
      projectId: state.goalRunner.selectedProjectId,
      goals: state.goals,
      selectedGoal: selectedGoal
    });
    host.innerHTML =
      '<div class="cc-workflow-head">' +
      '<h2 class="cc-workflow-title">How it works</h2>' +
      '<p class="cc-workflow-sub">Five steps from idea to done — you stay in control at approval and sign-off.</p></div>' +
      '<ol class="cc-workflow-steps">' +
      CCGoalRunnerHelpers.USER_WORKFLOW.map(function (step, index) {
        var cls = index < activeStep ? ' cc-workflow-done'
          : index === activeStep ? ' cc-workflow-current' : '';
        return (
          '<li class="cc-workflow-step' + cls + '">' +
          '<span class="cc-workflow-num">' + (index + 1) + '</span>' +
          '<div class="cc-workflow-copy">' +
          '<strong>' + escapeHtml(step.label) + '</strong>' +
          '<span>' + escapeHtml(step.hint) + '</span></div></li>'
        );
      }).join('') +
      '</ol>';
  }

  function renderActionInbox() {
    var host = $('ccActionInbox');
    if (!host) return;
    var items = collectActionInboxItems();
    if (!items.length) {
      host.innerHTML = '';
      host.hidden = true;
      return;
    }
    host.hidden = false;
    host.innerHTML =
      '<article class="cc-card cc-inbox-card">' +
      '<header class="cc-card-head"><span>' + CCIcons.icon('goals') + '</span>' +
      '<h2>Needs your attention</h2></header>' +
      '<p class="cc-card-desc">These goals are waiting for you — click to open and take action.</p>' +
      '<ul class="cc-inbox-list">' +
      items.map(function (item) {
        return (
          '<li class="cc-inbox-item">' +
          '<div class="cc-inbox-copy">' +
          '<strong>' + escapeHtml(item.label) + '</strong>' +
          '<span class="cc-inbox-project">' + escapeHtml(item.projectName) + '</span>' +
          '<span class="cc-inbox-statement">' + escapeHtml(truncate(item.statement, 100)) + '</span></div>' +
          '<button type="button" class="cc-primary-btn cc-inbox-open" data-inbox-goal="' +
          escapeHtml(item.goalId) + '" data-inbox-project="' + escapeHtml(item.projectId) + '">Open</button>' +
          '</li>'
        );
      }).join('') +
      '</ul></article>';
    if (!host.dataset.inboxWired) {
      host.dataset.inboxWired = '1';
      host.addEventListener('click', function (ev) {
        var btn = ev.target.closest('[data-inbox-goal]');
        if (!btn) return;
        var goalId = btn.getAttribute('data-inbox-goal');
        var projectId = btn.getAttribute('data-inbox-project');
        state.goalRunner.selectedProjectId = projectId;
        var projectSelect = $('ccGoalRunnerProject');
        if (projectSelect) projectSelect.value = projectId;
        void loadGoalRunnerProjectProfile(projectId).then(function () {
          return viewGoalLifecycle(goalId, projectId);
        }).then(function () {
          scrollToSection('ccPanelGoals');
        });
      });
    }
  }

  function renderStats() {
    var grid = $('ccStatGrid');
    if (!grid) return;
    var buckets = goalStatusBuckets();
    var inboxCount = collectActionInboxItems().length;
    var visibleGoals = visiblePlatformGoals();
    var staleCount = platformStaleGoalCount();
    var stats = [
      {
        icon: 'projects',
        label: 'Projects',
        scope: 'All projects',
        value: state.projects.length,
        hint: 'Registered codebases you can run governed work against.'
      },
      {
        icon: 'goals',
        label: 'Active goals',
        scope: 'All projects',
        value: visibleGoals.length,
        hint: inboxCount
          ? inboxCount + ' need your action · ' + buckets.completed + ' done · ' + buckets.blocked + ' blocked'
          : buckets.pending + ' in progress · ' + buckets.completed + ' done · ' + buckets.blocked + ' blocked'
            + (staleCount ? ' · ' + staleCount + ' stale duplicates hidden' : '')
      },
      {
        icon: 'runs',
        label: 'Executions',
        scope: 'All projects',
        value: state.runs.length,
        hint: 'Driver runs across every registered project. Use History for one project.'
      }
    ];
    grid.innerHTML = stats.map(function (stat) {
      var mod = ' cc-stat-card--' + stat.icon;
      return (
        '<article class="cc-stat-card' + mod + '">' +
        '<div class="cc-stat-card-inner">' +
        '<div class="cc-stat-head">' +
        '<div class="cc-stat-icon">' + CCIcons.icon(stat.icon) + '</div>' +
        '<span class="cc-stat-scope">' + escapeHtml(stat.scope) + '</span>' +
        '</div>' +
        '<div class="cc-stat-value">' + escapeHtml(String(stat.value)) + '</div>' +
        '<div class="cc-stat-label">' + escapeHtml(stat.label) + '</div>' +
        '<div class="cc-stat-hint">' + escapeHtml(stat.hint) + '</div>' +
        '</div></article>'
      );
    }).join('');
    if (state.section === 'overview') {
      var badge = $('ccTopbarBadge');
      if (badge) {
        badge.hidden = false;
        badge.textContent = state.projects.length + ' projects · ' + visiblePlatformGoals().length + ' active goals';
      }
    }
  }

  function newDriverRunId() {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
      return crypto.randomUUID();
    }
    return 'run-' + Date.now();
  }

  async function resolveDriverRepoPath(projectId, goalId) {
    var pid = projectId || state.goalRunner.selectedProjectId;
    var profile = pid ? resolveProjectProfile(pid) : null;
    if (profile && profile.repo_path) {
      return profile.repo_path;
    }
    if (pid && state.projectDetails[pid] && state.projectDetails[pid].repo_path) {
      return state.projectDetails[pid].repo_path;
    }
    if (pid) {
      try {
        var detail = await govFetch('projects/' + encodeURIComponent(pid));
        state.projectDetails[pid] = detail;
        if (detail.repo_path) return detail.repo_path;
        if (detail.repos && detail.repos.length && detail.repos[0].repo_path) {
          return detail.repos[0].repo_path;
        }
      } catch (_err) { /* fall through */ }
    }
    if (goalId) {
      var match = state.goals.find(function (g) { return g.goal_id === goalId; });
      if (match && match.project_id) {
        return resolveDriverRepoPath(match.project_id, null);
      }
    }
    var driverGoal = state.driver && state.driver.active_goal_id;
    if (driverGoal) {
      var g2 = state.goals.find(function (g) { return g.goal_id === driverGoal; });
      if (g2 && g2.project_id) return resolveDriverRepoPath(g2.project_id, null);
    }
    throw new Error('No repo path — set the repo path when editing the project above.');
  }

  async function fetchSignOffReadiness(goalId, projectId) {
    if (!goalId) return null;
    var repoPath = await resolveDriverRepoPath(projectId, goalId);
    var query = 'goals/' + encodeURIComponent(goalId) + '/sign-off-readiness?repo_path=' +
      encodeURIComponent(repoPath) + '&actor=operator';
    var payload = await govFetch(query);
    state.goalRunner.signOffReadinessCache[goalId] = payload;
    return payload;
  }

  async function fetchDriverLaunchReadiness(goalId, projectId) {
    if (!goalId) return null;
    var repoPath = await resolveDriverRepoPath(projectId, goalId);
    var query = 'driver/launch-readiness?repo_path=' + encodeURIComponent(repoPath) +
      '&goal_id=' + encodeURIComponent(goalId);
    var payload = await govFetch(query);
    state.goalRunner.launchReadinessCache[goalId] = payload;
    return payload;
  }

  async function refreshLaunchReadinessForGoals(projectId, goals) {
    var rows = goals || state.goalRunner.projectGoals || [];
    await Promise.all(rows.map(function (goal) {
      if (!goal || !goal.goal_id) return Promise.resolve();
      return fetchDriverLaunchReadiness(goal.goal_id, projectId || goal.project_id).catch(function () {
        return null;
      });
    }));
  }

  async function postDriverControl(action, goalId, projectId) {
    var select = $('ccDriverProjectSelect');
    var pid = (select && select.value) || projectId || state.goalRunner.selectedProjectId;
    var repoPath = await resolveDriverRepoPath(pid, goalId);
    var body = {
      repo_path: repoPath,
      run_id: newDriverRunId(),
      goal_id: goalId || null
    };
    if (action === 'stop') {
      body.reason = 'operator_requested_stop';
    }
    return govFetch('driver/' + action, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
  }

  async function postGoalSignOff(goalId, projectId) {
    var repoPath = await resolveDriverRepoPath(projectId, goalId);
    return govFetch('goals/' + encodeURIComponent(goalId) + '/sign-off', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        repo_path: repoPath,
        request_id: 'cc-sign-off-' + Date.now(),
        actor: 'operator',
        source: 'command_center'
      })
    });
  }

  async function postBreakdownApprove(goalId, projectId, breakdownVersion) {
    var repoPath = await resolveDriverRepoPath(projectId, goalId);
    return govFetch('goals/' + encodeURIComponent(goalId) + '/breakdown/approve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        repo_path: repoPath,
        breakdown_version: breakdownVersion,
        request_id: 'cc-approve-' + Date.now()
      })
    });
  }

  function shouldShowBreakdownApproval(goalDetail) {
    var status = String((goalDetail && (goalDetail.display_status || goalDetail.status)) || '');
    return status === 'pending_approval';
  }

  function shouldShowGoalSignOff(goalDetail) {
    return String((goalDetail && (goalDetail.display_status || goalDetail.status)) || '') === 'pending_completion';
  }

  function driverControlButtonsHtml(options) {
    options = options || {};
    var showSignOff = !!options.showSignOff;
    return (
      '<div class="cc-driver-controls">' +
      '<button type="button" class="cc-ghost-btn" data-driver-action="start">Start</button>' +
      '<button type="button" class="cc-ghost-btn" data-driver-action="pause">Pause</button>' +
      '<button type="button" class="cc-ghost-btn" data-driver-action="resume">Resume</button>' +
      '<button type="button" class="cc-ghost-btn" data-driver-action="halt">Halt</button>' +
      '<button type="button" class="cc-ghost-btn" data-driver-action="stop">Stop</button>' +
      (showSignOff
        ? '<button type="button" class="cc-primary-btn" data-goal-action="sign-off">Sign off completion</button>'
        : '') +
      '</div>'
    );
  }

  function buildGoalApprovalPanelHtml(goalDetail, goalId, projectId) {
    var status = goalStatusLabel(
      (goalDetail && (goalDetail.display_status || goalDetail.status)) || ''
    );
    var gid = escapeHtml(goalId);
    var pid = escapeHtml(projectId);
    var baseAttrs = ' data-goal-id="' + gid + '" data-project-id="' + pid + '"';

    if (shouldShowBreakdownApproval(goalDetail)) {
      var bVersion = (goalDetail && goalDetail.breakdown_version) || 1;
      return (
        '<article class="cc-card cc-approval-panel" id="ccGoalApprovalPanel">' +
        '<header class="cc-card-head"><h2>Your approval is needed</h2></header>' +
        '<p class="cc-card-desc">The plan for this goal is ready. Review the breakdown below, then approve to ' +
        'unlock Driver dispatch, or reject to mark it non-dispatchable.</p>' +
        '<dl class="cc-approval-meta">' +
        '<dt>Status</dt><dd>' + escapeHtml(status) + '</dd>' +
        '<dt>Breakdown version</dt><dd>' + escapeHtml(String(bVersion)) + '</dd>' +
        '<dt>Goal</dt><dd class="cc-mono">' + gid + '</dd>' +
        '</dl>' +
        '<div class="cc-form-actions">' +
        '<button type="button" class="cc-primary-btn" data-goal-action="approve-breakdown"' + baseAttrs +
        ' data-breakdown-version="' + escapeHtml(String(bVersion)) + '">Approve breakdown</button>' +
        '<button type="button" class="cc-ghost-btn" data-goal-action="reject-breakdown"' + baseAttrs +
        ' data-breakdown-version="' + escapeHtml(String(bVersion)) + '">Reject breakdown</button>' +
        '</div>' +
        '<div class="cc-meta-line cc-approval-result" id="ccGoalActionResult" data-governance-result></div>' +
        '</article>'
      );
    }

    if (shouldShowGoalSignOff(goalDetail)) {
      var signOffGate = CCGoalRunnerHelpers.computeSignOffGate({
        goalDetail: goalDetail,
        readiness: state.goalRunner.signOffReadinessCache[goalId]
      });
      var queueDetail = state.goalRunner.queueDetailsCache[goalId] || null;
      return (
        '<article class="cc-card cc-approval-panel" id="ccGoalApprovalPanel">' +
        '<header class="cc-card-head"><h2>Ready for sign-off</h2></header>' +
        '<p class="cc-card-desc">The Driver finished this goal. Review the results, then sign off to mark it complete.</p>' +
        '<dl class="cc-approval-meta">' +
        '<dt>Status</dt><dd>' + escapeHtml(status) + '</dd>' +
        '<dt>Goal</dt><dd class="cc-mono">' + gid + '</dd>' +
        '</dl>' +
        CCGoalRunnerHelpers.buildSignOffReadinessPanelHtml(
          state.goalRunner.signOffReadinessCache[goalId],
          queueDetail
        ) +
        '<div class="cc-form-actions">' +
        (signOffGate.ok
          ? '<button type="button" class="cc-primary-btn" data-goal-action="sign-off"' + baseAttrs +
            '>Sign off completion</button>'
          : '<div class="cc-meta-line">' + escapeHtml(signOffGate.reason) + '</div>') +
        '</div>' +
        '<div class="cc-meta-line cc-approval-result" id="ccGoalActionResult" data-governance-result></div>' +
        '</article>'
      );
    }

    if (String((goalDetail && goalDetail.status) || '') === 'completed') {
      return (
        '<article class="cc-card cc-approval-panel" id="ccGoalApprovalPanel">' +
        '<header class="cc-card-head"><h2>Goal completed</h2></header>' +
        CCGoalRunnerHelpers.buildCompletionMetadataHtml(goalDetail) +
        '<div class="cc-meta-line cc-approval-result" id="ccGoalActionResult" data-governance-result></div>' +
        '</article>'
      );
    }

    var idleMsg = status && status !== '—'
      ? 'No governance action is required for this goal right now.'
      : 'Inspect goal panels below for research, breakdown, and execution status.';
    return (
      '<article class="cc-card cc-approval-panel cc-approval-panel-idle" id="ccGoalApprovalPanel">' +
      '<header class="cc-card-head"><h2>Governance</h2></header>' +
      '<p class="cc-card-desc">' + escapeHtml(idleMsg) + '</p>' +
      '<dl class="cc-approval-meta">' +
      '<dt>Status</dt><dd>' + escapeHtml(status) + '</dd>' +
      '</dl>' +
      '<div class="cc-meta-line cc-approval-result" id="ccGoalActionResult" data-governance-result></div>' +
      '</article>'
    );
  }

  async function refreshAfterGovernanceAction(projectId, goalId) {
    try {
      state.driver = await govFetch(driverStatusPath());
    } catch (_driverErr) { /* optional */ }
    if (projectId) {
      await mergeProjectGoalsAndRuns(projectId);
      state.goalRunner.projectGoals = state.goals.filter(function (g) {
        return g.project_id === projectId;
      });
      state.goalRunner.projectRuns = state.runs.filter(function (r) {
        return r.project_id === projectId;
      });
    }
    renderAll();
    if (state.section === 'goals') {
      renderGoalFilterTabs();
      renderGoalList();
      if (goalId) {
        state.goalRunner.selectedGoalId = goalId;
        renderGoalList();
        await expandGoalCard(goalId, projectId);
      }
    }
    if (state.section === 'history' && projectId) {
      await loadHistoryForProject(state.history.selectedProjectId || projectId);
    }
  }

  function wireGovernanceActionsOnce() {
    var shell = $('ccShell');
    if (!shell || shell.dataset.govActionsWired === '1') return;
    shell.dataset.govActionsWired = '1';
    shell.addEventListener('click', function (ev) {
      var driverBtn = ev.target.closest('[data-driver-action]');
      var goalBtn = ev.target.closest('[data-goal-action]');
      if (!driverBtn && !goalBtn) return;
      if (governanceActionInFlight) return;

      void (async function () {
        governanceActionInFlight = true;
        var activeBtn = driverBtn || goalBtn;
        activeBtn.disabled = true;
        activeBtn.classList.add('cc-busy');
        var resultHost = (goalBtn && goalBtn.closest('[data-governance-result], .cc-approval-panel'))
          ? document.getElementById('ccGoalActionResult')
          : $('ccDriverActionResult');

        try {
          if (driverBtn) {
            var action = driverBtn.getAttribute('data-driver-action') || '';
            var pid = driverBtn.getAttribute('data-project-id') || state.goalRunner.selectedProjectId;
            var activeGoalId = driverBtn.getAttribute('data-goal-id') ||
              state.goalRunner.selectedGoalId ||
              (state.driver && state.driver.active_goal_id);
            if (action === 'start') {
              var cachedDetail = state.goalRunner.goalDetailsCache[activeGoalId] ||
                state.goalRunner.projectGoals.find(function (g) { return g.goal_id === activeGoalId; }) ||
                {};
              var readiness = null;
              try {
                readiness = await fetchDriverLaunchReadiness(activeGoalId, pid);
              } catch (_readinessErr) {
                readiness = state.goalRunner.launchReadinessCache[activeGoalId] || null;
              }
              var launchGate = CCGoalRunnerHelpers.computeDriverLaunchGate({
                goalDetail: cachedDetail,
                profile: state.goalRunner.selectedProfile || state.projectDetails[pid],
                connected: state.connected,
                readiness: readiness
              });
              if (!launchGate.ok) {
                if (resultHost) resultHost.textContent = launchGate.reason;
                return;
              }
            }
            await postDriverControl(action, activeGoalId, pid);
            await refreshAfterGovernanceAction(pid, activeGoalId);
          } else if (goalBtn) {
            var gAction = goalBtn.getAttribute('data-goal-action') || '';
            if (gAction === 'edit') return;
            var goalId = goalBtn.getAttribute('data-goal-id') || state.goalRunner.selectedGoalId;
            var projectId = goalBtn.getAttribute('data-project-id') || state.goalRunner.selectedProjectId;
            if (!goalId || !projectId) return;
            if (gAction === 'remove') {
              if (!window.confirm('Remove this goal? Pending plans will be rejected.')) return;
              var cached = state.goalRunner.goalDetailsCache[goalId] || {};
              var listGoal = state.goalRunner.projectGoals.find(function (g) {
                return g.goal_id === goalId;
              }) || {};
              await postGoalReject(
                goalId,
                projectId,
                cached.breakdown_version || listGoal.breakdown_version || 1,
                'removed_by_operator'
              );
              if (state.goalRunner.selectedGoalId === goalId) {
                state.goalRunner.selectedGoalId = null;
              }
              delete state.goalRunner.goalDetailsCache[goalId];
              await refreshAfterGovernanceAction(projectId, null);
              return;
            }
            if (gAction === 'sign-off') {
              if (!window.confirm('Sign off marks this goal complete in governance. Continue?')) {
                return;
              }
              var signOffDetail = state.goalRunner.goalDetailsCache[goalId] || {};
              var signOffReadiness = null;
              try {
                signOffReadiness = await fetchSignOffReadiness(goalId, projectId);
              } catch (_signOffErr) {
                signOffReadiness = state.goalRunner.signOffReadinessCache[goalId] || null;
              }
              var signOffGate = CCGoalRunnerHelpers.computeSignOffGate({
                goalDetail: signOffDetail,
                readiness: signOffReadiness
              });
              if (!signOffGate.ok) {
                if (resultHost) resultHost.textContent = signOffGate.reason;
                return;
              }
            }
            if (gAction === 'sign-off') {
              await postGoalSignOff(goalId, projectId);
            } else if (gAction === 'approve-breakdown') {
              var version = Number(goalBtn.getAttribute('data-breakdown-version') || 1);
              await postBreakdownApprove(goalId, projectId, version);
            } else if (gAction === 'reject-breakdown') {
              if (!window.confirm('Reject this breakdown? The goal will remain non-dispatchable.')) {
                return;
              }
              var rejectVersion = Number(goalBtn.getAttribute('data-breakdown-version') || 1);
              await postGoalReject(goalId, projectId, rejectVersion, 'rejected_by_operator');
            } else {
              return;
            }
            await refreshAfterGovernanceAction(projectId, goalId);
          }
        } catch (err) {
          var msg = String(err.message || err);
          if (err && err.detail && err.detail.blocking_reason) {
            msg = String(err.detail.display_reason || err.detail.blocking_reason).replace(/_/g, ' ');
          }
          if (resultHost) resultHost.textContent = msg;
        } finally {
          governanceActionInFlight = false;
          if (activeBtn) {
            activeBtn.disabled = false;
            activeBtn.classList.remove('cc-busy');
          }
        }
      })();
    });
  }

  function renderOverviewBody() {
    var host = $('ccOverviewBody');
    if (!host) return;
    var inboxCount = collectActionInboxItems().length;
    var buckets = goalStatusBuckets();
    var staleCount = platformStaleGoalCount();
    var recentRuns = state.runs.slice(0, 5);
    var runsHtml = recentRuns.length
      ? '<ul class="cc-overview-run-list">' + recentRuns.map(function (run) {
        var label = run.project_id ? projectLabel(run.project_id) : 'Run';
        return (
          '<li class="cc-overview-run-item">' +
          '<span class="cc-overview-run-project">' + escapeHtml(label) + '</span>' +
          '<span class="cc-overview-run-status">' + escapeHtml(String(run.status || run.state || 'unknown')) + '</span>' +
          '</li>'
        );
      }).join('') + '</ul>'
      : '<p class="cc-card-desc">No executions yet. Start work from the Goals tab.</p>';
    host.innerHTML =
      '<article class="cc-card cc-overview-secondary">' +
      '<header class="cc-card-head"><span>' + CCIcons.icon('runs') + '</span><h2>Recent executions</h2></header>' +
      runsHtml +
      '<div class="cc-overview-links">' +
      '<button type="button" class="cc-ghost-btn cc-quick-link" data-goto-section="goals">Open Goals' +
      (inboxCount ? ' (' + inboxCount + ' need you)' : '') + '</button>' +
      '<button type="button" class="cc-ghost-btn cc-quick-link" data-goto-section="projects">Projects</button>' +
      '<button type="button" class="cc-ghost-btn cc-quick-link" data-goto-section="history">History</button>' +
      '</div></article>' +
      '<article class="cc-card cc-overview-secondary">' +
      '<header class="cc-card-head"><span>' + CCIcons.icon('goals') + '</span><h2>Goal pipeline</h2></header>' +
      '<dl class="cc-overview-pipeline">' +
      '<div><dt>Needs you</dt><dd>' + inboxCount + '</dd></div>' +
      '<div><dt>In progress</dt><dd>' + buckets.pending + '</dd></div>' +
      '<div><dt>Complete</dt><dd>' + buckets.completed + '</dd></div>' +
      '<div><dt>Blocked</dt><dd>' + buckets.blocked + '</dd></div>' +
      (staleCount ? '<div><dt>Stale duplicates</dt><dd>' + staleCount + '</dd></div>' : '') +
      '</dl></article>';
    if (!host.dataset.quickLinksWired) {
      host.dataset.quickLinksWired = '1';
      host.addEventListener('click', function (ev) {
        var btn = ev.target.closest('[data-goto-section]');
        if (!btn) return;
        switchSection(btn.getAttribute('data-goto-section'));
      });
    }
  }

  function renderDriverPanelHost() {
    /* Driver controls live on each goal card in the Goals tab. */
  }

  function projectSelectOptions(values, selected) {
    return values.map(function (v) {
      var sel = v === selected ? ' selected' : '';
      return '<option value="' + escapeHtml(v) + '"' + sel + '>' + escapeHtml(v.replace(/_/g, ' ')) + '</option>';
    }).join('');
  }

  function renderProjectCard(project, detail) {
    var p = detail || project || {};
    var name = p.display_name || p.name || p.slug || p.project_id || 'project';
    var metaRows = CCGoalRunnerHelpers.formatProjectRegistryMeta(p);
    var pid = p.project_id || project.project_id || '';
    return (
      '<article class="cc-project-card" data-project-id="' + escapeHtml(pid) + '">' +
      '<div class="cc-project-head">' +
      '<div class="cc-project-avatar">' + CCIcons.icon('folder') + '</div>' +
      '<div><div class="cc-project-name">' + escapeHtml(name) + '</div>' +
      '<div class="cc-project-slug">' + escapeHtml(p.slug || '') + '</div></div></div>' +
      '<dl class="cc-project-meta">' +
      metaRows.map(function (row) {
        return '<div><dt>' + escapeHtml(row[0]) + '</dt><dd>' + escapeHtml(row[1]) + '</dd></div>';
      }).join('') +
      '</dl>' +
      '<div class="cc-project-card-actions">' +
      '<button type="button" class="cc-ghost-btn" data-work-project="' + escapeHtml(pid) + '">Work on this</button>' +
      '<button type="button" class="cc-project-edit-btn" data-edit-project="' + escapeHtml(pid) + '">Edit</button>' +
      '</div></article>'
    );
  }

  function readProjectForm() {
    return {
      slug: ($('ccProjectSlug') || {}).value || '',
      display_name: ($('ccProjectDisplayName') || {}).value || '',
      description: ($('ccProjectDescription') || {}).value || '',
      repo_path: ($('ccProjectRepoPath') || {}).value || '',
      status: ($('ccProjectStatus') || {}).value || 'active',
      default_validator: ($('ccProjectDefaultValidator') || {}).value || '',
      full_validator: ($('ccProjectFullValidator') || {}).value || '',
      research_mode: ($('ccProjectResearchMode') || {}).value || 'light',
      research_required: !!($('ccProjectResearchRequired') || {}).checked,
      memory_recall_mode: ($('ccProjectMemoryMode') || {}).value || 'light',
      memory_include_mimir: !!($('ccProjectMemoryInclude') || {}).checked,
      approval_mode: ($('ccProjectApprovalMode') || {}).value || 'manual_approval',
      architect_import_required: !!($('ccProjectArchitectImport') || {}).checked,
      architect_supervision_required: !!($('ccProjectArchitectSupervision') || {}).checked,
      goal_file: ($('ccProjectGoalFile') || {}).value || 'project_goals.md',
      budget_max_run_count: Number(($('ccProjectBudgetRuns') || {}).value || 5),
      budget_max_wall_clock_hours: Number(($('ccProjectBudgetHours') || {}).value || 4)
    };
  }

  function buildProjectFormHtml(mode, detail) {
    var p = detail || {};
    var budget = p.budget_defaults || {};
    var isCreate = mode === 'create';
    return (
      '<label class="cc-form-label">Slug<input id="ccProjectSlug" type="text" ' +
      (isCreate ? '' : 'readonly ') + 'value="' + escapeHtml(p.slug || '') + '" placeholder="my-project"></label>' +
      '<label class="cc-form-label">Display name<input id="ccProjectDisplayName" type="text" value="' +
      escapeHtml(p.display_name || p.name || '') + '"></label>' +
      '<label class="cc-form-label">Description<textarea id="ccProjectDescription" rows="2">' +
      escapeHtml(p.description || '') + '</textarea></label>' +
      '<label class="cc-form-label">Repo path<input id="ccProjectRepoPath" type="text" value="' +
      escapeHtml(p.repo_path || '') + '" placeholder="/home/you/Projects/my-repo"></label>' +
      '<div class="cc-form-row">' +
      '<label class="cc-form-label">Status<select id="ccProjectStatus">' +
      projectSelectOptions(['active', 'bench', 'archived'], p.status || 'active') +
      '</select></label>' +
      '<label class="cc-form-label">Goal file<input id="ccProjectGoalFile" type="text" value="' +
      escapeHtml(p.goal_file || 'project_goals.md') + '"></label></div>' +
      '<label class="cc-form-label">Default validator<input id="ccProjectDefaultValidator" type="text" value="' +
      escapeHtml(p.default_validator || '.venv/bin/pytest -q') + '"></label>' +
      '<label class="cc-form-label">Full validator (optional)<input id="ccProjectFullValidator" type="text" value="' +
      escapeHtml(p.validator_full || p.default_validator || '') + '"></label>' +
      '<div class="cc-form-row">' +
      '<label class="cc-form-label">Research mode<select id="ccProjectResearchMode">' +
      projectSelectOptions(['off', 'light', 'standard', 'deep'], p.research_mode || 'light') +
      '</select></label>' +
      '<label class="cc-form-label">Memory recall<select id="ccProjectMemoryMode">' +
      projectSelectOptions(['off', 'light', 'standard', 'deep'], p.memory_mode || 'light') +
      '</select></label>' +
      '<label class="cc-form-label">Approval mode<select id="ccProjectApprovalMode">' +
      projectSelectOptions(
        ['manual_approval', 'auto_approve_if_policy_clean', 'auto_run_if_policy_clean'],
        p.approval_mode || 'manual_approval'
      ) +
      '</select></label></div>' +
      '<label class="cc-form-check"><input id="ccProjectResearchRequired" type="checkbox"' +
      (p.research_required !== false ? ' checked' : '') + '> Research required before Oracle breakdown</label>' +
      '<label class="cc-form-check"><input id="ccProjectMemoryInclude" type="checkbox"' +
      (p.memory_include_mimir !== false ? ' checked' : '') + '> Include Mimir in memory recall</label>' +
      '<label class="cc-form-check"><input id="ccProjectArchitectImport" type="checkbox"' +
      (p.architect_import_required !== false ? ' checked' : '') + '> Architect import required</label>' +
      '<label class="cc-form-check"><input id="ccProjectArchitectSupervision" type="checkbox"' +
      (p.architect_supervision_required !== false ? ' checked' : '') + '> Architect supervision required</label>' +
      '<div class="cc-form-row">' +
      '<label class="cc-form-label">Budget max runs<input id="ccProjectBudgetRuns" type="number" min="1" value="' +
      escapeHtml(String(budget.max_run_count != null ? budget.max_run_count : 5)) + '"></label>' +
      '<label class="cc-form-label">Budget max hours<input id="ccProjectBudgetHours" type="number" min="0.1" step="0.1" value="' +
      escapeHtml(String(budget.max_wall_clock_hours != null ? budget.max_wall_clock_hours : 4)) + '"></label></div>' +
      '<div id="ccProjectFormError" class="cc-form-error"></div>' +
      '<div class="cc-form-actions">' +
      '<button type="button" class="cc-primary-btn" id="ccProjectSaveBtn">' +
      (isCreate ? 'Create project' : 'Save changes') + '</button>' +
      '<button type="button" class="cc-ghost-btn" id="ccProjectCancelBtn">Cancel</button></div>'
    );
  }

  function closeProjectEditor() {
    state.projectEditor.open = false;
    state.projectEditor.projectId = null;
    var modal = $('ccProjectModal');
    if (modal) modal.hidden = true;
  }

  async function openProjectEditor(mode, projectId) {
    state.projectEditor.mode = mode;
    state.projectEditor.projectId = projectId || null;
    state.projectEditor.open = true;
    var modal = $('ccProjectModal');
    var title = $('ccProjectModalTitle');
    var host = $('ccProjectFormHost');
    if (!modal || !host) return;
    modal.hidden = false;
    if (title) title.textContent = mode === 'create' ? 'Add project' : 'Edit project';
    host.innerHTML = '<div class="cc-meta-line">Loading…</div>';
    var detail = {};
    if (mode === 'edit' && projectId) {
      try {
        detail = state.projectDetails[projectId] || await govFetch('projects/' + encodeURIComponent(projectId));
        state.projectDetails[projectId] = detail;
      } catch (err) {
        detail = state.projects.find(function (p) { return p.project_id === projectId; }) || {};
        if (!detail.project_id) {
          host.innerHTML = '<div class="cc-form-error">' + escapeHtml(err.message) + '</div>';
          return;
        }
        state.projectDetails[projectId] = detail;
      }
    }
    host.innerHTML = buildProjectFormHtml(mode, detail);
    $('ccProjectSaveBtn').addEventListener('click', function () { void saveProject(); });
    $('ccProjectCancelBtn').addEventListener('click', closeProjectEditor);
  }

  async function saveProject() {
    var errHost = $('ccProjectFormError');
    if (state.projectEditor.saving) return;
    var form = readProjectForm();
    if (!form.display_name.trim()) {
      if (errHost) errHost.textContent = 'Display name is required.';
      return;
    }
    if (!form.repo_path.trim()) {
      if (errHost) errHost.textContent = 'Repo path is required.';
      return;
    }
    if (state.projectEditor.mode === 'create' && !form.slug.trim()) {
      if (errHost) errHost.textContent = 'Slug is required for new projects.';
      return;
    }
    state.projectEditor.saving = true;
    if (errHost) errHost.textContent = 'Saving…';
    try {
      if (state.projectEditor.mode === 'create') {
        await govFetch('projects', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(form)
        });
      } else {
        var updatePayload = Object.assign({}, form);
        delete updatePayload.slug;
        await govFetch('projects/' + encodeURIComponent(state.projectEditor.projectId) + '/update', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(updatePayload)
        });
      }
      closeProjectEditor();
      await refreshData({ showLoading: true, loadDetails: true });
    } catch (err) {
      if (errHost) errHost.textContent = String(err.message || err);
    } finally {
      state.projectEditor.saving = false;
    }
  }

  function wireProjectEditorChrome() {
    var addBtn = $('ccProjectAddBtn');
    if (addBtn && !addBtn.dataset.wired) {
      addBtn.dataset.wired = '1';
      addBtn.addEventListener('click', function () { void openProjectEditor('create'); });
    }
    var closeBtn = $('ccProjectModalClose');
    var backdrop = $('ccProjectModalBackdrop');
    if (closeBtn && !closeBtn.dataset.wired) {
      closeBtn.dataset.wired = '1';
      closeBtn.addEventListener('click', closeProjectEditor);
    }
    if (backdrop && !backdrop.dataset.wired) {
      backdrop.dataset.wired = '1';
      backdrop.addEventListener('click', closeProjectEditor);
    }
    var grid = $('ccProjectGrid');
    if (grid && !grid.dataset.wired) {
      grid.dataset.wired = '1';
      grid.addEventListener('click', function (ev) {
        var editBtn = ev.target.closest('[data-edit-project]');
        if (editBtn) {
          void openProjectEditor('edit', editBtn.getAttribute('data-edit-project'));
          return;
        }
        var workBtn = ev.target.closest('[data-work-project]');
        if (workBtn) {
          var pid = workBtn.getAttribute('data-work-project');
          state.goalRunner.selectedProjectId = pid;
          state.goalRunner.selectedGoalId = null;
          var projectSelect = $('ccGoalRunnerProject');
          if (projectSelect) projectSelect.value = pid;
          void loadGoalRunnerProjectProfile(pid).then(function () {
            switchSection('goals');
          });
        }
      });
    }
  }

  function renderProjects() {
    wireProjectEditorChrome();
    var grid = $('ccProjectGrid');
    var metaHost = $('ccProjectRegistryMeta');
    var intro = $('ccProjectsIntro');
    if (intro) {
      intro.textContent =
        'Each project links a codebase (repo path) to governance rules — validators, research depth, ' +
        'and approval policy. Add a project first, or select one to work on below.';
    }
    if (!grid) return;
    if (!state.projects.length) {
      grid.innerHTML = '<div class="cc-empty">No projects yet — click Add project to register one.</div>';
      if (metaHost) metaHost.textContent = '';
      return;
    }
    if (metaHost) {
      metaHost.textContent = state.projects.length + ' registered project(s)';
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
    var intro = $('ccRunsIntro');
    if (intro) {
      intro.textContent =
        'Past Driver executions across all projects. Select a goal above for full lifecycle detail.';
    }
    if (!host) return;
    if (!state.runs.length) {
      host.innerHTML = '<div class="cc-empty">No runs recorded yet.</div>';
      return;
    }
    var sorted = state.runs.slice().sort(function (a, b) {
      return (b.last_seq || b.started_seq || 0) - (a.last_seq || a.started_seq || 0);
    });
    host.innerHTML = sorted.slice(0, 20).map(function (r) {
      var pct = runProgressPct(r);
      var color = runBarColor(r);
      var summary = /complete|approved|released/.test(String(r.status || ''))
        ? 'Run finished with status ' + String(r.status || '').replace(/_/g, ' ')
        : 'Tier ' + (r.tier || '—') + ' · correlation ' + truncate(r.correlation_id || r.request_id || '—', 24);
      return (
        '<div class="cc-run-row">' +
        '<div class="cc-run-meta"><strong>' + escapeHtml(r._project_name || projectLabel(r.project_id)) + '</strong>' +
        '<div class="cc-run-summary">' + escapeHtml((r.run_id || '').slice(0, 12)) + '…</div>' +
        '<div class="cc-run-summary">' + escapeHtml(summary) + '</div></div>' +
        '<div><div class="cc-run-bar"><span style="width:' + pct + '%;background:' + color + '"></span></div></div>' +
        '<div class="' + statusClass(r.status) + '">' + escapeHtml(String(r.status || '—').replace(/_/g, ' ')) + '</div>' +
        '</div>'
      );
    }).join('');
  }

  function truncate(text, maxLen) {
    var s = String(text == null ? '' : text);
    if (s.length <= maxLen) return s;
    return s.slice(0, Math.max(0, maxLen - 1)) + '…';
  }

  function goalRunnerHelpHtml(title, body) {
    return (
      '<button type="button" class="cc-info-btn" title="' + escapeHtml(body) + '" aria-label="' +
      escapeHtml(title) + '">?</button>'
    );
  }

  function updateGoalRunnerRunButton() {
    var btn = $('ccGoalRunnerRun');
    var modeSelect = $('ccGoalRunnerRunMode');
    if (!btn || !modeSelect) return;
    var mode = modeSelect.value || 'draft_only';
    btn.textContent = CCGoalRunnerHelpers.RUN_MODE_BUTTON[mode] || 'Run goal';
  }

  function readGoalRunnerForm() {
    var projectSelect = $('ccGoalsProjectSelect') || $('ccGoalRunnerProject');
    return {
      projectId: (projectSelect && projectSelect.value) || state.goalRunner.selectedProjectId || '',
      statement: ($('ccGoalRunnerStatement') || {}).value || '',
      includeMemory: !!($('ccGoalRunnerIncludeMemory') || {}).checked,
      includeResearch: !!($('ccGoalRunnerIncludeResearch') || {}).checked,
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
    var loadSeq = ++projectLoadSeq;
    state.goalRunner.selectedProjectId = projectId;
    syncGoalProjectSelectors(projectId);
    var profile = resolveProjectProfile(projectId);
    if (!profile || (!profile.research_mode && !profile.profile_missing)) {
      try {
        profile = await govFetch('projects/' + encodeURIComponent(projectId));
        state.projectDetails[projectId] = profile;
      } catch (_fetchErr) {
        profile = profile || resolveProjectProfile(projectId);
      }
    }
    if (!profile) return;
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
    updateGoalRunnerRunButton();
    var maxRuns = $('ccGoalRunnerMaxRuns');
    if (maxRuns && profile.budget_defaults && profile.budget_defaults.max_run_count != null) {
      maxRuns.value = String(profile.budget_defaults.max_run_count);
    }
    var maxHours = $('ccGoalRunnerMaxHours');
    if (maxHours && profile.budget_defaults && profile.budget_defaults.max_wall_clock_hours != null) {
      maxHours.value = String(profile.budget_defaults.max_wall_clock_hours);
    }
    updateGoalRunnerWarnings();
    await loadGoalRunnerProjectActivity(projectId, loadSeq);
  }

  function goalStatusLabel(status) {
    return String(status || '—').replace(/_/g, ' ');
  }

  function renderGoalRunnerActivity() {
    var host = $('ccGoalRunnerActivity');
    if (!host) return;
    var goals = state.goalRunner.projectGoals || [];
    var runs = state.goalRunner.projectRuns || [];
    var selectedGoal = state.goalRunner.selectedGoalId;
    var goalRows = goals.length
      ? goals.slice().sort(function (a, b) {
          return (b.last_seq || 0) - (a.last_seq || 0);
        }).map(function (g) {
          var active = g.goal_id === selectedGoal ? ' cc-goal-list-item-active' : '';
          return (
            '<button type="button" class="cc-goal-list-item cc-goal-pick' + active + '" data-goal-id="' +
            escapeHtml(g.goal_id) + '">' +
            '<strong>' + escapeHtml(goalStatusLabel(g.display_status || g.status)) + '</strong>' +
            '<div class="cc-meta-line">' + escapeHtml(truncate(g.statement, 100)) + '</div>' +
            '<div class="cc-meta-line">goal_id: ' + escapeHtml(String(g.goal_id).slice(0, 12)) + '…</div>' +
            '</button>'
          );
        }).join('')
      : '<div class="cc-empty">No goals for this project yet.</div>';
    var runRows = runs.length
      ? runs.slice().sort(function (a, b) {
          return (b.last_seq || b.started_seq || 0) - (a.last_seq || a.started_seq || 0);
        }).slice(0, 12).map(function (r) {
          var pct = runProgressPct(r);
          return (
            '<div class="cc-run-row cc-run-row-compact">' +
            '<div class="cc-run-meta"><strong>' + escapeHtml(String(r.run_id || '').slice(0, 12)) + '…</strong>' +
            '<div class="cc-run-summary">' + escapeHtml(goalStatusLabel(r.status)) + ' · tier ' + escapeHtml(r.tier || '—') + '</div></div>' +
            '<div><div class="cc-run-bar"><span style="width:' + pct + '%;background:' + runBarColor(r) + '"></span></div></div>' +
            '</div>'
          );
        }).join('')
      : '<div class="cc-empty">No driver runs recorded for this project.</div>';
    host.innerHTML =
      '<article class="cc-card">' +
      '<header class="cc-card-head"><span>' + CCIcons.icon('goals') + '</span><h2>Goals for this project</h2></header>' +
      '<p class="cc-card-desc">Click a goal to see its progress, take action, or review results.</p>' +
      '<div class="cc-goal-list">' + goalRows + '</div></article>' +
      '<article class="cc-card">' +
      '<header class="cc-card-head"><span>' + CCIcons.icon('runs') + '</span><h2>Recent runs</h2></header>' +
      '<p class="cc-card-desc">Latest Driver executions for the selected project.</p>' +
      runRows + '</article>';
    host.querySelectorAll('[data-goal-id]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        void viewGoalLifecycle(btn.getAttribute('data-goal-id'), state.goalRunner.selectedProjectId);
      });
    });
  }

  async function archiveStaleGoalsForProject(projectId) {
    if (!projectId) return;
    var btn = $('ccArchiveStaleBtn');
    var repoPath = await resolveDriverRepoPath(projectId, null).catch(function () { return ''; });
    if (btn) btn.classList.add('cc-busy');
    try {
      var preview = await govFetch(
        'projects/' + encodeURIComponent(projectId) + '/goals/archive-stale',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ repo_path: repoPath || '', dry_run: true })
        }
      );
      var staleCount = preview.stale_count || (preview.goal_ids && preview.goal_ids.length) || 0;
      if (!staleCount) {
        window.alert('No stale duplicate goals to archive for this project.');
        return;
      }
      var ok = window.confirm(
        'Archive ' + staleCount + ' stale duplicate goal(s)? The newest open copy in each group is kept.'
      );
      if (!ok) return;
      await govFetch(
        'projects/' + encodeURIComponent(projectId) + '/goals/archive-stale',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ repo_path: repoPath || '', dry_run: false })
        }
      );
      await loadGoalRunnerProjectActivity(projectId);
      if (state.section === 'overview') {
        await loadGoalsAndRunsAcrossProjects();
        renderAll();
      }
    } catch (err) {
      window.alert(String(err.message || err));
    } finally {
      if (btn) btn.classList.remove('cc-busy');
    }
  }

  function updateArchiveStaleButton(staleCount) {
    var btn = $('ccArchiveStaleBtn');
    if (!btn) return;
    if (staleCount > 0) {
      btn.hidden = false;
      btn.textContent = 'Archive ' + staleCount + ' stale duplicate' + (staleCount === 1 ? '' : 's');
    } else {
      btn.hidden = true;
      btn.textContent = 'Archive stale duplicates';
    }
    if (!btn.dataset.wired) {
      btn.dataset.wired = '1';
      btn.addEventListener('click', function () {
        void archiveStaleGoalsForProject(state.goalRunner.selectedProjectId);
      });
    }
  }

  async function loadGoalRunnerProjectActivity(projectId, loadSeq) {
    if (!projectId) return;
    try {
      var results = await Promise.all([
        govFetch('goals?project_id=' + encodeURIComponent(projectId)),
        govFetch('runs?limit=24&project_id=' + encodeURIComponent(projectId))
      ]);
      if (loadSeq != null && loadSeq !== projectLoadSeq) return;
      state.goalRunner.projectGoals = results[0].goals || [];
      state.goalRunner.projectRuns = results[1].runs || [];
      await refreshLaunchReadinessForGoals(projectId, state.goalRunner.projectGoals);
      updateArchiveStaleButton(results[0].stale_count || 0);
      syncGoalsRunsForProject(projectId, state.goalRunner.projectGoals, state.goalRunner.projectRuns);
      if (!state.goalRunner.selectedGoalId && state.goalRunner.projectGoals.length) {
        var firstVisible = visibleProjectGoals()[0];
        if (firstVisible) state.goalRunner.selectedGoalId = firstVisible.goal_id;
      }
      renderGoalFilterTabs();
      renderGoalList();
    } catch (err) {
      var listHost = $('ccGoalList');
      if (listHost) {
        listHost.innerHTML = '<div class="cc-form-error">' + escapeHtml(err.message) + '</div>';
      }
    }
  }

  async function viewGoalLifecycle(goalId, projectId) {
    state.goalRunner.selectedGoalId = goalId;
    state.goalRunner.selectedProjectId = projectId;
    switchSection('goals');
    renderGoalList();
    void expandGoalCard(goalId, projectId);
  }

  async function renderGoalRunnerForm() {
    var controlsHost = $('ccGoalNewGoalHost') || $('ccGoalRunnerControls');
    if (!controlsHost) return;
    controlsHost.innerHTML = '<div class="cc-meta-line">Loading Goal Runner…</div>';
    try {
      if (!state.projects.length) {
        var data = await govFetch('projects');
        state.projects = data.projects || [];
      }
      var projectId = state.goalRunner.selectedProjectId || CCGoalRunnerHelpers.ANIMA_LINUX_PROJECT_ID;
      controlsHost.innerHTML =
        '<article class="cc-card cc-goal-new-card" id="ccGoalRunnerPanel">' +
        '<p class="cc-form-help">Submit a governed goal to the platform API. Oracle decomposes it; you approve before any Driver dispatch.</p>' +
        '<input type="hidden" data-goal-runner-field="project_id" id="ccGoalRunnerProject" value="' +
        escapeHtml(projectId) + '">' +
        '<div class="cc-meta-line" id="ccGoalRunnerProjectMeta"></div>' +
        '<label class="cc-form-label">' +
        '<span class="cc-form-label-head">What should be done? ' +
        goalRunnerHelpHtml('Goal statement help', CCGoalRunnerHelpers.GOAL_STATEMENT_HELP) +
        '</span>' +
        '<textarea data-goal-runner-field="statement" id="ccGoalRunnerStatement" rows="4" ' +
        'placeholder="Example: Add retry logic to the intake API with tests."></textarea></label>' +
        '<div class="cc-form-row">' +
        '<label class="cc-form-check"><input type="checkbox" id="ccGoalRunnerIncludeMemory"> Include Mimir memory recall</label>' +
        '<label class="cc-form-check"><input type="checkbox" id="ccGoalRunnerIncludeResearch"> Include Scout research</label>' +
        '</div>' +
        '<div class="cc-form-row">' +
        '<label class="cc-form-label">Budget max runs<input data-goal-runner-field="max_run_count" id="ccGoalRunnerMaxRuns" type="number" min="1" readonly></label>' +
        '<label class="cc-form-label">Budget max hours<input data-goal-runner-field="max_wall_clock_hours" id="ccGoalRunnerMaxHours" type="number" min="0.1" step="0.1" readonly></label>' +
        '</div>' +
        '<div class="cc-meta-line">Budget caps come from the project profile and are fixed for this breakdown version after approval.</div>' +
        '<div id="ccGoalRunnerWarnings"></div>' +
        '<div class="cc-form-actions">' +
        '<button type="button" class="cc-primary-btn" id="ccGoalRunnerRun">Create goal</button>' +
        '<button type="button" class="cc-ghost-btn" id="ccGoalRunnerRefresh">Refresh goals</button>' +
        '</div>' +
        '<div class="cc-meta-line" id="ccGoalRunnerResult"></div>' +
        '</article>';

      $('ccGoalRunnerRun').addEventListener('click', function () { void submitGoalIntake(); });
      $('ccGoalRunnerRefresh').addEventListener('click', function () {
        void loadGoalRunnerProjectActivity(state.goalRunner.selectedProjectId);
      });

      await loadGoalRunnerProjectProfile(
        state.goalRunner.selectedProjectId || CCGoalRunnerHelpers.ANIMA_LINUX_PROJECT_ID
      );
      state.goalRunner.wired = true;
      await loadGoalRunnerProjectActivity(
        state.goalRunner.selectedProjectId || CCGoalRunnerHelpers.ANIMA_LINUX_PROJECT_ID
      );
    } catch (err) {
      controlsHost.innerHTML = '<div class="cc-empty">' + escapeHtml(err.message) + '</div>';
    }
  }

  async function submitGoalIntake() {
    var resultHost = $('ccGoalRunnerResult');
    var form = readGoalRunnerForm();
    var validation = CCGoalRunnerHelpers.validateGoalStatement(
      form.statement,
      form.projectId,
      state.goalRunner.running,
      state.goalRunner.projectGoals
    );
    if (!validation.ok) {
      if (resultHost) resultHost.textContent = validation.error;
      if (validation.existingGoalId) {
        state.goalRunner.selectedGoalId = validation.existingGoalId;
        state.goalRunner.filterTab = CCGoalRunnerHelpers.goalFilterBucket(
          state.goalRunner.projectGoals.find(function (g) {
            return g.goal_id === validation.existingGoalId;
          }) || {}
        ) || 'active';
        renderGoalFilterTabs();
        renderGoalList();
      }
      return;
    }
    var repoPath = await resolveDriverRepoPath(form.projectId, null);
    var payload = CCGoalRunnerHelpers.buildGoalIntakePayload(
      form,
      state.goalRunner.selectedProfile,
      form.projectId,
      repoPath
    );
    if (resultHost) resultHost.textContent = 'Submitting governed goal…';
    state.goalRunner.running = true;
    try {
      var response = await govFetch(CCGoalRunnerHelpers.goalIntakePostPath(), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      state.goalRunner.lastResponse = response;
      state.goalRunner.selectedGoalId = response.goal_id || state.goalRunner.selectedGoalId;
      if ($('ccGoalRunnerStatement')) {
        $('ccGoalRunnerStatement').value = '';
      }
      if (resultHost) {
        resultHost.textContent =
          'Created — goal ' + truncate(response.goal_id || '—', 16) +
          ' · status ' + goalStatusLabel(response.display_status || response.status) +
          ' · breakdown v' + (response.breakdown_version || '—') +
          ' (awaiting approval; Driver not started)';
      }
      await loadGoalRunnerProjectActivity(form.projectId);
      if (response.goal_id) {
        state.goalRunner.filterTab = 'pending_review';
        renderGoalFilterTabs();
        renderGoalList();
        void expandGoalCard(response.goal_id, form.projectId);
      }
    } catch (err) {
      var msg = String(err.message || err);
      if (resultHost) resultHost.textContent = msg;
      if (/duplicate_goal|409/.test(msg)) {
        try {
          await loadGoalRunnerProjectActivity(form.projectId);
        } catch (_refreshErr) { /* ignore */ }
      }
    } finally {
      state.goalRunner.running = false;
    }
  }

  async function submitProjectGoalRun() {
    return submitGoalIntake();
  }

  async function refreshGoalRunnerView(options) {
    options = options || {};
    var response = options.response || state.goalRunner.lastResponse;
    var projectId = options.projectId || (response && response.project_id) || state.goalRunner.selectedProjectId;
    var goalId = options.goalId || (response && response.goal_id) || state.goalRunner.selectedGoalId;
    if (!goalId) return null;
    if (!response) {
      response = {
        goal_id: goalId,
        project_id: projectId,
        status: null,
        research: {},
        breakdown: {},
        driver: {}
      };
    }
    var goalDetail = null;
    var queuePayload = null;
    var driverPayload = null;
    var goalRunProjection = null;
    try {
      var fetches = [
        govFetch('goals/' + encodeURIComponent(goalId) + '?project_id=' + encodeURIComponent(projectId)),
        govFetch('goals/' + encodeURIComponent(goalId) + '/queue'),
        govFetch('goals/' + encodeURIComponent(goalId) + '/milestones').catch(function () { return null; }),
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
      var milestonesPayload = results[2];
      driverPayload = results[3];
      goalRunProjection = results[4] || null;
      if (!response.status && goalDetail) {
        response = Object.assign({}, response, {
          status: goalDetail.status,
          research: { status: goalDetail.research_status, mode: goalDetail.research_mode }
        });
      }
    } catch (_err) {
      goalDetail = goalDetail || {};
    }
    if (goalDetail) {
      state.goalRunner.goalDetailsCache[goalId] = goalDetail;
    }
    if (queuePayload) {
      state.goalRunner.queueDetailsCache[goalId] = queuePayload;
    }
    try {
      await fetchDriverLaunchReadiness(goalId, projectId);
    } catch (_launchReadyErr) { /* mirror falls back to client-side gate */ }
    if (shouldShowGoalSignOff(goalDetail)) {
      try {
        await fetchSignOffReadiness(goalId, projectId);
      } catch (_signOffReadyErr) { /* mirror falls back to client-side gate */ }
    }
    var panelsHtml =
      '<article class="cc-card"><header class="cc-card-head"><h2>Research</h2></header>' +
      CCGoalRunnerHelpers.buildResearchPanelHtml(response, goalDetail) + '</article>' +
      '<article class="cc-card"><header class="cc-card-head"><h2>Breakdown</h2></header>' +
      CCGoalRunnerHelpers.buildBreakdownPanelHtml(response, queuePayload, state.goalRunner.selectedProfile, milestonesPayload, goalDetail) + '</article>' +
      '<article class="cc-card"><header class="cc-card-head"><h2>Launch readiness</h2></header>' +
      CCGoalRunnerHelpers.buildLaunchReadinessPanelHtml(state.goalRunner.launchReadinessCache[goalId]) + '</article>' +
      (shouldShowGoalSignOff(goalDetail)
        ? '<article class="cc-card"><header class="cc-card-head"><h2>Sign-off readiness</h2></header>' +
          CCGoalRunnerHelpers.buildSignOffReadinessPanelHtml(
            state.goalRunner.signOffReadinessCache[goalId],
            queuePayload
          ) + '</article>'
        : '') +
      '<article class="cc-card"><header class="cc-card-head"><h2>Execution</h2></header>' +
      CCGoalRunnerHelpers.buildExecutionPanelHtml(response, driverPayload, response.run_mode || readGoalRunnerForm().runMode) + '</article>' +
      '<article class="cc-card"><header class="cc-card-head"><h2>Blocker / Recovery</h2></header>' +
      CCGoalRunnerHelpers.buildBlockerRecoveryPanelHtml(response, goalRunProjection) + '</article>' +
      '<article class="cc-card"><header class="cc-card-head"><h2>Memory</h2></header>' +
      CCGoalRunnerHelpers.buildMemoryPanelHtml(response) + '</article>' +
      '<article class="cc-card"><header class="cc-card-head"><h2>Outcome report</h2></header>' +
      CCGoalRunnerHelpers.buildOutcomePanelHtml(response, goalDetail) + '</article>';
    if (options.panelsTarget) {
      options.panelsTarget.innerHTML = panelsHtml;
    }
    return { goalDetail: goalDetail, panelsHtml: panelsHtml };
  }

  function renderAll() {
    renderStats();
    renderActionInbox();
    renderOverviewBody();
    renderProjects();
    var overviewIntro = $('ccOverviewIntro');
    if (overviewIntro) {
      overviewIntro.textContent =
        'Platform snapshot across all registered projects. Open Projects to manage repos, Goals to run work, History for run audit.';
    }
    var goalsIntro = $('ccGoalsIntro');
    if (goalsIntro) {
      goalsIntro.textContent =
        'Choose a project, submit a new goal, then manage goals here — filter by status, run the Driver per goal, approve, or sign off inline. ' +
        'The Driver is the autonomous executor; use the play/pause/stop icons on each goal card.';
    }
    var projectsIntro = $('ccProjectsIntro');
    if (projectsIntro) {
      projectsIntro.textContent =
        'All projects registered in Command Center. Add or edit repo paths, validators, and approval policy.';
    }
    var historyIntro = $('ccHistoryIntro');
    if (historyIntro) {
      historyIntro.textContent =
        'Execution history for the selected project. Expand a run for details.';
    }
    if (state.section === 'goals' && state.goalRunner.wired) {
      renderGoalsProjectSelect();
      renderNewGoalForm();
      renderGoalFilterTabs();
      renderGoalList();
    }
    if (state.section === 'history') {
      renderHistoryProjectSelect();
      renderHistoryList();
    }
  }

  async function refreshData(options) {
    options = options || {};
    if (refreshInFlight) return;
    refreshInFlight = true;
    var shell = $('ccShell');
    var showLoading = !!options.showLoading;
    if (showLoading && shell) shell.classList.add('cc-loading', 'cc-loading-manual');
    try {
      var projectsPayload = await govFetch('projects');
      state.projects = projectsPayload.projects || [];
      rebuildProjectIndex();
      seedProjectDetailsFromList();
      if (options.loadDetails) {
        await loadProjectDetails();
        await loadGoalsAndRunsAcrossProjects();
      } else if (state.goalRunner.selectedProjectId) {
        await mergeProjectGoalsAndRuns(state.goalRunner.selectedProjectId);
      }
      if (state.goalRunner.selectedProjectId) {
        state.goalRunner.projectGoals = state.goals.filter(function (g) {
          return g.project_id === state.goalRunner.selectedProjectId;
        });
        state.goalRunner.projectRuns = state.runs.filter(function (r) {
          return r.project_id === state.goalRunner.selectedProjectId;
        });
      }
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
      refreshInFlight = false;
      if (showLoading && shell) shell.classList.remove('cc-loading', 'cc-loading-manual');
      renderAll();
      if (!state.goalRunner.wired && state.section === 'goals') {
        void initGoalsTab();
      }
      if (state.section === 'history') {
        void loadHistoryForProject(state.history.selectedProjectId || state.goalRunner.selectedProjectId);
      }
    }
  }

  function init() {
    if (initialized) return;
    initialized = true;
    wireGovernanceActionsOnce();
    CCIcons.mount($('ccRefreshIcon'), 'refresh');
    buildNav();
    switchSection('overview');
    $('ccRefreshBtn').addEventListener('click', function () {
      void refreshData({ showLoading: true, loadDetails: true });
    });
    void refreshData({ showLoading: true, loadDetails: true });
    if (refreshTimerId) clearInterval(refreshTimerId);
    refreshTimerId = setInterval(function () {
      void refreshData({ showLoading: false, loadDetails: false });
    }, AUTO_REFRESH_MS);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
