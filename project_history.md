# Project history (animus)

Chronological work log. Newest entries at the bottom.

0901 290426 - Added AGENTS.md and project continuity files (goal, status, history, knowledge, repo map).
Files touched:
- AGENTS.md
- project_goal.md
- project_status.md
- project_history.md
- project_knowledge.md
- repo_map.md

0908 290426 - Added setup_repo.md bootstrap guide and documented four-way rule mirroring.
Files touched:
- setup_repo.md
- project_status.md
- project_history.md
- project_knowledge.md
- repo_map.md

0914 290426 - Added token/repo_map/history-append efficiency rules to AGENTS and mirrors, setup_repo.md, and continuity docs.
Files touched:
- AGENTS.md
- CLAUDE.md
- .cursorrules
- .cursor/rules/operating_rules.md
- setup_repo.md
- project_status.md
- project_history.md
- project_knowledge.md

2145 290426 - Bootstrapped ANIMUS monorepo: copied animus-chat and hermes-agent, added control-plane routes, installer/Docker/docs, sanitisation, build-release.
Files touched:
- animus-chat/server.py
- animus-chat/hermes_runner.py
- animus-chat/cron_routes.py
- animus-chat/skills_routes.py
- animus-chat/setup_wizard/wizard_routes.py
- animus-chat/setup_wizard/__init__.py
- animus-chat/requirements.txt
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/app/manifest.json
- animus-chat/restart.sh
- animus-chat/TAILSCALE-SERVE.md
- animus-chat/systemd/hermes-chat.service
- animus-chat/repo_map.md
- animus-chat/project_history.md
- animus-chat/generate-icons.py
- animus-chat/hermes-chat.env.example
- animus-chat/animus.env.example
- hermes-agent/ (full tree copy; personal PEMs removed)
- installer/install.sh
- installer/preflight.sh
- docker/Dockerfile
- docker/docker-compose.yml
- docker/.env.example
- systemd/animus.service
- systemd/animus-agent.service
- docs/hermes-agent-patches.md
- docs/models.md
- docs/tailscale.md
- README.md
- INSTALL.md
- VERSION
- LICENSE
- .gitignore
- build-release.sh
- animus.env.example
- repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md
1011 290426 - Phase 2 UI: wizard, cron paths/polling/daemon/logs, model refresh/about, tooltips, build-release checks, wizard save-config keys+tailscale, docs Option C.
Files touched:
- animus-chat/app/index.html
- animus-chat/setup_wizard/wizard_routes.py
- build-release.sh
- docs/hermes-agent-patches.md
- project_status.md
- project_knowledge.md
- project_history.md
- repo_map.md
1200 290426 - Phase 3: cron logs (CLI+disk+error), skills capabilities+UI+detail, client-config wake lock, chat_data_dir alignment, token CSV/SSE, docs/build/smoke script.
Files touched:
- animus-chat/hermes_runner.py
- animus-chat/server.py
- animus-chat/cron_routes.py
- animus-chat/skills_routes.py
- animus-chat/setup_wizard/wizard_routes.py
- animus-chat/app/index.html
- docs/hermes-agent-patches.md
- build-release.sh
- INSTALL.md
- scripts/phase3-smoke-checklist.md
- project_status.md
- project_knowledge.md
- project_history.md
- repo_map.md
1245 290426 - Smoke checklist: document chat_data_dir (CHAT_DATA_DIR / ~/.hermes/chat), not ./data; setup/teardown options.
Files touched:
- scripts/phase3-smoke-checklist.md
1315 290426 - project_goal Phase 3/4 smoke + Docker + token check: CHAT_DATA_DIR, python3, wake lock paths; INSTALL Docker curls pipe to python3.
Files touched:
- project_goal.md
- INSTALL.md
- project_knowledge.md
- project_status.md
1345 290426 - Go-live operator tips: keys, SSE usage during smoke, screenshots during CHAT_DATA_DIR session, build-release after unset; checklist + goal cross-link.
Files touched:
- project_knowledge.md
- scripts/phase3-smoke-checklist.md
- project_goal.md
- repo_map.md
1415 290426 - Smoke step 2 PASS logged; hermes-agent-patches top note (v0.11.0, 778 commits drift, no hermes update); v1.1 rebase backlog; knowledge + status + repo_map.
Files touched:
- project_status.md
- docs/hermes-agent-patches.md
- project_knowledge.md
- repo_map.md
2345 290426 - Phase 5 wizard (providers+auth, model scope, skills manager, projects path, Tailscale+wake), Settings inference matrix, About+check updates API, branding Plan tab, build-release/installer checks.
Files touched:
- animus-chat/app/index.html
- animus-chat/server.py
- animus-chat/setup_wizard/wizard_routes.py
- animus-chat/skills_routes.py
- build-release.sh
- installer/install.sh
- project_status.md
- project_knowledge.md
- repo_map.md
- project_history.md

2355 290426 - Codex OAuth: non-blocking POST start + GET poll by poll_id; session probe moved to codex-auth-session.
Files touched:

- animus-chat/setup_wizard/wizard_routes.py
- animus-chat/app/index.html

- project_knowledge.md
- repo_map.md

- project_history.md

1123 290426 - Phase 5 coder smoke: API curls (codex start/status, check-path, tailscale-check, skills list), grep/static acceptance checks, `./build-release.sh` pass; documented results + check-updates git HEAD caveat in `project_status.md`.
Files touched:
- project_status.md
- project_knowledge.md
- project_history.md

1545 290426 - Git: initial commit on main, origin→git@github.com:SketchOTP/animus.git; removed nested hermes-agent/.git for flat tree; .gitignore **/*.flock; push blocked here (SSH publickey).

Files touched:
- .gitignore
- project_history.md

1132 290426 - check-updates: friendly errors when no git HEAD or missing origin/main; apply-update HEAD guard; install.sh fetch+checkout main; INSTALL troubleshooting; zip cap 55MB in build-release + docs; project_knowledge venv/update notes.
Files touched:
- animus-chat/server.py
- animus-chat/repo_map.md
- installer/install.sh
- INSTALL.md
- build-release.sh
- project_goal.md
- project_status.md
- project_knowledge.md
- repo_map.md
- scripts/phase3-smoke-checklist.md
- project_history.md

1209 290426 - Phase 6: cron async TZ/projects UI, Piper TTS+docs, skills create modal, chatModel Auto for cursor-agent, build-release greps.
Files touched:
- animus-chat/app/index.html
- build-release.sh
- docs/tts.md
- project_status.md
- project_knowledge.md
- repo_map.md
- project_history.md


1200 290426 - Phase 7: PWA path hints (no Browse), TTS server sync + test phrase, Claude Code models + matrix, token_usage API + chat/cron recording + UI by-source + CSV, Slack + SSH hosts settings/modals, docs/ssh.md, animus.env Slack vars, build-release checks.
Files touched:
- animus-chat/server.py
- animus-chat/token_usage.py
- animus-chat/integrations_slack.py
- animus-chat/ssh_routes.py
- animus-chat/cron_routes.py
- animus-chat/setup_wizard/wizard_routes.py
- animus-chat/app/index.html
- animus.env.example
- build-release.sh
- docs/ssh.md
- project_status.md
- project_knowledge.md
- repo_map.md
- project_history.md

1305 290426 - Plan Hermes completions record tokens via POST /api/tokens/record; skill responses hook usage when present; TTS Settings vertical flow (engine, voice, test); v1.1 backlog sshfs auto-mount; project docs.
Files touched:
- animus-chat/app/index.html
- project_status.md
- project_knowledge.md
- repo_map.md
- project_history.md

1311 290426 - Startup splash image: serve ANIMUSLOGO.png from app static (synced from repo root asset).
Files touched:
- animus-chat/app/index.html
- animus-chat/app/ANIMUSLOGO.png
- project_knowledge.md
- repo_map.md
- project_history.md

1313 290426 - Setup wizard welcome screen uses ANIMUSLOGOICON.png (bundled under animus-chat/app).
Files touched:
- animus-chat/app/index.html
- animus-chat/app/ANIMUSLOGOICON.png
- project_knowledge.md
- repo_map.md
- project_history.md

1314 290426 - Wizard Hermes step: explain why ANIMUS does not auto-run hermes update (patch policy); project_status + project_knowledge.
Files touched:
- animus-chat/app/index.html
- project_status.md
- project_knowledge.md
- project_history.md

1315 290426 - repo_map: wizard Hermes drift / no auto hermes-update note in app row.
Files touched:
- repo_map.md
- project_history.md

1320 290426 - Setup wizard step 1: title Agent check; success Agent is reachable only; no hermes --version pre dump; failure copy tightened.
Files touched:
- animus-chat/app/index.html
- project_knowledge.md
- project_status.md
- repo_map.md
- project_history.md

1325 290426 - Wizard welcome icon 56px → 84px (+50%); cache bump animus-icon-2.
Files touched:
- animus-chat/app/index.html
- project_history.md

1330 290426 - Wizard welcome icon 84px → 126px (+50%); cache bump animus-icon-3.
Files touched:
- animus-chat/app/index.html
- project_history.md

1335 290426 - Wizard welcome icon: 189px centered in fixed 126px slot so Welcome heading does not shift down.
Files touched:
- animus-chat/app/index.html
- project_history.md

1345 290426 - TTS Read aloud: fix radio layout crushed by global .field input{width:100%}; scoped #ttsBackendRadios overrides.
Files touched:
- animus-chat/app/index.html
- project_history.md
- project_knowledge.md

1355 290426 - Piper: installer fetch-piper-voices.sh (2 HF voices) wired into install.sh; docs/tts + INSTALL + animus.env.example + UI empty hint; repo_map.
Files touched:
- installer/fetch-piper-voices.sh
- installer/install.sh
- docs/tts.md
- INSTALL.md
- animus.env.example
- animus-chat/app/index.html
- project_knowledge.md
- repo_map.md
- project_history.md

1410 290426 - Piper: server auto-download default HF voices in background (tts_routes + lifespan); voices API fetching/error; UI poll; docs/INSTALL/repo_map/knowledge.
Files touched:
- animus-chat/tts_routes.py
- animus-chat/server.py
- animus-chat/app/index.html
- docs/tts.md
- INSTALL.md
- project_knowledge.md
- repo_map.md
- project_history.md

1411 290426 - animus.env.example: document SKIP_ANIMUS_PIPER_VOICES for Piper auto-download.
Files touched:
- animus.env.example
- project_history.md

1430 290426 - Piper: six default HF voices; browser TTS: auto presets (UK/US/AU M+F) + other-languages optgroup; docs/install/repo_map/knowledge.
Files touched:
- animus-chat/tts_routes.py
- installer/fetch-piper-voices.sh
- installer/install.sh
- animus-chat/app/index.html
- docs/tts.md
- INSTALL.md
- project_knowledge.md
- repo_map.md
- project_history.md

1505 290426 - Settings SSH host modal: scoped radio CSS (#sshFormAuthRadios); IdentitiesOnly + strict host toggles; reset checkboxes on add.
Files touched:
- animus-chat/app/index.html
- project_knowledge.md
- project_history.md
- repo_map.md

1525 290426 - Default TTS: Piper + voice en_GB-alan-medium (client + server config default); download/install order; docs/tts.
Files touched:
- animus-chat/app/index.html
- animus-chat/server.py
- animus-chat/tts_routes.py
- installer/fetch-piper-voices.sh
- docs/tts.md
- project_knowledge.md
- project_history.md
- project_status.md
- repo_map.md

1645 290426 - Settings: unread badge + wake lock toggles; per-thread notif unread (accent); HELP modal + docs/animus-user-guide.md + help_routes (/api/help/guide, /api/help/ask).
Files touched:
- animus-chat/app/index.html
- animus-chat/server.py
- animus-chat/help_routes.py
- docs/animus-user-guide.md
- project_knowledge.md
- project_history.md
- project_status.md
- repo_map.md

1712 290426 - Help center: tabbed UI (Home, Topics, FAQ, Ask); GET /api/help/guide returns topics_markdown + faq_markdown + topics[]; guide FAQ section expanded.
Files touched:
- animus-chat/app/index.html
- animus-chat/help_routes.py
- docs/animus-user-guide.md
- project_knowledge.md
- project_history.md

1735 290426 - Settings: hr above HELP, remove caption, center HELP button under Token usage.
Files touched:
- animus-chat/app/index.html
- project_history.md
1812 290426 - Desktop launcher: create-desktop-launcher.sh from install.sh; GET /api/animus/desktop-launcher; wizard one-time download on non-phone; INSTALL + env example.

Files touched:
- installer/create-desktop-launcher.sh
- installer/install.sh
- animus.env.example
- animus-chat/server.py
- animus-chat/app/index.html
- INSTALL.md
- repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md

1626 290426 - Chat empty state uses ghostonlyicon.png instead of SVG ghost; asset in app/.

Files touched:
- animus-chat/app/index.html
- animus-chat/app/ghostonlyicon.png
- animus-chat/repo_map.md
- repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md

1635 290426 - Branding + PWA: ghostonlyicon.png for sidebar/header, favicon, manifest icons, apple-touch, About, notifications; SW cache animus-v2; desktop launcher icon prefers ghost file.

Files touched:
- animus-chat/app/index.html
- animus-chat/app/manifest.json
- animus-chat/app/sw.js
- animus-chat/server.py
- installer/create-desktop-launcher.sh
- repo_map.md
- animus-chat/repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md

