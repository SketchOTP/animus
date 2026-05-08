````md
# COLD START DIRECTIVE — Animus Model Router Plugin

## Objective

Build a new standalone Python module for Animus called the **Model Router Plugin**.

This module must route chat/model requests through available local CLI providers:

- Cursor CLI
- OpenAI Codex CLI
- Claude Code CLI

It must be fully isolated from Animus core behavior and must be toggleable:

- Router OFF → Animus processes requests exactly as it does today.
- Router ON → Animus sends eligible requests through the router.
- Router failure → fallback to current Animus processing path unless explicitly configured to hard-fail.

Do not break existing Animus behavior.

---

# 1. Non-negotiable design rules

## Isolation

The router must be developed as a separate module/package.

Do not deeply modify existing Animus chat, provider, or execution logic.

Add only a thin integration layer.

## Toggle behavior

Add one simple config flag:

```env
ANIMUS_MODEL_ROUTER_ENABLED=false
````

Optional:

```env
ANIMUS_MODEL_ROUTER_VISIBLE=true
ANIMUS_MODEL_ROUTER_FAIL_OPEN=true
```

Meaning:

* `ENABLED=false` → bypass router entirely.
* `VISIBLE=true` → expose route decision logs in UI/API.
* `FAIL_OPEN=true` → if router fails, use existing Animus path.

## Plugin style

Animus should call the router like this:

```python
if router_enabled:
    result = model_router.process(request)
else:
    result = existing_animus_process(request)
```

No existing provider path should be deleted.

---

# 2. Module layout

Create:

```txt
animus_model_router/
  __init__.py
  api.py
  cli.py
  config.py
  router.py
  schemas.py
  storage.py

  providers/
    __init__.py
    base.py
    cursor_cli.py
    codex_cli.py
    claude_code_cli.py

  inventory/
    __init__.py
    model_inventory.py
    model_normalizer.py
    capability_registry.py

  evals/
    __init__.py
    artificial_analysis.py
    scoring.py

  memory/
    __init__.py
    project_memory.py
    session_log.py
    summarizer.py

  logs/
    __init__.py
    audit_log.py
    route_events.py

  tests/
    test_router_toggle.py
    test_inventory.py
    test_classifier.py
    test_model_selection.py
    test_project_memory.py
    test_fallback.py
```

Animus integration should live separately:

```txt
animus/plugins/model_router_bridge.py
```

or equivalent existing plugin directory.

---

# 3. Request flow

## Current flow

```txt
User prompt
  ↓
Animus normal processing
  ↓
Selected provider/model
  ↓
Response
```

## New optional router flow

```txt
User prompt
  ↓
Animus router bridge
  ↓
Model Router Plugin
  ↓
Refresh/load model inventory
  ↓
Pick cheapest classifier model
  ↓
Classify prompt
  ↓
Select best exposed provider/model
  ↓
Attach project session summary
  ↓
Send prompt to selected CLI
  ↓
Return response + visible route metadata
  ↓
Animus displays response
```

---

# 4. Provider support

Each provider adapter must implement:

```python
class ProviderAdapter:
    name: str

    def is_available(self) -> bool:
        ...

    def list_models(self) -> list[ModelInfo]:
        ...

    def run_prompt(
        self,
        model: str,
        prompt: str,
        cwd: str | None = None,
        session_id: str | None = None,
        extra_args: dict | None = None,
    ) -> ProviderResult:
        ...
```

Adapters required:

```txt
CursorCLIProvider
CodexCLIProvider
ClaudeCodeCLIProvider
```

Rules:

* Provider CLIs are assumed already authenticated on PATH.
* Do not require API keys for provider CLIs.
* Do not hardcode model availability.
* If a provider cannot list models, log and continue.
* If a provider cannot run, fallback to next valid candidate.

---

# 5. Model inventory

The router must regularly discover exposed models from each CLI.

Store per project:

```txt
<project_root>/.animus_router/
  model_inventory.json
  model_capabilities.json
  route_audit.jsonl
  sessions/
    <session_id>/
      raw_log.jsonl
      summary.md
      unsummarized.jsonl
```

If no project is provided:

```txt
~/.animus/model_router/global/
```

Inventory schema:

```json
{
  "last_refreshed": "2026-05-07T00:00:00Z",
  "providers": {
    "cursor": [
      {
        "provider": "cursor",
        "model": "auto",
        "available": true
      }
    ],
    "codex": [],
    "claude": []
  }
}
```

Refresh rules:

* Refresh on startup.
* Refresh manually with CLI/API.
* Refresh if inventory is stale.
* Default stale threshold: 24 hours.

---

# 6. Artificial Analysis integration

Use Artificial Analysis as an optional external evaluation source.

API reference:

```txt
https://artificialanalysis.ai/api-reference
```

Add config:

```env
ARTIFICIAL_ANALYSIS_API_KEY=
ANIMUS_MODEL_ROUTER_USE_ARTIFICIAL_ANALYSIS=true
```

Rules:

* Use Artificial Analysis only to enrich model metadata.
* Never use it to determine what local CLIs expose.
* Local CLI inventory remains source of truth for availability.
* If API data is missing, stale, or unavailable, continue with local registry.
* Log missing enrichment.

Enrichment data should include where available:

```json
{
  "model": "model-name",
  "quality_score": 0,
  "coding_score": 0,
  "price_input": 0,
  "price_output": 0,
  "latency": 0,
  "output_speed": 0,
  "cost_efficiency": 0
}
```

---

# 7. Capability registry

Create:

```txt
<project_root>/.animus_router/model_capabilities.json
```

Example:

```json
{
  "codex:gpt-5.2-codex": {
    "provider": "codex",
    "model": "gpt-5.2-codex",
    "cost_rank": 5,
    "strength": "strong",
    "good_at": ["coding", "debugging", "refactor", "architecture"],
    "max_complexity": 10
  },
  "claude:sonnet": {
    "provider": "claude",
    "model": "sonnet",
    "cost_rank": 4,
    "strength": "balanced",
    "good_at": ["planning", "writing", "analysis", "architecture"],
    "max_complexity": 9
  },
  "cursor:auto": {
    "provider": "cursor",
    "model": "auto",
    "cost_rank": 3,
    "strength": "balanced",
    "good_at": ["general", "coding", "project_agent"],
    "max_complexity": 8
  }
}
```

This file can be updated over time.

---

# 8. Cheap classifier pass

The router must first choose the cheapest exposed model capable of classification.

Classifier prompt must return strict JSON only:

```json
{
  "complexity": 1,
  "task_type": "general",
  "is_coding": false,
  "is_research": false,
  "is_planning": false,
  "requires_project_context": true,
  "requires_file_changes": false,
  "recommended_strength": "cheap",
  "reason": "Simple direct question."
}
```

Valid task types:

```txt
general
coding
debugging
refactor
research
planning
writing
analysis
architecture
ops
```

Complexity scale:

```txt
1-3 = simple
4-6 = moderate
7-8 = hard
9-10 = expert / high-risk
```

If classifier returns bad JSON:

1. Retry once with stricter JSON-only instruction.
2. If still bad, fallback to deterministic default:

   * task_type: `general`
   * complexity: `5`
   * recommended_strength: `balanced`

---

# 9. Deterministic model selection

The classifier does not directly pick the final model.

Router selection rules:

1. Load currently exposed models.
2. Filter by task type.
3. Filter by `max_complexity >= classifier.complexity`.
4. Apply Artificial Analysis enrichment if available.
5. Apply local capability overrides.
6. Pick cheapest valid model meeting minimum quality.
7. If tied:

   * prefer Codex for coding/debugging/refactor
   * prefer Claude for writing/planning/analysis
   * prefer Cursor for general/project-agent tasks
8. If no match:

   * pick strongest exposed model
9. If selected provider fails:

   * fallback to next valid candidate
10. Log every decision.

---

# 10. Project memory

Each project must have isolated memory.

The router must accept:

```json
{
  "project_path": "/path/to/project",
  "session_id": "default",
  "prompt": "..."
}
```

Memory files:

```txt
<project_root>/.animus_router/sessions/default/
  raw_log.jsonl
  summary.md
  unsummarized.jsonl
```

Rules:

* Never send full raw chat history by default.
* Always send project session summary.
* Also send recent unsummarized turns.
* Raw logs are retained for audit/recovery only.

---

# 11. Rolling summary

Summary behavior:

```txt
summary.md + newest unsummarized turns
  ↓
summarizer model
  ↓
new summary.md
```

Default threshold:

```txt
1000 unsummarized tokens
```

When threshold is exceeded:

1. Load existing `summary.md`.
2. Load `unsummarized.jsonl`.
3. Summarize both together.
4. Replace `summary.md`.
5. Clear `unsummarized.jsonl`.
6. Keep `raw_log.jsonl`.

Summarizer model:

* Use cheapest summarization-capable model.
* If summarization fails, keep unsummarized log and continue.
* Never lose raw logs.

---

# 12. Final prompt format sent to selected model

```txt
You are processing a request routed by Animus Model Router.

PROJECT SESSION SUMMARY:
{summary}

RECENT UNSUMMARIZED CONTEXT:
{recent_turns}

CURRENT USER REQUEST:
{prompt}

Return the best answer or execute the requested CLI-compatible task according to the provider environment.
```

---

# 13. Visible route logging

Every routed request must write:

```json
{
  "timestamp": "2026-05-07T00:00:00Z",
  "project_path": "/path/to/project",
  "session_id": "default",
  "router_enabled": true,
  "input_preview": "Fix this failing test...",
  "inventory_age_seconds": 302,
  "classifier": {
    "provider": "cursor",
    "model": "cheap-model",
    "complexity": 6,
    "task_type": "debugging",
    "reason": "Code failure diagnosis."
  },
  "selected": {
    "provider": "codex",
    "model": "gpt-5.2-codex",
    "reason": "Lowest-cost exposed model matching debugging with complexity >= 6."
  },
  "fallbacks": [],
  "artificial_analysis": {
    "used": true,
    "matched": true
  },
  "result": {
    "status": "success",
    "latency_ms": 4120
  }
}
```

Animus should optionally display compact route info:

```txt
Routed via Codex CLI / gpt-5.2-codex
Task: debugging
Complexity: 6/10
Reason: lowest-cost valid debugging model
```

---

# 14. Local API

Create FastAPI server:

```bash
python -m animus_model_router.api
```

Endpoints:

## `POST /chat`

Request:

```json
{
  "project_path": "/path/to/project",
  "session_id": "default",
  "prompt": "Fix this bug.",
  "visible_route": true
}
```

Response:

```json
{
  "response": "...",
  "route": {
    "task_type": "debugging",
    "complexity": 6,
    "classifier_provider": "cursor",
    "classifier_model": "cheap-model",
    "selected_provider": "codex",
    "selected_model": "gpt-5.2-codex",
    "reason": "Lowest-cost valid debugging model."
  }
}
```

## `GET /models`

Returns current model inventory.

## `POST /models/refresh`

Refreshes provider model inventory.

## `GET /summary`

Query params:

```txt
project_path
session_id
```

Returns current project/session summary.

## `GET /logs`

Query params:

```txt
project_path
session_id
limit
```

Returns latest route audit entries.

---

# 15. Standalone CLI

Create CLI:

```bash
python -m animus_model_router.cli chat --project ~/Projects/my-app --session default "Fix this bug"
python -m animus_model_router.cli models refresh --project ~/Projects/my-app
python -m animus_model_router.cli models list --project ~/Projects/my-app
python -m animus_model_router.cli logs --project ~/Projects/my-app --session default
python -m animus_model_router.cli summary --project ~/Projects/my-app --session default
```

CLI must use same router core as API.

---

# 16. Animus integration bridge

Add thin bridge only.

Pseudo-code:

```python
from animus_model_router.router import ModelRouter
from animus_model_router.config import RouterConfig

def process_with_optional_router(request):
    config = RouterConfig.from_env()

    if not config.enabled:
        return existing_animus_process(request)

    try:
        router = ModelRouter(config)
        return router.process(
            project_path=request.project_path,
            session_id=request.session_id or "default",
            prompt=request.prompt,
        )
    except Exception as exc:
        log_router_failure(exc)

        if config.fail_open:
            return existing_animus_process(request)

        raise
```

Do not remove existing Animus model path.

---

# 17. Config

Add:

```env
ANIMUS_MODEL_ROUTER_ENABLED=false
ANIMUS_MODEL_ROUTER_VISIBLE=true
ANIMUS_MODEL_ROUTER_FAIL_OPEN=true
ANIMUS_MODEL_ROUTER_INVENTORY_TTL_HOURS=24
ANIMUS_MODEL_ROUTER_SUMMARY_THRESHOLD_TOKENS=1000
ANIMUS_MODEL_ROUTER_DEFAULT_SESSION=default
ANIMUS_MODEL_ROUTER_PROVIDER_ORDER=codex,claude,cursor

ARTIFICIAL_ANALYSIS_API_KEY=
ANIMUS_MODEL_ROUTER_USE_ARTIFICIAL_ANALYSIS=true
```

---

# 18. Failure behavior

## Router disabled

Use current Animus behavior.

## Router enabled but classifier fails

Retry once, then use safe default classification.

## Selected provider fails

Try next valid candidate.

## All routed providers fail

If `FAIL_OPEN=true`, use current Animus behavior.

If `FAIL_OPEN=false`, return clear router failure.

## Artificial Analysis fails

Continue without it.

## Summary update fails

Continue request, preserve logs.

---

# 19. Tests

Required tests:

```txt
test_router_toggle.py
- Router off uses existing path.
- Router on uses router path.
- Router failure falls back when fail-open enabled.

test_inventory.py
- Provider model discovery works with mocked CLIs.
- Failed provider does not break inventory.

test_classifier.py
- Valid JSON classification parsed.
- Bad JSON retries.
- Failed classifier falls back to default.

test_model_selection.py
- Cheapest valid model selected.
- Task-specific provider preference works.
- Strongest fallback works.

test_project_memory.py
- Each project has separate summary/logs.
- Summary rolls over after threshold.
- Raw logs are preserved.

test_fallback.py
- Selected provider failure falls back.
- All provider failure respects fail-open.
```

---

# 20. Validation commands

Run:

```bash
python -m pytest animus_model_router/tests
python -m animus_model_router.cli models refresh --project /tmp/router-test
python -m animus_model_router.cli chat --project /tmp/router-test --session default "Explain what this router does."
python -m animus_model_router.api
```

Then test API:

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "project_path": "/tmp/router-test",
    "session_id": "default",
    "prompt": "Explain what this router does.",
    "visible_route": true
  }'
```

---

# 21. Acceptance criteria

The task is complete only when:

* Router can run standalone as CLI.
* Router can run as local FastAPI server.
* Animus can toggle router on/off.
* Router OFF preserves current Animus behavior.
* Router ON sends requests through router.
* Router failure can fail open to existing Animus path.
* Cursor, Codex, and Claude Code provider adapters exist.
* Model inventory is discovered and stored.
* Artificial Analysis enrichment is optional and non-blocking.
* Cheapest classifier model classifies task complexity/type.
* Final model selection is deterministic and auditable.
* Project-specific memory works.
* Rolling summaries work.
* Raw logs are preserved.
* Route audit logs are visible.
* Tests pass.
* Existing Animus tests still pass.

---

# 22. Hard constraints

* Do not rewrite Animus core.
* Do not delete existing provider logic.
* Do not hardcode exposed models.
* Do not require provider API keys.
* Do not silently fallback.
* Do not send full raw chat history by default.
* Do not let classifier directly choose final model.
* Do not make Artificial Analysis mandatory.
* Do not allow router errors to break Animus when fail-open is enabled.

---

# 23. First implementation phase

Implement in this order:

1. Create isolated `animus_model_router/` package.
2. Add schemas/config/storage.
3. Add mocked provider adapters.
4. Add model inventory refresh.
5. Add capability registry.
6. Add classifier.
7. Add deterministic selector.
8. Add project memory and rolling summary.
9. Add audit logs.
10. Add CLI.
11. Add FastAPI server.
12. Add Animus bridge with toggle.
13. Add Artificial Analysis enrichment.
14. Add tests.
15. Validate router ON/OFF behavior.

```
```
