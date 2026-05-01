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


0953 300426 - VERSION 1.0.2; ./build-release.sh produced animus-v1.0.2.zip (~28MB).
Files touched:

- VERSION
- animus-v1.0.2.zip (artifact, gitignored)

- project_status.md
- project_history.md

1011 300426 - Skills list + wizard step 4: re-seed bundled skills when .bundled_manifest missing; show list API errors in wizard.
Files touched:
- animus-chat/skills_routes.py
- animus-chat/server.py
- animus-chat/app/index.html
- project_status.md
- project_knowledge.md
- repo_map.md
- project_history.md

1024 300426 - Skills: re-sync bundled when manifest empty and no SKILL.md but bundle has skills; run seed before skills update-all.
Files touched:
- animus-chat/skills_routes.py
- animus-chat/server.py
- project_status.md
- project_knowledge.md
- repo_map.md
- project_history.md

1035 300426 - Dev install: sync-dev-systemd.sh, restart-after-code-change prefers animus.service, HERMES_HOME absolute in env examples + Docker ENV, INSTALL.md.
Files touched:
- scripts/sync-dev-systemd.sh
- animus-chat/restart-after-code-change.sh
- animus.env.example
- animus-chat/animus.env.example
- INSTALL.md
- docker/Dockerfile
- repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md
- animus.env (local, gitignored)

1104 300426 - Multi-device chat list: server convs always on init; refetch on visibility/pageshow; SW cache animus-v3; CHAT_SERVER_REV bump.
Files touched:
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/server.py
- repo_map.md
- project_knowledge.md
- project_status.md
- project_history.md
1105 300426 - Doc touch: animus-chat/repo_map.md + project_status SW cache string animus-v3.
Files touched:
- animus-chat/repo_map.md
- project_status.md
- project_history.md

1122 300426 - Settings UI: grouped compact panels, info tooltips, notification + inference active toggles; icon sidebar tabs (Tokens, Help); check-updates uses animusai default manifest + confirm/alert flow; server default manifest URL.
Files touched:
- animus-chat/app/index.html
- animus-chat/server.py
- animus.env.example
- repo_map.md
- animus-chat/repo_map.md
- project_history.md
- project_status.md
- project_knowledge.md

1235 300426 - Token tracker: flush chat SSE tail buffer so final usage line parses; accept data: without space; server SSE usage from choices[0], CRLF, input_tokens/output_tokens/total_tokens fallbacks.
Files touched:
- animus-chat/app/index.html
- animus-chat/server.py
- project_history.md
- project_knowledge.md
- project_status.md
- repo_map.md

1310 300426 - Chat/help proxy: allow missing HERMES_API_KEY when gateway has no API key; gateway_upstream_headers + live os.environ bearer; drop mistaken 503 on raw gateway models fetch.
Files touched:
- animus-chat/hermes_runner.py
- animus-chat/server.py
- animus-chat/help_routes.py
- project_history.md
- project_knowledge.md
- repo_map.md

1345 300426 - Diagnose “still” HERMES_API_KEY chat error: v1.0.2 zip shipped old server gate; VERSION 1.0.3 + CHAT_SERVER_REV bump + meta `chat_proxy_blocks_on_missing_hermes_api_key`; `./build-release.sh` → animus-v1.0.3.zip.
Files touched:
- VERSION
- animus-chat/server.py
- animus-v1.0.3.zip
- project_history.md
- project_status.md
- project_knowledge.md

1405 300426 - Harden stale-install path: installer/sync-animus-chat-from-zip.sh; /api/version + meta fingerprint; build-release rejects obsolete gate string; START_HERE/INSTALL/user-guide/env.example/restart script; VERSION 1.0.4 + animus-v1.0.4.zip.
Files touched:
- VERSION
- build-release.sh
- installer/sync-animus-chat-from-zip.sh
- installer/install.sh
- animus-chat/server.py
- animus-chat/restart-after-code-change.sh
- animus.env.example
- animus-chat/animus.env.example
- START_HERE.txt
- INSTALL.md
- docs/animus-user-guide.md
- repo_map.md
- project_status.md
- project_history.md
- project_knowledge.md
- animus-v1.0.4.zip

1425 300426 - animus-chat/sync-from-release-zip.sh for partial installs (no installer/); installer/sync wrapper; VERSION 1.0.5 + animus-v1.0.5.zip; START_HERE + INSTALL + repo_map + user-guide.
Files touched:
- VERSION
- animus-chat/server.py
- animus-chat/sync-from-release-zip.sh
- installer/sync-animus-chat-from-zip.sh
- START_HERE.txt
- INSTALL.md
- docs/animus-user-guide.md
- repo_map.md
- project_status.md
- project_history.md
- project_knowledge.md
- animus-v1.0.5.zip

1445 300426 - START_HERE + INSTALL: partial-tree sync must unzip sync-from-release-zip.sh first (file not on disk until extracted).
Files touched:
- START_HERE.txt
- INSTALL.md
- project_knowledge.md
- project_history.md
1245 300426 - Document HERMES_API_KEY vs API_SERVER_KEY; synced atlas animus.env from ~/.hermes/.env (operational).
Files touched:
- animus.env.example
- project_knowledge.md
- project_history.md
1310 300426 - v1.0.6 buyer hardening: API_SERVER_KEY fallback in hermes_runner, startup /v1/models probe + version/meta telemetry, merge-hermes-gateway-auth.py in install/preflight, docs + systemd Description + START_HERE systemctl --user.
Files touched:
- VERSION
- animus-chat/hermes_runner.py
- animus-chat/server.py
- animus-chat/restart-after-code-change.sh
- installer/install.sh
- installer/preflight.sh
- installer/merge-hermes-gateway-auth.py
- systemd/animus.service
- START_HERE.txt
- INSTALL.md
- animus.env.example
- docs/animus-user-guide.md
- build-release.sh
- repo_map.md
- animus-chat/repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md
- animus-v1.0.6.zip

1228 300426 - Confirmed ANIMUS monorepo after hermes-update analysis: animus-chat import server + build-release.sh pass; documented atlas hermes update stash conflicts (clean tree = stashed ANIMUS patches not reapplied).
Files touched:
- project_history.md
- project_knowledge.md
- project_status.md
1620 300426 - Token tracker: keep explicit zero SSE usage in normalizeUsagePayload; Tokens tab shows recent server rows when chart is empty; Hermes api_server _run_agent usage from run_conversation result.
Files touched:
- animus-chat/app/index.html
- hermes-agent/gateway/platforms/api_server.py
- project_status.md
- project_knowledge.md
- repo_map.md
- project_history.md


1235 300426 - Wired hermes project CLI in hermes_cli/main.py; synced monorepo hermes-agent to animus-fresh-install; Patch 6 in hermes-agent-patches.md; repo_map hermes-agent row; tests: hermes_chat_delivery + project_workspace (pytest in disposable env).
Files touched:
- hermes-agent/hermes_cli/main.py
- docs/hermes-agent-patches.md
- repo_map.md
- project_history.md
- project_status.md
- project_knowledge.md
1645 300426 - Codex Responses: capture usage from terminal SSE events and merge onto get_final_response() so session token counters populate for ANIMUS token tracker.
Files touched:
- hermes-agent/run_agent.py
- project_status.md
- project_knowledge.md
- project_history.md


1245 300426 - Repeated hermes-agent rsync to animus-fresh-install; restarted animus.service; isolated CHAT_DATA_DIR spot-check: hermes project init + append_cron_to_hermes_chat (project UUID); did not restart hermes-gateway.service (live ~/.hermes agent path).
Files touched:
- project_history.md
- project_status.md

1255 300426 - Pointed user hermes-gateway.service at animus-fresh-install/hermes-agent venv; HERMES_HOME=default; CHAT_DATA_DIR=animus/animus-chat/data; daemon-reload + restart; backup prior unit as hermes-gateway.service.bak-20260430-dpc; /v1/models probe pass.
Files touched:
- /home/sketch/.config/systemd/user/hermes-gateway.service
- /home/sketch/.config/systemd/user/hermes-gateway.service.bak-20260430-dpc
- project_history.md
- project_status.md
- project_knowledge.md

1310 300426 - Single-repo dev: hermes-gateway.service points at monorepo hermes-agent; scripts/sync-dev-systemd.sh writes user hermes-gateway.service from ROOT; repo_map + project docs; removed animus-fresh-install from gateway path.
Files touched:
- /home/sketch/.config/systemd/user/hermes-gateway.service
- scripts/sync-dev-systemd.sh
- repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md

1325 300426 - Removed dev sandbox directory /home/sketch/animus-fresh-install (~2GB); single-repo workflow only.
Files touched:
- (deleted) /home/sketch/animus-fresh-install/
- project_status.md
- project_knowledge.md
- project_history.md

1515 300426 - Chat assistant bubbles: show provider·model footer for all inference backends (not only OpenAI Codex Auto); rehydrate footer from stored inference_* when inference_label missing.
Files touched:
- animus-chat/app/index.html
- project_status.md
- project_knowledge.md
- repo_map.md
- project_history.md

1545 300426 - Settings Codex Sign in: delegated click on inference matrix root + TEXT_NODE target→parent for closest(); per-row .inf-codex-status; try/finally re-enable button (fixes no-op / stuck disabled; banner-only feedback was easy to miss below long matrix).
Files touched:
- animus-chat/app/index.html
- project_status.md
- project_knowledge.md
- project_history.md

1610 300426 - effectiveChatModelId: prefer inference_models[active] then chat_model before animus_selected_model localStorage; Active toggle + persistChatModelPicker sync inference_models + localStorage so chat/footer match Settings matrix model.
Files touched:
- animus-chat/app/index.html
- project_status.md
- project_knowledge.md
- project_history.md

1645 300426 - Codex OAuth: new hermes_cli/codex_device_oauth.py (extract from web_server); dashboard + ANIMUS use it; wizard_routes drops hermes subprocess; PWA opens verification_url; docs Patch 7 + repo_map.
Files touched:
- hermes-agent/hermes_cli/codex_device_oauth.py
- hermes-agent/hermes_cli/web_server.py
- animus-chat/setup_wizard/wizard_routes.py
- animus-chat/app/index.html
- docs/hermes-agent-patches.md
- repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md
1415 300426 - Buyer install: ensure-sshpass.sh from install.sh; Docker sshpass; INSTALL/START_HERE/docs/ssh/env/build-release/preflight/repo_map.
Files touched:
- installer/ensure-sshpass.sh
- installer/install.sh
- installer/preflight.sh
- docker/Dockerfile
- INSTALL.md
- START_HERE.txt
- docs/ssh.md
- animus.env.example
- build-release.sh
- repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md

1745 300426 - Settings inference matrix: Hermes snapshot on provider-status; POST sync-hermes-model; UI reflects Hermes default and syncs on model change / Active toggle / chat picker when bound.
Files touched:
- animus-chat/setup_wizard/wizard_routes.py
- animus-chat/app/index.html
- project_status.md
- project_knowledge.md
- project_history.md
- repo_map.md
1445 300426 - SSH password test: omit BatchMode=yes for password auth (OpenSSH disables it); PubkeyAuthentication=no + PreferredAuthentications password,kbd-interactive; CHAT_SERVER_REV bump; docs/repo_map/knowledge/status.
Files touched:
- animus-chat/ssh_routes.py
- animus-chat/server.py
- docs/ssh.md
- repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md

1530 300426 - Research: inventoried Hermes agent gateway/CLI/dashboard surfaces vs ANIMUS wiring (no code).
Files touched:
- project_history.md
- project_knowledge.md

1815 300426 - sync-hermes-model: support cursor-agent, claude-code (→anthropic), copilot-acp; Copilot PATH check; provider base_url env before resolve; mistral/groq/togetherai/cohere fallbacks; missing base →422 not 500.
Files touched:
- animus-chat/setup_wizard/wizard_routes.py
- project_status.md
- project_knowledge.md
- project_history.md

1645 300426 - Hermes backend wiring: cron→gateway /api/jobs, restart via dashboard/CLI, skills+tokens+dashboard client, gateway messaging panel, gateway schedule_tz PATCH, CHAT_SERVER_REV.
Files touched:
- animus-chat/hermes_service_client.py
- animus-chat/cron_routes.py
- animus-chat/server.py
- animus-chat/skills_routes.py
- animus-chat/token_usage.py
- animus-chat/setup_wizard/wizard_routes.py
- animus-chat/integrations_gateway_routes.py
- animus-chat/app/index.html
- animus.env.example
- hermes-agent/gateway/platforms/api_server.py
- repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md

1403 300426 - Settings Messaging: in-app Hermes gateway platform setup (API + UI); writes ~/.hermes/.env and config.yaml; legacy GET /api/integrations/hermes-gateway/* kept; removed integrations_gateway_routes.py.
Files touched:
- animus-chat/messaging_routes.py
- animus-chat/server.py
- animus-chat/app/index.html
- animus-chat/integrations_gateway_routes.py
- animus-chat/repo_map.md
- repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md

1415 300426 - Messaging Settings: SW cache animus-v4, reg.update() after register, purge/hard-reload hint, resilient fetch + legacy platforms fallback; clearer API failure copy; CHAT_SERVER_REV bump.
Files touched:
- animus-chat/app/sw.js
- animus-chat/app/index.html
- animus-chat/server.py
- animus-chat/repo_map.md
- repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md

1520 300426 - POST /api/restart/gateway: async background restart + 12s dashboard timeout (fix browser Failed to fetch); optional chaining on restart buttons; CHAT_SERVER_REV.
Files touched:
- animus-chat/server.py
- animus-chat/hermes_service_client.py
- animus-chat/app/index.html
- project_knowledge.md
- project_history.md

1545 300426 - GET /api/models: merge Hermes CLI rows for openai-codex/cursor-agent/claude-code when hermes_models_cache.json is gateway-only; fixes missing Codex in Settings; CHAT_SERVER_REV.
Files touched:
- animus-chat/server.py
- project_knowledge.md
- project_history.md

1610 300426 - Read aloud: Piper always selectable; tri-state /api/tts/backends probe; no forced browser fallback; tryReadAloudPiper gate; Messaging group id + border + SW animus-v5; CHAT_SERVER_REV.
Files touched:
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/server.py
- animus-chat/repo_map.md
- repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md

1745 300426 - Models: normalize gateway owned_by to matrix ids; refresh merges /v1/models; inference OAuth model pick when not signed in; Codex link + Cursor status/errors; SW animus-v6; CHAT_SERVER_REV.
Files touched:
- animus-chat/server.py
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md

1830 300426 - Added scripts/animus CLI (start/stop/restart/status); sync-dev-systemd.sh symlinks to ~/.local/bin; INSTALL + repo_map + project docs.
Files touched:
- scripts/animus
- scripts/sync-dev-systemd.sh
- INSTALL.md
- repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md

1845 300426 - Settings inference: Claude Code Sign in (server) + POST /api/setup/claude-code-login-start (claude setup-token); SW animus-v7; CHAT_SERVER_REV.
Files touched:
- animus-chat/setup_wizard/wizard_routes.py
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/server.py
- animus-chat/repo_map.md
- repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md

1920 300426 - Settings: collapsible Inference + Messaging (CSS grid slide); messaging per-platform On toggle + collapsible Configuration; SW animus-v8; CHAT_SERVER_REV.
Files touched:
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/server.py
- animus-chat/repo_map.md
- repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md

1645 300426 - Settings: sidebar shrink/collapse + width radios, Screen wake label, one info per section, removed Slack Integrations UI/modal; Messaging POST import-animus-slack; Plan play/stop icons; cron Slack hint → Settings; user guide + sw v9 + CHAT_SERVER_REV.
Files touched:
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/messaging_routes.py
- animus-chat/server.py
- animus-chat/repo_map.md
- docs/animus-user-guide.md
- project_status.md
- repo_map.md
- project_history.md
- project_knowledge.md

1530 300426 - Settings: sidebar label trim; Notifications + Read aloud collapsible (default collapsed); notification status only when actionable; Piper first in TTS; removed Voice engine / Piper hint copy; sw animus-v10; CHAT_SERVER_REV; user guide aligned.
Files touched:
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/server.py
- animus-chat/repo_map.md
- docs/animus-user-guide.md
- repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md

1645 300426 - Plan tab: remove intro; draft banner stamp+idea with edit/play/delete; clarification modal per question + cancel saves; draft fields clarifyQuestions/gapClarifyQuestions + answers arrays; sw v11; CHAT_SERVER_REV.
Files touched:
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/server.py
- animus-chat/repo_map.md
- docs/animus-user-guide.md
- repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md
1613 300426 - Cron UI: project scope + workdir, overseer + composed prompt/invariant, optimize-prompt API, dynamic deliver from messaging overview; gateway jobs workdir + prompt cap; client-config cron_overseer_prompt; SW animus-v12.
Files touched:
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/cron_routes.py
- animus-chat/server.py
- animus-chat/messaging_routes.py
- animus-chat/repo_map.md
- hermes-agent/gateway/platforms/api_server.py
- docs/hermes-agent-patches.md
- repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md

1625 300426 - Cron overseer collapsible (default closed); prompt optimizer new-btn styling + hourglass spinner; timezone Change opens dialog picker; sw animus-v13; CHAT_SERVER_REV.
Files touched:
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/server.py
- animus-chat/repo_map.md
- repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md


1730 300426 - Chat UI: 2x empty-state + main header ghost icon; remove sidebar head ghost; sw animus-v14; CHAT_SERVER_REV.
Files touched:
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/server.py
- animus-chat/repo_map.md
- repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md

1745 300426 - Fix chat branding: restore 2x ghost on sidebar ANIMUS; remove main header ghost; sw animus-v15; CHAT_SERVER_REV.
Files touched:
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/server.py
- animus-chat/repo_map.md
- repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md

1810 300426 - Default General project: server ensures projects_dir/general + projects.json; lifespan + wizard + client-config hooks; PWA session auto-open; sw animus-v16; CHAT_SERVER_REV.
Files touched:
- animus-chat/server.py
- animus-chat/setup_wizard/wizard_routes.py
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/repo_map.md
- repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md

1845 300426 - Projects sidebar: drag row reorder (gear excluded; ⋮⋮ affordance); persist projects.json + merge order; refetch projects on visibility; Screen wake settings title+toggle+info only; sw animus-v17; CHAT_SERVER_REV.
Files touched:
- animus-chat/server.py
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/repo_map.md
- repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md

1920 300426 - Projects: purple bold + add button (accent); list collapsed by default (localStorage 1/0); initial HTML + sw animus-v18; CHAT_SERVER_REV.
Files touched:
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/server.py
- animus-chat/repo_map.md
- repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md

1935 300426 - Add project + control: bold accent text only (no purple chip); sw animus-v19; CHAT_SERVER_REV.
Files touched:
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/server.py
- animus-chat/repo_map.md
- repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md

1950 300426 - Help sidebar tab SVG: overflow visible on rail icons; Feather-style ?-in-circle (r9, stroke caps); sw animus-v20; CHAT_SERVER_REV.
Files touched:
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/server.py
- animus-chat/repo_map.md
- repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md

2010 300426 - Cron tab: job row icon buttons (edit/run/pause-play/delete/logs order); add job + matches projects accent +; sw animus-v21; CHAT_SERVER_REV.
Files touched:
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/server.py
- animus-chat/repo_map.md
- repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md

2035 300426 - Settings sync: animus_ui_settings in config.json + GET ui_settings; client debounced POST on save + pullClientConfig on visibility; sw animus-v22; CHAT_SERVER_REV.
Files touched:
- animus-chat/server.py
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/repo_map.md
- repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md

2045 300426 - Cron Run now icon: clear stick-figure runner SVG; sw animus-v23; CHAT_SERVER_REV.
Files touched:
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/server.py
- animus-chat/repo_map.md
- repo_map.md
- project_history.md

2115 300426 - Plan: Stop pipeline anytime — shared requestPlanPipelineStop(); clarification modal Stop button (overlay hid toolbar stop); sw v24 + CHAT_SERVER_REV.
Files touched:
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/server.py
- animus-chat/repo_map.md
- repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md

2125 300426 - Plan draft banner: stamp format HHMM MMDDYY (was DDMMYY); sw v25 + CHAT_SERVER_REV.
Files touched:
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/server.py
- animus-chat/repo_map.md
- repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md

2138 300426 - Pushed main to origin (3156589): PWA/server/hermes/installer batch; excluded animus-chat/\${HOME}/, whoami, notes.md.
Files touched:
- (git push only; commit 3156589 on remote)
- project_history.md

2145 300426 - VERSION 1.0.7; ./build-release.sh produced animus-v1.0.7.zip (~31 MB).
Files touched:
- VERSION
- animus-v1.0.7.zip (gitignored artifact)
- project_status.md
- project_history.md

1741 300426 - Hardened beta Conversation mode loop so active mic hands-free flow auto-retries listening after empty/failed STT turns instead of stalling.
Files touched:
- animus-chat/app/index.html
- project_status.md
- project_knowledge.md
- repo_map.md
- project_history.md
1741 043026 — Chat: Let's add a new feature to Animus. In settings add a conversation mode with a toggle for on/off and → Implemented the Conversation Mode behavior you asked for in `animus-chat/app/index.html`, and tightened one key gap so i (hermes-chat)

1535 300426 - Documented chat STT env vars; Settings Read aloud hint when stt_backend none; docs/tts.md + animus.env.example; sw v26 + CHAT_SERVER_REV.
Files touched:
- animus.env.example
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/server.py
- docs/tts.md
- project_status.md
- project_knowledge.md
- repo_map.md
- project_history.md

1628 300426 - Embedded local STT: HERMES_CHAT_STT_LOCAL_EMBEDDED faster-whisper path for /api/stt/transcribe; transcribe_audio_force_local_faster_whisper in transcription_tools; requirements + docs + Patch 10.
Files touched:
- animus-chat/server.py
- animus-chat/requirements.txt
- animus-chat/app/index.html
- animus-chat/app/sw.js
- hermes-agent/tools/transcription_tools.py
- animus.env.example
- docs/tts.md
- docs/hermes-agent-patches.md
- project_status.md
- project_knowledge.md
- repo_map.md
- project_history.md

1645 300426 - Read aloud STT hint: refresh stt_backend from /api/hermes-chat-meta in renderTtsSettings and async onVoiceInputClick; applySttBackendFromMeta in init; clearer hint copy; sw v28 + CHAT_SERVER_REV.
Files touched:
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/server.py
- project_knowledge.md
- repo_map.md
- project_history.md

1712 300426 - Buyer/dev: enforce faster-whisper in animus-chat/requirements.txt via build-release.sh; INSTALL.md + START_HERE.txt + install.sh notes; requirements comment.
Files touched:
- animus-chat/requirements.txt
- build-release.sh
- installer/install.sh
- INSTALL.md
- START_HERE.txt
- project_status.md
- project_knowledge.md
- repo_map.md
- project_history.md

1745 300426 - Wired Settings Local/Online STT: postAnimusChatSttSource, Save/Clear key listeners, single-fetch renderTtsSettings bootstrap; sw v29 + CHAT_SERVER_REV; docs/tts.md; repo_map + status + knowledge.
Files touched:
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/server.py
- docs/tts.md
- repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md

1820 300426 - Conversation mode: purple rotating laser ring on mic while listening; normal red pulse when conversation off; sw v30 + CHAT_SERVER_REV.
Files touched:
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/server.py
- repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md

1845 300426 - Added python-multipart to animus-chat/requirements.txt for Starlette multipart (STT transcribe, attachments); repo_map + knowledge + status.
Files touched:
- animus-chat/requirements.txt
- repo_map.md
- project_knowledge.md
- project_status.md
- project_history.md

1846 300426 - build-release.sh: assert python-multipart in animus-chat/requirements.txt.
Files touched:
- build-release.sh
- project_history.md

1905 300426 - Buyer/dev bundle: document python-multipart in INSTALL.md, START_HERE.txt, docs/tts.md; install.sh echo + post-pip import check; repo_map build-release blurb.
Files touched:
- INSTALL.md
- START_HERE.txt
- docs/tts.md
- installer/install.sh
- repo_map.md
- project_knowledge.md
- project_status.md
- project_history.md

1906 300426 - animus-chat/repo_map.md: requirements.txt notes python-multipart + faster-whisper.
Files touched:
- animus-chat/repo_map.md
- project_history.md

1935 300426 - localhost ERR_FAILED: startup log tip for 127.0.0.1 bind; animus.env.example + START_HERE + INSTALL troubleshooting (IPv6 localhost vs IPv4 bind).
Files touched:
- animus-chat/server.py
- animus.env.example
- START_HERE.txt
- INSTALL.md
- project_knowledge.md
- project_history.md

2010 300426 - Read aloud STT/TTS layout + CSS; conversation mode send() finally always calls maybeContinue; faster-whisper beam for ANIMUS force path; docs/env/patch; sw v32 + CHAT_SERVER_REV.
Files touched:
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/server.py
- hermes-agent/tools/transcription_tools.py
- animus.env.example
- docs/tts.md
- docs/hermes-agent-patches.md
- repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md

2045 300426 - Conversation mode: defer assistant TTS text when maybeContinue re-enters during listen→send (fixes Piper/Web Speech stopping after first reply); sw v33 + CHAT_SERVER_REV.
Files touched:
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/server.py
- repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md

2105 300426 - Conversation mode Settings on: voice input button shows talking-head SVG; off: mic SVG; refreshVoiceInputButtonState + toggle handler; sw v34 + CHAT_SERVER_REV.
Files touched:
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/server.py
- repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md

1215 300426 - Default CHAT_HOST to :: (dual-stack) when unset; startup warning; env examples + INSTALL/START_HERE/tailscale; desktop launcher URL for ::/0.0.0.0; CHAT_SERVER_REV v35.
Files touched:
- animus-chat/server.py
- animus.env.example
- animus-chat/animus.env.example
- animus-chat/hermes-chat.env.example
- INSTALL.md
- START_HERE.txt
- docs/tailscale.md
- installer/create-desktop-launcher.sh
- project_knowledge.md
- project_status.md
- repo_map.md
- project_history.md

1235 300426 - CHAT_HOST=::: pre-bind socket with IPV6_V6ONLY=0 + uvicorn Server(sockets=) so 127.0.0.1 and localhost both work; CHAT_SERVER_REV v36; project_status/knowledge/repo_map.
Files touched:
- animus-chat/server.py
- project_status.md
- project_knowledge.md
- repo_map.md
- project_history.md

1245 300426 - VERSION 1.0.8; build-release animus-v1.0.8.zip; git push main (eadee74); release-and-publish.sh + publish-animus-manifest to animusai.
Files touched:
- VERSION
- project_status.md
- (commit: prior session files + v1.0.8)
- animus-v1.0.8.zip (artifact, gitignored)
- /home/sketch/animus-site/releases/animus-v1.0.8.zip
- project_history.md

1310 300426 - Projects sidebar: mergeProjectLists local-order preference while order dirty + sessionStorage; await flush path; sw animus-v35; CHAT_SERVER_REV v37; status/knowledge/repo_map.
Files touched:
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/server.py
- project_status.md
- project_knowledge.md
- repo_map.md
- project_history.md

2002 300426 - Wired model-agnostic skills capability by forcing API-server skills toolset and injecting ANIMUS chat skill guidance for recurring workflows.
Files touched:
- hermes-agent/gateway/platforms/api_server.py
- animus-chat/server.py
- animus-chat/app/index.html
- project_status.md
- project_knowledge.md
- repo_map.md
- project_history.md
2003 043026 — Chat: We need to make sure Animus can use the skills Hermes agent exposes and that like Hermes agent it ca → Implemented this so ANIMUS can consistently use Hermes skills across backends and nudge skill creation for recurring wor (hermes-chat)
2025 043026 — Chat: We need to know come up with a better memory system that's project specific currently we have projec → Yes — build a **project-local memory graph** and stop feeding full `project_history.md` into prompts. ## Proposed system (hermes-chat)

2102 300426 - Automated project bootstrap now mirrors AGENTS/CLAUDE/.cursorrules and seeds status/knowledge files for newly added project roots.
Files touched:
- hermes-agent/agent/project_workspace.py
- hermes-agent/tests/agent/test_project_workspace.py
- project_status.md
- project_knowledge.md
- repo_map.md
- project_history.md

2105 300426 - Repo-map refresh now ensures/mirrors workspace governance for existing projects and tests cover refresh-time policy/file repair.
Files touched:
- hermes-agent/agent/project_workspace.py
- hermes-agent/tests/agent/test_project_workspace.py
- project_status.md
- project_knowledge.md
- repo_map.md
- project_history.md

2107 300426 - Cron workdir runs now auto-enforce project governance/continuity files before agent execution.
Files touched:
- hermes-agent/cron/scheduler.py
- hermes-agent/tests/cron/test_cron_workdir.py
- project_status.md
- project_knowledge.md
- repo_map.md
- project_history.md

2111 300426 - Deep-pass hardened project continuity wiring by exposing status/knowledge in workspace APIs/UI and documenting refresh+cron continuity behavior in Help.
Files touched:
- animus-chat/server.py
- animus-chat/app/index.html
- docs/animus-user-guide.md
- project_status.md
- project_knowledge.md
- repo_map.md
- project_history.md

1420 300426 - VERSION 1.0.9; build-release excludes hermes-agent/.venv + animus-chat stray paths; animus-v1.0.9.zip ~28MB; git push main (e37aa96).
Files touched:
- VERSION
- build-release.sh
- project_status.md
- project_knowledge.md
- (commit: index.html, sw.js, server.py, docs, hermes-agent, repo_map, project_history)
- animus-v1.0.9.zip (artifact, gitignored)
- project_history.md

2118 010526 - Published animus-v1.0.9.zip: release-and-publish.sh + publish-animus-manifest (animusai).
Files touched:
- /home/sketch/animus-site/releases/animus-v1.0.9.zip (sibling deploy)
- project_history.md
2125 300426 - animus-site: dedupe release history API + Redis compact on publish; require publish notes (≥24 chars); ANIMUS_RELEASE_NOTES required in publish-animus-manifest.sh; seller UI + README.
Files touched:
- /home/sketch/animus-site/lib_release.py
- /home/sketch/animus-site/api/publish.py
- /home/sketch/animus-site/api/history.py
- /home/sketch/animus-site/js/release-admin.js
- /home/sketch/animus-site/seller-publish.html
- /home/sketch/animus-site/README.md
- /home/sketch/animus/scripts/publish-animus-manifest.sh
- /home/sketch/animus/scripts/release-and-publish.sh
- /home/sketch/animus/project_status.md
- /home/sketch/animus/project_knowledge.md
- /home/sketch/animus/project_history.md
- seller-private/README.md
2128 300426 - Deployed animus-site to Vercel Production; aliased animusai.vercel.app; verified GET /api/history (Redis dedupe live). Redis compact POST skipped (no seller-private/ADMIN_TOKEN on host).
Files touched:
- project_history.md
- project_status.md
- project_knowledge.md
2132 043026 — Chat: Was this the idea behoind the memory/map system that was supposed to cut down token use signiigatly? → You’re not missing anything — your read is correct. What you described **was intended** to reduce tokens, but it only wo (hermes-chat)
2139 300426 - Auto-refresh project_memory index for existing projects during ensure pass, and added regression test for stale/invalid index repair.
Files touched:
- hermes-agent/agent/project_workspace.py
- hermes-agent/tests/agent/test_project_workspace.py
- project_status.md
- project_knowledge.md
- project_history.md
2139 043026 — Chat: yes and make sure thats applied to our automated system for new and exsisitng projects → Code and tests are in: existing projects now get automatic compact-index refresh during normal ensure runs, and I added (hermes-chat)

2219 300426 - Plan tab: removed header Clear button and dead planDiscardOnNextPipelineEnd path (draft delete + listing delete + Stop); bumped sw.js animus-v36 and CHAT_SERVER_REV v38.
Files touched:
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/server.py
- project_status.md
- project_knowledge.md
- project_history.md
2340 300426 - Token tracker: normalize_usage reads dict-shaped usage; Codex _tok_sum dict support; regression tests.

Files touched:
- hermes-agent/agent/usage_pricing.py
- hermes-agent/run_agent.py
- hermes-agent/tests/agent/test_usage_pricing.py
- project_status.md
- project_knowledge.md
- project_history.md
- repo_map.md

2228 300426 - Restarted user hermes-gateway.service so ANIMUS gateway on 127.0.0.1:8642 loads bundled hermes-agent (token usage dict fix).

Files touched:
- project_history.md

2228 043026 — Chat: this is just a test just ack → Ack. (hermes-chat)
0235 010526 - Token tracker: run_conversation always normalises usage; rough in/out estimates when provider omits or all-zero; restart hermes-gateway.

Files touched:
- hermes-agent/run_agent.py
- project_status.md
- project_knowledge.md
- project_history.md

2235 043026 — Chat: this is jus a test. just ack → Ack. (hermes-chat)
0315 010526 - Token rough fallback: marginal message-token snapshot per user turn + estimate_tokens_rough for output (fix inflated input sums).

Files touched:
- hermes-agent/run_agent.py
- project_status.md
- project_knowledge.md
- project_history.md

2238 043026 — Chat: test → Ack. (hermes-chat)
0345 010526 - Token tracker chart: calendar day buckets + sqrt bar heights + chart overflow; sw animus-v37; CHAT_SERVER_REV v39.

Files touched:
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/server.py
- project_history.md


2243 300426 - Tokens tab: dedupe chat in mergeServerTokenEntries (server JSONL vs local msg.usage); summary note on input = full prompt; sw animus-v38; CHAT_SERVER_REV v40.
Files touched:
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/server.py
- project_knowledge.md
- project_history.md
- repo_map.md
2246 043026 — Chat: test → Ack. (hermes-chat)

2246 300426 - Tokens chart: stretch chart columns so bar stack % heights resolve (fix invisible bars); sw animus-v39; CHAT_SERVER_REV v41.
Files touched:
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/server.py
- project_knowledge.md
- project_status.md
- project_history.md
- repo_map.md

2249 300426 - Token rough fallback: first LLM-call input cap 16k -> 262144 (subscription Codex later turns vs real first turn).
Files touched:
- hermes-agent/run_agent.py
- project_knowledge.md
- project_status.md
- project_history.md

2256 300426 - Chat: per-conv Hermes session (ensureHermesSessionIds, conversation_id body); api_server derive + bogus header strip; slimmer project buildMessages; token summary + Codex usage fields; sw v40 CHAT_SERVER_REV v42.
Files touched:
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/server.py
- hermes-agent/gateway/platforms/api_server.py
- project_knowledge.md
- project_status.md
- project_history.md
- repo_map.md

2259 300426 - Project chat: persist merged ephemeral system in session DB (run_agent); ANIMUS buildMessages omits duplicate project system after hermes_project_session_primed; sw v41 CHAT_SERVER_REV v43.
Files touched:
- hermes-agent/run_agent.py
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/server.py
- project_knowledge.md
- project_status.md
- project_history.md
- repo_map.md

0634 010526 - Tokens chart: pixel-height bars, linear-gradient in/out split, fixed column width + day labels; tab chart min-height 180px; sw v42 CHAT_SERVER_REV v44.
Files touched:
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/server.py
- project_knowledge.md
- project_status.md
- project_history.md
- repo_map.md
1245 010526 - Chat: gateway hermes.session SSE + headers for stored system_prompt; ANIMUS buildMessages omits project block only when hermes_has_stored_system_prompt; SSE event parser + session_id reset clears flags; CHAT_SERVER_REV + sw cache bump.
Files touched:
- hermes-agent/gateway/platforms/api_server.py
- animus-chat/app/index.html
- animus-chat/server.py
- animus-chat/app/sw.js
- animus-chat/repo_map.md
- project_history.md
- project_knowledge.md
- project_status.md
- repo_map.md

2200 300426 - Tokens tab: current month day bars (color cycle), yearly chart, full log API (?full=1), Records CSV; sw v44 + CHAT_SERVER_REV v46.
Files touched:
- animus-chat/token_usage.py
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/server.py
- project_status.md
- project_knowledge.md
- repo_map.md
- project_history.md

1530 010526 - Hermes project session priming E2E: artifact artifacts/hermes_project_session_priming_e2e.md; gateway tests for hermes.session SSE + headers (test_api_server); .e2e-venv gitignore; repo_map + status + knowledge updates.
Files touched:
- artifacts/hermes_project_session_priming_e2e.md
- hermes-agent/tests/gateway/test_api_server.py
- hermes-agent/.gitignore
- animus-chat/repo_map.md
- repo_map.md
- project_status.md
- project_history.md
- project_knowledge.md

2235 300426 - Tokens: recent server log in collapsible details (default closed, open state resets by local day via sessionStorage); Records CSV appends server_recent_snapshot from serverRecentFull; sw v45 + rev v47.
Files touched:
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/server.py
- project_status.md
- project_knowledge.md
- project_history.md

2310 300426 - Tokens header: summary only; daily chart sqrt scale cap 3M; all-time monthly chart + yearly below; sw v46 + rev v48.
Files touched:
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/server.py
- project_status.md
- project_knowledge.md
- project_history.md

2345 300426 - Tokens breakdown: Day/Week/Month/Year total columns for provider, model, source; sw v47 + rev v49.
Files touched:
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/server.py
- project_status.md
- project_knowledge.md
- project_history.md

2355 300426 - Tokens: local 12h server log + time context line; CSV ts_local_12h + local date + # metadata; single nowMs for period math; sw v48 rev v50.
Files touched:
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/server.py
- project_status.md
- project_knowledge.md
- project_history.md

1615 010526 - Session priming stale-state fix: GET /v1/chat/session-prompt-status + ANIMUS preflight proxy; buildMessages binds hermes_stored_prompt_confirmed_session_id; reconcile before send; TestChatSessionPromptStatus; CHAT_SERVER_REV v51 sw v49; artifact updated PARTIAL.
Files touched:
- hermes-agent/gateway/platforms/api_server.py
- hermes-agent/tests/gateway/test_api_server.py
- animus-chat/server.py
- animus-chat/app/index.html
- animus-chat/app/sw.js
- artifacts/hermes_project_session_priming_e2e.md
- project_status.md
- project_knowledge.md
- project_history.md
- repo_map.md
- animus-chat/repo_map.md

1645 010526 - Hermes session priming artifact: added live E2E proof checklist (§1–§2), PASS gate, status table; project_status priority #3 for operator capture.
Files touched:
- artifacts/hermes_project_session_priming_e2e.md
- project_status.md
- project_history.md

0045 010526 - Re-applied Tokens tab UI: server log details/summary flex+chevron inside box; chart blocks + spread bars + surface3 track; sw v50 + CHAT_SERVER_REV v52 (prior layout commit lost).
Files touched:
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/server.py
- project_history.md

0715 050126 — Chat: Say the ANIMUS project workspace path in one line. → `/home/sketch/animus/hermes-agent` (hermes-chat)
0716 050126 — Chat: What is the exact project name string from the project block (not the folder leaf)? Reply one phrase → home-sketch-animus (hermes-chat)
0115 010526 - Tokens: displayProviderLabel maps JSONL provider slug unknown to human-readable note; sw v51 + CHAT_SERVER_REV v53.
Files touched:
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/server.py
- project_history.md

0718 050126 — Chat: Say the ANIMUS project workspace path in one line. → `/home/sketch/animus/` (hermes-chat)
0718 050126 — Chat: What is the exact project name string from the project block (not the folder leaf)? Reply one phrase → animus (hermes-chat)
0720 050126 — Chat: After a DB reset, acknowledge in one word: RESEND → RESEND (hermes-chat)
0721 050126 — Chat: After a DB reset, acknowledge in one word: RESEND → RESEND (hermes-chat)
0723 050126 — Chat: After a DB reset, acknowledge in one word: RESEND → RESEND (hermes-chat)
0724 050126 — Chat: After a DB reset, acknowledge in one word: RESEND → RESEND (hermes-chat)

0727 010526 - Hermes project session priming: live-stack E2E evidence pasted in artifacts/hermes_project_session_priming_e2e.md §2 (PASS); project_status priority #3 cleared; project_knowledge gateway/SQLite path note.
Files touched:
- artifacts/hermes_project_session_priming_e2e.md
- project_status.md
- project_knowledge.md
- project_history.md
0731 010526 - Inferred cursor-coding token bucket for /api/chat without hermes_provider (composer model + Cursor UA); Tokens UI label; user guide; v54 rev + sw v52.
Files touched:
- animus-chat/server.py
- animus-chat/app/index.html
- animus-chat/app/sw.js
- docs/animus-user-guide.md
- project_status.md
- project_knowledge.md
- animus-chat/repo_map.md
- project_history.md
0735 010526 - PWA X-Animus-Client web marker + token_usage animus_client field; Cursor inference only without marker; CSV + server log tag.
Files touched:
- animus-chat/token_usage.py
- animus-chat/server.py
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/repo_map.md
- docs/animus-user-guide.md
- project_status.md
- project_knowledge.md
- repo_map.md
- project_history.md
0739 010526 - Expanded animus_client slugs (chat/plan/skills/wizard/help/cron/prompt-optimizer/web); server stamps help+cron+optimizer; CSV/log tags; wizard token source.
Files touched:
- animus-chat/token_usage.py
- animus-chat/server.py
- animus-chat/cron_routes.py
- animus-chat/help_routes.py
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/repo_map.md
- docs/animus-user-guide.md
- project_status.md
- project_knowledge.md
- repo_map.md
- project_history.md

0912 300426 - Added unittest suite for allowlisted animus_client token JSONL (tokens/record, help, cron, prompt-optimizer).
Files touched:
- animus-chat/tests/__init__.py
- animus-chat/tests/test_token_usage_animus_client.py
- animus-chat/repo_map.md
- project_status.md
- project_history.md
- project_knowledge.md
- repo_map.md

0945 300426 - Recorded animus_client verification scope: PASS server-side contract; out of scope chat SSE / CSV / UI E2E.
Files touched:
- project_status.md
- project_knowledge.md
- project_history.md
0801 010526 - Documented Token Tracker end-to-end in artifacts/token_tracker_tab_explained.md; extended token usage unittest (GET full=1 + static CSV/UI checks).
Files touched:
- artifacts/token_tracker_tab_explained.md
- animus-chat/tests/test_token_usage_animus_client.py
- project_history.md
- project_knowledge.md
- project_status.md
- repo_map.md
0817 010526 - Tokens tab: ANIMUS client breakdown (aggregateAnimusClientTotals + renderAnimusClientBreakdown), source tab labeled logging; sw animus-v55; CHAT_SERVER_REV v57; tests + artifact doc.
Files touched:
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/server.py
- animus-chat/tests/test_token_usage_animus_client.py
- animus-chat/repo_map.md
- artifacts/token_tracker_tab_explained.md
- project_status.md
- project_knowledge.md
- repo_map.md
- project_history.md
0824 010526 - Token tracker artifact: aligned PASS/PARTIAL framing + optional browser E2E checklist (§10); project_knowledge browser E2E note.
Files touched:
- artifacts/token_tracker_tab_explained.md
- project_knowledge.md
- project_history.md
0832 010526 - Tokens tab: auto-refresh renderTokenUsageModal every 10 min while tab active and visible; sw animus-v56; CHAT_SERVER_REV v58.
Files touched:
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/server.py
- animus-chat/tests/test_token_usage_animus_client.py
- animus-chat/repo_map.md
- artifacts/token_tracker_tab_explained.md
- project_knowledge.md
- project_status.md
- project_history.md
0834 010526 - Tokens tab: collapsible chart sections (details/summary); This month + By year default collapsed, All months default open; chart reflow on expand; sw animus-v57; CHAT_SERVER_REV v59.
Files touched:
- animus-chat/app/index.html
- animus-chat/app/sw.js
- animus-chat/server.py
- animus-chat/tests/test_token_usage_animus_client.py
- animus-chat/repo_map.md
- artifacts/token_tracker_tab_explained.md
- project_knowledge.md
- project_status.md
- repo_map.md
- project_history.md
0836 050126 — Chat: test → Ack. (hermes-chat)
0836 050126 — Chat: test2 → Ack. (hermes-chat)
0839 010526 - v1.1.0: Help user guide Tokens tab (charts, auto-refresh, ANIMUS client vs logging); VERSION 1.1.0; build-release excludes .e2e-venv and artifacts/; git push main; animus-v1.1.0.zip + Vercel deploy + manifest publish.
Files touched:
- docs/animus-user-guide.md
- VERSION
- build-release.sh
- .gitignore
- (commit dad6d95: animus-chat, hermes-agent, scripts, project docs, project_memory, notes.md, etc.)

0842 010526 - Post v1.1.0 docs: repo_map zip + build-release excludes; project_status v1.1.0 ship line; project_knowledge .e2e-venv zip cap lesson.
Files touched:
- repo_map.md
- project_status.md
- project_knowledge.md
- project_history.md

0845 010526 - After v1.1.0 Vercel deploy: vercel alias set production deployment → animusai.vercel.app so /releases/animus-v1.1.0.zip matches manifest download_url.
Files touched:
- (Vercel alias only; no repo files)

