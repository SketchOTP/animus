# Beta Skill/Tool Context Protocol

## Purpose
Reduce repeated tool/skill context injection and optionally route prompts to the best enabled provider/model while preserving current behavior when beta is off.

## Decision engine
- Selector/router now run through a real provider-backed cheap model call (OpenAI-compatible chat completion) when an enabled candidate model is available.
- Decision model choice:
  - `specific_model`: uses configured `router_provider` + `router_model` when enabled.
  - `cheapest_enabled`: picks the lowest-cost enabled candidate using provider pricing data when available, with heuristic tie-breakers.
- The decision request includes compact registry snapshot + user prompt and requires strict JSON output.
- On model call failure or invalid JSON, beta falls back to heuristic decisioning, then to normal path if guards still fail.

## Selector calibration constraints (shadow-first)
- Selector prompt explicitly requires direct-need-only selection, prefers empty selection over weak relevance, and disallows `browser_*` for normal code/test/refactor/docs/repo/local-edit tasks.
- Selector JSON contract supports relevance-bearing tool objects:
  - `selected_tools: [{ "id": "...", "relevance": 0.0-1.0, "reason": "..." }]`
- Deterministic post-pruning runs after model output:
  - drop all `browser_*` tools if prompt lacks strong browser/UI intent terms.
  - drop tools with `relevance < 0.55`.
  - apply anti-slot-filling cap (prefer ~1-3 tools by default).
- Deterministic baseline selector now runs first and is authoritative:
  - baseline rules derive `required` tools from prompt intent before any LLM scoring.
  - LLM selection is merged with baseline tools; required baseline tools are non-prunable unless unavailable.
  - relevance pruning applies to optional LLM-added tools only.
  - medium/high complexity requests still enforce a minimum viable non-empty toolset when possible.
- Empty selection is valid and preferred over weak/noisy selection.
- Shadow benchmark tracks `precision`, `recall`, `F1`, browser false-positive rate, average selected tools, and `empty_selection_rate`.

## Active mode safety gate (limited beta)
- Active mode is allowed only when all are true:
  - requested mode is `active`
  - `shadow_benchmark_passed = true`
  - `fallback_to_manual = true`
  - `decision_diagnostics_enabled = true`
  - if `active_local_dev_only = true`, environment must be local/dev
- If gate conditions fail, runtime forces effective mode to `shadow` (no request mutation).
- Active mode gate remains metric-based and should not be enabled unless shadow benchmark meets:
  - recall `>= 0.70`
  - precision `>= 0.50`
  - browser false positives near zero on code-only prompts
  - average selected tools `<= 4` unless justified

## Existing inference entrypoint
- File: `animus-chat/server.py`
- Function/class: `chat()`
- Current behavior: receives `POST /api/chat`, injects ANIMUS skill/tool hints, forwards to Hermes gateway `POST /v1/chat/completions`, and streams the unchanged upstream response back to the UI.

## Existing model selection
- File: `animus-chat/app/index.html`
- Function/class: `send()`, `effectiveChatModelId()`, `chatBackendPayload()`
- Current behavior: UI selects a manual backend/provider+model from Settings, then sends `model` + `hermes_provider` (and optional `hermes_base_url`) in each chat request.

## Existing tool/skill context assembly
- File: `hermes-agent/gateway/platforms/api_server.py`
- Function/class: `_handle_chat_completions()`, `_create_agent()`
- Current behavior: request-level `hermes_disabled_tools` is parsed and passed to `AIAgent(disabled_tools=...)`; API server enables platform toolsets and forces `skills` toolset.
- File: `hermes-agent/run_agent.py`
- Function/class: `AIAgent.__init__()`, `_build_system_message()`
- Current behavior: tool schemas are built via `get_tool_definitions(...)`; skills system prompt is built via `build_skills_system_prompt(...)` when skill tools are present.

## Planned beta hook point
- File: `hermes-agent/gateway/platforms/api_server.py`
- Function/class: `_handle_chat_completions()`
- Why this is safe:
  - The hook runs before agent creation and can fail closed to existing behavior.
  - `off` mode bypasses all beta decisions.
  - `shadow` mode runs selector/router + logging but does not mutate provider/model/context.
  - `active` mode only mutates request-scoped tool/skill/model selection; no global config mutation.

## Modes
- `off`
- `shadow`
- `active`

## Recommended rollout
1. Off (default)
2. Shadow for telemetry and confidence tuning
3. Active for trusted workflows

## Failure behavior
All selector/router failures fall back to current inference behavior.

## Safety rules
- Disabled tools are never injected.
- Disabled/unavailable models are never selected by router validation.
- Full prompts are not logged unless explicitly enabled.
- Manual model selection is preserved unless Auto Router is enabled and validated.

## Known limitations
- Some providers may reject strict JSON response format hints; adapter retries once without `response_format` and still enforces JSON parsing.
- Token savings are estimated via lightweight character-based approximation.
- Router introduces one additional decision stage before final inference in active mode.

