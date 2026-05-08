```txt
DIRECTIVE: Add Animus Command Brief as an optional modular startup plugin

Goal:
Add a new optional startup feature called “Animus Command Brief.” When enabled, Animus opens to a project overview instead of auto-opening General. The sidebar shows the open project list. The normal chat area is temporarily filled by a Command Brief overlay showing project summaries. When the user clicks/selects a project, the overlay disappears and normal project chat opens. When disabled, Animus must behave exactly as it does today.

Hard requirements:
- Implement as a removable plugin/module.
- Suggested path: animus/plugins/command_brief/
- Must be toggled from settings.
- If disabled, Animus must preserve current behavior exactly:
  - default opens General
  - no Command Brief UI
  - no startup scan
  - no timestamp check
  - no model calls
  - no routing changes
  - no cache reads required
  - no project summary logic executed

Settings:
- commandBrief.enabled: boolean
- commandBrief.autoRefreshRecent: boolean default true
- commandBrief.recentWindowDays: number default 3

Startup behavior:
IF commandBrief.enabled == false:
    run existing startup flow unchanged
    default to General exactly as before
    return

IF commandBrief.enabled == true:
    do not auto-select General
    show project list in sidebar
    show Command Brief overlay in the main chat-space view
    load cached summaries immediately
    scan only approved project governance docs for modified timestamps
    classify projects as active, stale, inactive, blocked, or unknown
    regenerate only recent + stale summaries
    never regenerate all summaries on startup

Overlay behavior:
- Command Brief is not part of the chat thread.
- It must render as a temporary overlay/panel filling the normal chat area.
- Briefings must be divided by project using separate cards/sections.
- Once the user clicks/selects a project, dismiss the overlay and open normal project chat.
- Normal chat behavior must resume unchanged after project selection.
- Provide a way to manually reopen Command Brief if enabled.

Approved source files only:
- project_status.md
- project_goal.md
- project_history.md
- project_knowledge.md
- repo_map.md
- .project_intel/state.json
- .project_intel/active_context.json

File-reading rules:
- Do not scan entire repos.
- Do not read arbitrary folders.
- Read only approved governance files.
- For project_history.md, read only the last 80-150 lines.
- Missing files are allowed; mark missing data as unknown.

Regeneration logic:
A project summary may auto-regenerate only when all are true:
- commandBrief.enabled == true
- commandBrief.autoRefreshRecent == true
- project was modified within recentWindowDays, default 3 days
- approved docs changed after cached summary was generated

Pseudo:
shouldRegenerate =
    enabled
    && autoRefreshRecent
    && modifiedWithinRecentWindow
    && docsChangedSinceLastSummary

Do not auto-regenerate:
- inactive projects
- unchanged projects
- old projects outside recentWindowDays
- all projects globally on startup

Manual controls:
- Refresh this project
- Refresh all projects
- Open project
- View Summary Log
- Disable Command Brief

Cache requirements:
Store per-project summary cache for fast startup:
type ProjectSummary = {
  projectId: string;
  name: string;
  status: "active" | "stale" | "inactive" | "blocked" | "unknown";
  lastActivityAt: string | null;
  generatedAt: string | null;
  modelUsed: string | null;
  currentFocus: string;
  recentChanges: string[];
  nextActions: string[];
  risks: string[];
  sourceFiles: string[];
  sourceFileModifiedTimes: Record<string, string>;
};

Command Brief UI:
Header:
- Animus Command Brief
- Last updated
- Model used
- Refresh controls

Each project card/section:
- Project name
- Status
- Last activity
- Current focus
- Recent changes
- Next actions
- Risks/blockers
- Source files
- Generated timestamp
- Model used
- Buttons: Open Project, Refresh Summary, View Summary Log

Summarizer requirements:
- Use the currently selected Animus inference/model path.
- Return strict JSON only.
- Do not invent missing information.
- If unclear, use "unknown."
- Every summary must include sourceFiles.
- Keep bullets short.

Prompt:
You are generating a compact Animus project status summary.
Use only the provided project governance docs.
Do not invent missing information.
If status is unclear, mark it unknown.
Return valid JSON only.
Keep bullets under 18 words.

Required fields:
- status
- currentFocus
- recentChanges
- nextActions
- risks
- sourceFiles

Durable daily summary log:
Each generated project summary must append to this file inside that project repo:

project_daily_summaries.md

Rules:
- Create project_daily_summaries.md automatically if missing.
- Append each new generated summary to the bottom.
- Never overwrite prior summaries.
- Cache is for fast UI startup only.
- project_daily_summaries.md is the durable project record.
- Opening the log must not trigger model generation.

Append format:
## YYYY-MM-DD HH:mm - Animus Command Brief

Model: <model/provider>
Status: <active/stale/inactive/blocked/unknown>

Sources:
- <source file>
- <source file>

### Current Focus
<summary>

### Recent Changes
- item
- item

### Next Actions
- item
- item

### Risks / Blockers
- item
- item

---

Workspace UI update:
In each project workspace, add a new button:

Summaries

Placement:
Goal | Summaries | Refresh

Summaries button behavior:
- Opens project_daily_summaries.md for the selected project.
- If missing, create it with:

# Project Daily Summaries

This file is automatically appended by Animus Command Brief.

- Display the file contents.
- Do not generate a new summary just by opening Summaries.

Architecture rules:
- Command Brief must not become a dependency of chat, routing, memory, project loading, inference, or project workspaces.
- Disabled mode must bypass the plugin completely.
- Plugin errors must not break Animus startup.
- If plugin fails while enabled, show the error only inside the Command Brief overlay and allow normal project selection.
- Existing General-first behavior must remain available and unchanged when disabled.
- Feature must be removable later without breaking core Animus.

Acceptance criteria:
1. With commandBrief.enabled=false, Animus behaves exactly like current production behavior.
2. With commandBrief.enabled=true, Animus opens to project list + Command Brief overlay.
3. Command Brief overlay fills the chat-space view but is not chat.
4. Selecting/clicking any project dismisses the overlay and opens normal project chat.
5. Cached summaries render immediately before any model call.
6. Only recent + stale projects auto-regenerate.
7. Inactive old projects do not regenerate automatically.
8. Manual refresh one project works.
9. Manual refresh all works.
10. No full repo scan occurs.
11. Only approved governance docs are read.
12. Strict JSON model output is parsed safely.
13. Each generated summary appends to project_daily_summaries.md.
14. Summaries button appears between Goal and Refresh.
15. Summaries button opens the log without triggering generation.
16. Plugin errors do not break startup or project selection.

Validation:
- Unit test shouldRegenerate logic.
- Test disabled mode preserves legacy startup.
- Test enabled mode shows overlay instead of General.
- Test project selection dismisses overlay.
- Test recent/stale/inactive classification.
- Test inactive projects do not trigger summarization.
- Test cached summaries load before regeneration.
- Test only approved files are read.
- Test summary append creates project_daily_summaries.md if missing.
- Test summary append preserves existing log content.
- UI smoke test for enabled and disabled states.

Deliverable:
A fully modular Command Brief plugin that gives Animus a startup project command-center overlay when enabled, writes durable per-project summary logs, and preserves the existing General-first startup path perfectly when disabled.
```
