# Cluas — Cursor Project Guide
Mode: Surgical (1)

Cursor should follow all rules below unless explicitly overridden.

---

# 1. Operational Mode

## Surgical Mode Rules
- Do not refactor unless explicitly instructed.
- Do not modify multiple files unless I list them.
- Never modify architecture, directories, or file names without approval.
- Suggest changes through tickets or plans before acting.
- Show diffs before application.
- When uncertain, ask before reading or writing.

## Scope Minimization
- Default to reading only the file(s) mentioned in the prompt.
- If the task affects a directory, request confirmation before a bulk read.
- Use subfolder-level cursor.md files to override local behavior.

---

# 2. Project Overview

Cluas is a multi-agent research assistant with:
- Four character agents with distinct personas (`src/characters`)
- An MCP-based tool layer (`src/cluas_mcp`)
- A shared utility layer (`src/utils`)
- A Gradio-based UI (`src/gradio`)
- An orchestration layer (`src/orchestrator.py`)
- Local JSON-based memory and cache (`src/data`)

---

# 3. Repository Structure

src/
characters/ # persona logic
cluas_mcp/ # MCP servers & entrypoints
academic/
common/
domain/
news/
observation/
web/
data/ # stored memory & cache (never modify)
gradio/ # UI
utils/ # shared utilities
orchestrator.py # high-level orchestrator


---

# 4. Safe Editing Areas

Cursor may edit:
- `src/characters/*`
- `src/cluas_mcp/*` except where noted as fragile
- `src/gradio/app.py`
- `src/utils/*`
- Implementation-level code supporting tools
- Small, isolated improvements

---

# 5. Restricted / Fragile Areas

- `src/orchestrator.py` — changes require explicit approval
- `src/data/*` — never modify programmatically or structurally
- Any file not listed as safe
- Any control-plane glue code unless specifically permitted
- Any config or naming conventions

---

# 6. Architectural Notes

## Characters Layer
- Each file defines a persona with specific expertise.
- Output formatting conventions must remain stable.
- Do not merge personas; do not modify persona names or roles.

## MCP Layer
Contains specialized tool entrypoints:
- `academic/`: arXiv, PubMed, Semantic Scholar fetchers
- `news/`: news API search
- `observation/`: bird/weather observational tools
- `web/`: trending and general web search
- `common/`: shared HTTP, memory, cache logic

Rules:
- Do not alter API endpoint URLs without instruction.
- Network logic should be consistent across tools.
- Retry, caching, and rate-limiting must remain stable.

## Utilities
- `model_list_groq.py` and others should remain small and self-contained.
- Avoid large rewrites; maintain consistency.

## Gradio UI
- Keep user-facing function names and event wiring intact.

## Orchestrator
- Treat as a fragile, single-source-of-truth.
- Do not rewrite flow control, dispatch, or agent coordination without approval.

---

# 7. Code Conventions

## General
- Follow existing stylistic patterns.
- Prefer explicitness over magic.
- Use docstrings consistent with current style.

## Import rules
- Maintain import locality.
- Avoid introducing top-level cross-layer dependencies.

## Error handling
- Follow existing try/except patterns.
- Do not remove error metadata or context.

---

# 8. Ticket Workflow (Required Before Major Changes)

When asked for anything non-trivial:

1. Produce a numbered list of proposed tickets.
2. Each ticket contains:
   - Goal
   - Impacted files
   - Expected risk
   - Estimated complexity
3. Wait for explicit approval before generating code.

Example ticket structure:

[Ticket 1] Improve arXiv query building
Files: src/cluas_mcp/academic/arxiv.py
Risk: Low
Complexity: Low
Notes: Only adjust parsing logic.


---

# 9. Diff Workflow

For all modifications:
- Always show a diff preview.
- Only write code after explicit approval.
- Keep diffs minimal, targeted, and reversible.
- Do not auto-format unrelated areas.

---

# 10. Performance & Credit Preservation

- Do not scan the whole repo without being asked.
- Limit reads to single files or small folders.
- Ask before reading directories > 10 files.
- Prefer incremental review over full-context analysis.
- Avoid speculative work.

---

# 11. Subfolder `cursor.md` Rules

If a directory contains its own `cursor.md`:
- That file overrides root rules *for that directory only*.
- Root-level rules apply everywhere else.
- Local rules must remain compatible with Surgical Mode.

---

# 12. MCP Tool Guidelines

When editing MCP server/entrypoint modules:
- Maintain signatures required by the MCP spec.
- Preserve tool names, IDs, argument shapes.
- Keep responses deterministic unless instructed otherwise.
- Do not alter output contract formats.
- Keep HTTP client logic consistent across tools.

---

# 13. Persona/Character Guidelines

- Personas have fixed tone, knowledge windows, and behavioral constraints.
- Do not alter identity, speech patterns, or output styles.
- Internal logic may be improved but not reimagined.

---

# 14. Orchestrator Guidelines (High-Risk Zone)

Before editing `orchestrator.py`, always:
1. Generate a plan.
2. Produce tickets.
3. Wait for explicit approval.

Disallowed without authorization:
- Rewiring tool routing
- Changing conversation state logic
- Modifying persona dispatch
- Changing execution order or concurrency rules

---

# 15. Testing / Validation Rules

- Follow current usage patterns; do not introduce new frameworks.
- Keep tests inline or minimal.
- Ensure MCP tools remain usable without breaking contract.

---

# 16. Prompt Templates (For Cursor Tasks)

## General Improvement
“Review only this file: <file>. Identify small improvements. No refactors.”

## Write a patch
“Prepare a diff for tickets 1 and 2 only.”

## Ask for a plan
“Before editing, give me a plan and a ticket list.”

## Isolated folder work
“Limit analysis to src/cluas_mcp/news.”

---

# 17. Maintenance Guidelines

- Keep modifications atomic.
- Maintain existing naming conventions.
- Avoid unnecessary abstraction.
- Keep folder boundaries clean.
- Preserve backward compatibility.

---

# 18. Quick Summary for Cursor

- Surgical Mode only.
- Minimal diffs.
- Ask before reading large scopes.
- Never refactor without permission.
- Use tickets + plans before substantial work.
- Preserve architecture, personas, orchestrator flow.
- Subfolder cursor.md files override root rules.


