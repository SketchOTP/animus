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

1646 290426 - First-run wizard: mark complete on final step paint; cfg_still_first_run + setup_completed_at; client-config first_run uses helper.

Files touched:
- animus-chat/setup_wizard/wizard_routes.py
- animus-chat/server.py
- animus-chat/app/index.html
- repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md

1655 290426 - Gumroad packaging: START_HERE.txt, docs/GUMROAD.md, README download section, build-release checklist, repo_map.

Files touched:
- START_HERE.txt
- docs/GUMROAD.md
- README.md
- build-release.sh
- repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md

1656 290426 - Release checklist: exclude animus-chat/animus.env from zip, zip leak self-test, generic /home/you paths in UI, README version pointer, .gitignore.

Files touched:
- build-release.sh
- .gitignore
- README.md
- animus-chat/app/index.html
- docs/GUMROAD.md
- repo_map.md
- project_knowledge.md
- project_history.md
- project_status.md


1705 290426 - Release zip trim: exclude Ghost3D, hermes tests/website, whatsapp-bridge node_modules; 55MB hard fail; INSTALL WhatsApp note; docs/status.

Files touched:
- build-release.sh
- INSTALL.md
- docs/GUMROAD.md
- scripts/phase3-smoke-checklist.md
- repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md

1720 290426 - Release zip: exclude internal continuity (project_*, repo_map, AGENTS, CLAUDE, .cursor*, setup_repo, animus-chat mirrors), hermes-agent/.cursor and AGENTS.md.

Files touched:
- build-release.sh
- docs/GUMROAD.md
- repo_map.md
- project_knowledge.md
- project_status.md
- project_history.md

1735 290426 - Remove public GitHub link from About; neutral update errors; installer origin via ANIMUS_GIT_ORIGIN_URL only; INSTALL + env example + GUMROAD note.

Files touched:
- animus-chat/app/index.html
- animus-chat/server.py
- installer/install.sh
- animus.env.example
- INSTALL.md
- docs/GUMROAD.md
- project_knowledge.md
- project_history.md
- project_status.md
- repo_map.md

1745 290426 - Restore default git origin in install.sh for Check for updates; ANIMUS_GIT_ORIGIN_URL override; INSTALL/GUMROAD/knowledge/status/repo_map.

Files touched:
- installer/install.sh
- animus.env.example
- INSTALL.md
- docs/GUMROAD.md
- project_knowledge.md
- project_status.md
- repo_map.md
- project_history.md


1718 290426 - Buyer updates guide (BUYER_UPDATES.md), install.sh reset only on fresh git init, docs cross-links.
Files touched:
- docs/BUYER_UPDATES.md
- installer/install.sh
- INSTALL.md
- START_HERE.txt
- docs/GUMROAD.md
- repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md

1725 290426 - Clarified Gumroad file updates do not auto-download to buyer machines (BUYER_UPDATES.md).
Files touched:
- docs/BUYER_UPDATES.md
- project_history.md

1736 290426 - Phase 8: manifest+zip updates (ANIMUS_UPDATE_URL), removed git from install+server, launch banner, build-release checks; animus-update-server sibling project.
Files touched:
- animus-chat/server.py
- animus-chat/app/index.html
- animus-chat/repo_map.md
- installer/install.sh
- animus.env.example
- build-release.sh
- INSTALL.md
- docs/BUYER_UPDATES.md
- docs/GUMROAD.md
- docs/animus-user-guide.md
- START_HERE.txt
- repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md
- /home/sketch/animus-update-server/server.py
- /home/sketch/animus-update-server/requirements.txt
- /home/sketch/animus-update-server/README.md
- /home/sketch/animus-update-server/.env.example
- /home/sketch/animus-update-server/.gitignore
- /home/sketch/animus-update-server/systemd/animus-updates.service

1745 290426 - animus-update-server: systemd + README use .venv uvicorn; warn against ~/.local/bin/uvicorn.
Files touched:
- /home/sketch/animus-update-server/systemd/animus-updates.service
- /home/sketch/animus-update-server/README.md
- project_history.md

1755 290426 - animus-update-server README: port 8765 already in use troubleshooting.
Files touched:
- /home/sketch/animus-update-server/README.md
- project_history.md

1758 290426 - animus-update-server: optional EnvironmentFile, .env from example+token, README 9977; synced user systemd unit.
Files touched:
- /home/sketch/animus-update-server/systemd/animus-updates.service
- /home/sketch/animus-update-server/README.md
- /home/sketch/animus-update-server/.env (generated, not committed)
- /home/sketch/.config/systemd/user/animus-updates.service
- project_knowledge.md
- project_history.md

1805 290426 - animus-update-server: /updates/* mirror routes + README Tailscale HTTP vs HTTPS and path-on-443; GUMROAD manifest URL note.
Files touched:
- /home/sketch/animus-update-server/server.py
- /home/sketch/animus-update-server/README.md
- docs/GUMROAD.md
- project_knowledge.md
- project_history.md

1812 290426 - Set ANIMUS_UPDATE_URL in animus.env.example; build zip; publish v1.0.0; animus-update-server StaticFiles for releases/zips (mount order fix).
Files touched:
- animus.env.example
- animus-v1.0.0.zip (regenerated)
- /home/sketch/animus-update-server/releases/latest.json
- /home/sketch/animus-update-server/releases/history.jsonl
- /home/sketch/animus-update-server/releases/zips/animus-v1.0.0.zip
- /home/sketch/animus-update-server/server.py
- /home/sketch/animus-update-server/README.md
- project_history.md

1815 290426 - animus-update-server: dual StaticFiles /updates/releases + /releases for Tailscale path strip; README note.
Files touched:
- /home/sketch/animus-update-server/server.py
- /home/sketch/animus-update-server/README.md
- project_history.md

1825 290426 - build-release.sh: exclude animus-update-server + scripts; zip leak grep for animus-update-server/; comment trim list fix (whatsapp path).
Files touched:
- build-release.sh
- repo_map.md
- project_history.md

1845 290426 - New sibling animus-site: Vercel marketing + Redis update API; animus.env.example Vercel URL; GUMROAD/INSTALL/repo_map/knowledge/status.
Files touched:
- /home/sketch/animus-site/ (new tree: index.html, updates.html, docs.html, css/, js/, assets/, api/, vercel.json, requirements.txt, runtime.txt, README.md, .gitignore, .env.example)
- animus.env.example
- docs/GUMROAD.md
- INSTALL.md
- repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md

1826 290426 - animus-site: vercel.json v2 builds (@vercel/static for HTML/CSS/JS/assets, @vercel/python for api); routes for latest/history/admin; removed runtime.txt; README deploy note; vercel --prod smoke OK.
Files touched:
- /home/sketch/animus-site/vercel.json
- /home/sketch/animus-site/README.md
- /home/sketch/animus-site/runtime.txt (deleted)
- /home/sketch/animus/project_history.md

1844 290426 - animus-site: lib_redis supports REDIS_URL (Vercel Upstash) plus KV_/UPSTASH_ REST fallbacks; README/.env.example; vercel --prod.
Files touched:
- /home/sketch/animus-site/lib_redis.py
- /home/sketch/animus-site/README.md
- /home/sketch/animus-site/.env.example
- /home/sketch/animus/project_history.md
- /home/sketch/animus/project_knowledge.md

1855 290426 - animus-site: ADMIN_TOKEN on Vercel Production; lib_redis TCP via redis package for REDIS_URL (REST token != wire password); requirements redis; publish v1.0.0; latest.py Cache-Control; README/.env.example.
Files touched:
- /home/sketch/animus-site/lib_redis.py
- /home/sketch/animus-site/requirements.txt
- /home/sketch/animus-site/api/latest.py
- /home/sketch/animus-site/README.md
- /home/sketch/animus-site/.env.example
- /home/sketch/animus/project_history.md
- /home/sketch/animus/project_knowledge.md

2310 290426 - animus-site: full dark marketing redesign (PNG logos, tokens, index/updates/docs, main.css, FAQ accordion, Gumroad default URL); copied logos from animus repo.
Files touched:
- /home/sketch/animus-site/index.html
- /home/sketch/animus-site/updates.html
- /home/sketch/animus-site/docs.html
- /home/sketch/animus-site/css/main.css
- /home/sketch/animus-site/js/main.js
- /home/sketch/animus-site/assets/ANIMUSLOGO.png
- /home/sketch/animus-site/assets/ANIMUSLOGOICON.png
- /home/sketch/animus-site/assets/ghostonlyicon.png
- project_history.md
- project_status.md
- project_knowledge.md
- repo_map.md

1928 290426 - animus-site: product-led ANIMUS redesign from actual PWA surfaces; stylized previews; docs/updates chrome; Vercel prod deploy.
Files touched:
- /home/sketch/animus-site/index.html
- /home/sketch/animus-site/updates.html
- /home/sketch/animus-site/docs.html
- /home/sketch/animus-site/css/main.css
- /home/sketch/animus-site/assets/screenshots/chat.svg
- /home/sketch/animus-site/assets/screenshots/wizard.svg
- /home/sketch/animus-site/assets/screenshots/settings.svg
- /home/sketch/animus-site/assets/screenshots/cron.svg
- project_history.md
- project_status.md
- project_knowledge.md
- repo_map.md

1931 290426 - Re-aliased animusai.vercel.app to the redesigned animus-site Vercel deployment and verified live HTML.
Files touched:
- project_history.md
- project_status.md
- project_knowledge.md

1939 290426 - Fixed animusai release notes stuck loading by adding static fallback content and external updates.js enhancer; deployed + re-aliased.
Files touched:
- /home/sketch/animus-site/updates.html
- /home/sketch/animus-site/js/updates.js
- project_history.md
- project_status.md
- project_knowledge.md
- repo_map.md

1944 290426 - animus-site homepage copy cleanup: changed hero/workspace text, removed internal paragraphs and stat bar, deployed + re-aliased.
Files touched:
- /home/sketch/animus-site/index.html
- /home/sketch/animus-site/css/main.css
- project_history.md
- project_status.md
- project_knowledge.md

1949 290426 - animus-site brand layout: header uses ghost icon; hero logo centered below header; deployed + re-aliased animusai.
Files touched:
- /home/sketch/animus-site/index.html
- /home/sketch/animus-site/updates.html
- /home/sketch/animus-site/docs.html
- /home/sketch/animus-site/css/main.css
- project_history.md
- project_status.md
- project_knowledge.md
- repo_map.md

2009 290426 - Gumroad zip readiness: excluded hermes-agent raw env/dev lock files, rebuilt animus-v1.0.0.zip, verified archive clean.
Files touched:
- .gitignore
- build-release.sh
- animus-v1.0.0.zip
- project_history.md
- project_status.md
- project_knowledge.md
- repo_map.md

2018 290426 - animus-site Gumroad launch link: wired all buy CTAs to the live Gumroad product, deployed and re-aliased animusai.
Files touched:
- /home/sketch/animus-site/js/main.js
- project_history.md
- project_status.md
- project_knowledge.md

2345 290426 - Fix empty skills on fresh install: run Hermes bundled skills sync once at ANIMUS server import (mirrors CLI startup).
Files touched:
- animus-chat/server.py
- repo_map.md
- project_knowledge.md
- project_history.md

0012 290426 - VERSION 1.0.1 + release zip; publish helper script for Vercel manifest (skills seed fix ships in zip).
Files touched:
- VERSION
- animus-v1.0.1.zip
- scripts/publish-animus-manifest.sh
- project_knowledge.md
- repo_map.md
- project_history.md

0910 300426 - animus-site: static releases/ + zip; vercel.json; README publish flow; manifest 1.0.1 Vercel download_url (animus-site-ruddy host).
Files touched:
- /home/sketch/animus-site/vercel.json
- /home/sketch/animus-site/releases/README.md
- /home/sketch/animus-site/README.md
- project_history.md

0912 300426 - publish script defaults to production ruddy host; project_knowledge publish/ADMIN_TOKEN notes.
Files touched:
- scripts/publish-animus-manifest.sh
- project_knowledge.md
- project_history.md

0915 300426 - Vercel: alias animusai.vercel.app to animus-site Production; republish manifest download_url on animusai; publish script defaults + README/releases/knowledge.
Files touched:
- scripts/publish-animus-manifest.sh
- /home/sketch/animus-site/releases/README.md
- /home/sketch/animus-site/README.md
- project_knowledge.md
- project_status.md
- project_history.md

1005 300426 - Git: committed and pushed main to GitHub (94241f9) — v1.0.1 prep, skills seed, buyer docs, ghostonlyicon, build-release, publish script; excluded stray animus-chat/whoami.
Files touched:
- (git commit 94241f9 — 24 files)
- project_history.md

0931 300426 - Seller Blob release UI (admin/release.html), release_upload API, release-and-publish script; preflight + Docker animus.env bootstrap; docs.
Files touched:
- /home/sketch/animus-site/admin/release.html
- /home/sketch/animus-site/api/release_upload.js
- /home/sketch/animus-site/js/release-admin.js
- /home/sketch/animus-site/package.json
- /home/sketch/animus-site/package-lock.json
- /home/sketch/animus-site/vercel.json
- /home/sketch/animus-site/README.md
- /home/sketch/animus-site/releases/README.md
- /home/sketch/animus-site/.gitignore
- /home/sketch/animus/scripts/release-and-publish.sh
- /home/sketch/animus/scripts/publish-animus-manifest.sh
- /home/sketch/animus/installer/preflight.sh
- /home/sketch/animus/docker/Dockerfile
- /home/sketch/animus/START_HERE.txt
- /home/sketch/animus/INSTALL.md
- /home/sketch/animus/docs/GUMROAD.md
- /home/sketch/animus/repo_map.md
- /home/sketch/animus/project_status.md
- /home/sketch/animus/project_knowledge.md
- /home/sketch/animus/project_history.md

1045 300426 - Seller publish page at /seller-publish.html (root static); docs link; redirect /admin/release.html; fix 404.
Files touched:

- /home/sketch/animus-site/seller-publish.html
- /home/sketch/animus-site/vercel.json

- /home/sketch/animus-site/docs.html
- /home/sketch/animus-site/README.md

- /home/sketch/animus-site/releases/README.md
- /home/sketch/animus/docs/GUMROAD.md

- /home/sketch/animus/scripts/publish-animus-manifest.sh
- /home/sketch/animus/repo_map.md

- /home/sketch/animus/project_status.md
- /home/sketch/animus/project_knowledge.md

- /home/sketch/animus/project_history.md
- (deleted /home/sketch/animus-site/admin/release.html)

1055 300426 - Redeployed animus-site Production (vercel --prod --yes); seller-publish 200 on deployment + animus-site-ruddy.
Files touched:

- project_history.md


0940 300426 - Buyer hostname policy: docs/examples only https://animusai.vercel.app; vercel alias set animusai to latest Production; project_status/knowledge/repo_map + animus.env.example + GUMROAD + animus-site README/releases.
Files touched:

- animus.env.example
- docs/GUMROAD.md

- project_status.md
- project_knowledge.md

- repo_map.md
- /home/sketch/animus-site/README.md

- /home/sketch/animus-site/releases/README.md
- project_history.md

1110 300426 - seller-private/ for local seller secrets; gitignore + build-release exclude + leak check + README + GUMROAD/repo_map/knowledge.
Files touched:

- .gitignore
- build-release.sh

- seller-private/README.md
- docs/GUMROAD.md

- repo_map.md
- project_knowledge.md

- project_history.md

1112 300426 - project_status: note seller-private/ folder.
Files touched:
- project_status.md
- project_history.md

1205 300426 - Git: pushed main to GitHub (de82914) — seller-private, preflight/Docker animus.env, animusai docs, release-and-publish; omitted animus-chat/whoami.
Files touched:

- (commit de82914 — 15 files; see git show)

