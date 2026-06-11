/** Governance hub — BFF-backed Registry / Runs views (Command Brief overlay tabs). */
(function () {
  const PLATFORM_PROJECT_ID = '260c61b1-f774-5493-8ff3-97e0d750f58c';
  const CANONICAL_RUN_ID = 'a1dfc5a6-a1b3-4bc8-86b9-a7910f0aaae1';

  function $(id) {
    return document.getElementById(id);
  }

  async function govFetch(path) {
    const resp = await fetch('/api/governance/' + path.replace(/^\//, ''), {
      headers: { Accept: 'application/json' },
    });
    const body = await resp.json().catch(() => ({}));
    if (!resp.ok) {
      const detail = body.detail || body.error || resp.statusText;
      throw new Error(String(detail || 'governance_fetch_failed'));
    }
    return body;
  }

  function setGovernanceTab(tab) {
    const tabs = ['brief', 'projects', 'runs'];
    for (const name of tabs) {
      const panel = $('governancePanel' + name.charAt(0).toUpperCase() + name.slice(1));
      const btn = $('governanceTab' + name.charAt(0).toUpperCase() + name.slice(1));
      if (panel) panel.hidden = name !== tab;
      if (btn) btn.classList.toggle('active', name === tab);
    }
    if (tab === 'projects') void renderGovernanceProjects();
    if (tab === 'runs') void renderGovernanceRuns();
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
        const animusId = p.animus_project_id ? ` · animus ${p.animus_project_id.slice(0, 8)}…` : '';
        card.innerHTML =
          '<div class="command-brief-card-title">' +
          '<strong>' + (p.display_name || p.slug || p.project_id) + '</strong>' +
          '<span class="command-brief-status">' + (p.status || 'active') + '</span></div>' +
          '<div class="command-brief-meta">' + (p.slug || '') + animusId + '</div>' +
          '<ul class="command-brief-list">' +
          (p.repos || []).map((r) => '<li>' + (r.repo_path || r.repo_id) + '</li>').join('') +
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
      const [timeline, verification, release] = await Promise.all([
        govFetch('runs/' + encodeURIComponent(runId) + '/timeline'),
        govFetch('runs/' + encodeURIComponent(runId) + '/verification').catch(() => null),
        govFetch('runs/' + encodeURIComponent(runId) + '/release').catch(() => null),
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
        '</div>';
    } catch (err) {
      host.innerHTML = '<div class="command-brief-err">' + String(err.message || err) + '</div>';
    }
  }

  function wireGovernanceTabsOnce() {
    const bar = $('governanceTabBar');
    if (!bar || bar.dataset.wired) return;
    bar.dataset.wired = '1';
    bar.querySelectorAll('[data-governance-tab]').forEach((btn) => {
      btn.addEventListener('click', () => setGovernanceTab(btn.getAttribute('data-governance-tab') || 'brief'));
    });
  }

  window.AnimusGovernanceHub = {
    activateTab: setGovernanceTab,
    refreshProjects: renderGovernanceProjects,
    refreshRuns: renderGovernanceRuns,
    wire: wireGovernanceTabsOnce,
  };

  document.addEventListener('DOMContentLoaded', wireGovernanceTabsOnce);
})();
