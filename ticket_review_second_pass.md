# Ticket Review — Second Pass (Codebase Audit)

This document is a second-pass audit focused on:
- `src/cluas_mcp` (especially memory + tool layer)
- `src/characters`
- `src/cluas_mcp/server.py`
- `src/cluas_mcp/formatters.py`

It validates the earlier ticket list and identifies additional *concrete* issues (including several immediate runtime bugs).

---

## 1) High-level outcome

### Overall
- The original ticket list correctly identified the broad “big rocks”: **memory robustness** + **prompt/token burn**.
- The deeper audit surfaced multiple **hard runtime bugs** that can cause tools to fail or the system to “fall over” (often with `AttributeError` / `TypeError`) and which should be treated as **P0**.

### Most important new finding
- There are several places where tool handlers return the *wrong type* (tuple/string/None) for what downstream code expects (dict-like), and several call-sites do not guard against this.

---

## 2) Confirmed tickets (from optimisation_ticket_list.md)

### Confirmed: P0-8 PaperMemory pruning bug
- **File:** `src/cluas_mcp/common/paper_memory.py`
- **Location:** `PaperMemory.prune_long_term()` around line ~92
- **Issue:** `cutoff = datetime.now(UTC).isoformat() - timedelta(...)` is invalid.
- **Impact:** pruning never works; any call will raise.

### Confirmed: P0-2/P0-3 Memory system fragility
- **Files:**
  - `src/cluas_mcp/common/paper_memory.py`
  - `src/cluas_mcp/common/observation_memory.py`
  - `src/cluas_mcp/common/trend_memory.py`
- **Issues (confirmed):**
  - Non-atomic writes (`open(...,"w")`) can corrupt JSON on crash.
  - `_read_memory()` does not handle `json.JSONDecodeError`.
  - No input validation on `add_*` methods.
- **Impact:** corrupted memory bricks the app; unbounded growth; malformed tool data can poison memory.

### Confirmed: P0-5 Prompt/tool-output injection risk (partial)
- The risk is real in the sense that tool output is inserted into the LLM context.
- Practical mitigation should emphasize:
  - strict size caps
  - “data framing” delimiters
  - avoiding transcript-like tool payloads

---

## 3) NEW P0 issues discovered (these should become tickets)

### NEW-P0-1: `verify_news` can return `None` + NewsAPI path is broken
- **File:** `src/cluas_mcp/news/news_search.py`
- **Issues:**
  - `verify_news()` has no final return path → implicit `None` if all fallbacks fail or keys absent.
    - Location: around lines ~8–57.
  - `verify_news_newsapi` is defined twice.
    - Location: first def around ~58, second def around ~106.
    - The second definition overwrites the first, and references `NewsApiClient` which is **not imported** → `NameError` when NewsAPI path runs.
- **Impact:** MCP tool `verify_news` can fail unpredictably; downstream formatters expect dict and will crash.

### NEW-P0-2: `fetch_air_quality` returns a tuple, not a dict
- **File:** `src/cluas_mcp/observation/airquality.py`
- **Location:** final return around lines ~93–98
- **Issue:** trailing comma after dict literal: `return {...},`
- **Impact:** callers expecting dict (`result.get(...)`) will crash.

### NEW-P0-3: `check_local_weather` return type mismatch + async/sync mismatch
- **File:** `src/cluas_mcp/common/check_local_weather.py`
- **Issues:**
  - `check_local_weather()` is annotated `-> dict` but returns `await check_weather(location)` (a **string**) when location is present.
    - Location: around line ~110–126.
  - Characters import `check_local_weather` (async) but execute tool functions via `run_in_executor` as if they were sync.
    - Example: Corvus/Raven/Crow tool handling uses `await loop.run_in_executor(None, lambda: tool_func(**args))`.
- **Impact:** tool calls can produce coroutine objects, strings, or dicts depending on path → downstream formatting breaks.

### NEW-P0-4: MCP server doesn’t guard formatter failures
- **File:** `src/cluas_mcp/server.py`
- **Location:** `call_tool()` around lines ~240–271
- **Issue:** exceptions are caught around handler execution, but `formatter_func(results)` is outside the try/except.
- **Impact:** one malformed result (or one formatter assumption) can crash the tool call and potentially destabilize the MCP server.

### NEW-P0-5: eBird mock fallback is broken when no API key
- **File:** `src/cluas_mcp/observation/ebird.py`
- **Issue:** `fetch_bird_sightings()` calls `_mock_sightings(location, max_results, species)` but `_mock_sightings` signature does not accept `species`.
  - call-sites around ~35–36 and ~80
  - `_mock_sightings` def around ~84
- **Impact:** If `EBIRD_API_KEY` is absent (common), bird tool can error instead of falling back.

---

## 4) MCP server + formatter layer (server.py / formatters.py)

### A) Schema duplication / drift risk
- **File:** `src/cluas_mcp/server.py`
- TOOL metadata is duplicated across:
  - `required_args` (custom)
  - `inputSchema.required` (JSON schema)
- `call_tool()` validates `required_args` but does **not** validate `inputSchema`.

**Risk:** schema drift (and confusing errors for clients).

**Recommendation:**
- Make `inputSchema.required` the canonical requirement source, and derive `required_args` from it (or delete `required_args`).
- Add a startup validation step: for each tool, ensure `required_args == inputSchema.required` if you keep both.

### B) Formatters assume dict-shaped payloads
- **File:** `src/cluas_mcp/formatters.py`
- Example: `format_local_weather()` uses `results.get(...)` unconditionally.

**Risk:** any tool handler returning string/None/tuple breaks formatters.

**Recommendation:**
- Make each formatter defensive:
  - if `not isinstance(results, dict)`: return a safe string
- Or enforce a strict `ToolResult` envelope everywhere.

---

## 5) Memory system (src/cluas_mcp/common/*memory*.py)

### A) Non-atomic writes + no corruption recovery
- Confirmed across Paper/Observation/Trend memories.

**Practical failure mode:**
- crash during write → truncated JSON → next startup fails in `_read_memory()`.

**Recommendation:**
- atomic write via temp file + rename
- handle `json.JSONDecodeError` and move corrupted file aside

### B) Hot-path writes in character execution
- Corvus writes to PaperMemory during `_format_search_for_llm()`.
  - **File:** `src/characters/corvus.py` around ~520–582

**Risk:** formatting should not usually mutate state; it makes failures harder to reason about.

**Recommendation:**
- separate “format tool output” from “persist memory entry” (explicit step)

---

## 6) Characters (src/characters) — reliability + maintainability issues

### A) Async tool functions executed as sync
- Corvus/Raven/Crow use `run_in_executor` with `tool_func(**args)`.
- This breaks if `tool_func` is async (returns coroutine).

**Concrete case:** `check_local_weather` is async but used as if sync.

**Recommendation:**
- Add a shared tool-execution helper:
  - if `iscoroutinefunction(tool_func)`: `await tool_func(**args)`
  - else: `await run_in_executor(...)`

### B) Tool result schema mismatches
- **Corvus:** saves arXiv “doi” using `paper.get("arxiv_id")` but ArxivClient uses `source_id`.
  - `src/characters/corvus.py` around ~566–572
- **Crow:** expects `count` from bird sightings but tool returns `total_sightings`.
  - Crow formatting/conditions use `result.get("count")`.
  - `src/cluas_mcp/observation/observation_entrypoint.py` returns `total_sightings`.

**Recommendation:**
- Define and enforce tool result schemas (typed dicts / dataclasses).

### C) Local weather tool is present in tool definitions but inconsistent
- Corvus/Raven/Crow tool defs expose `check_local_weather`.
- The actual handler’s type/return contract is inconsistent (see P0 above).

---

## 7) Token burn observations (additional)

### A) Token burn isn’t only system prompts
- Some tool outputs (esp. `format_temporal_patterns` and `format_trend_angles`) can be very long.
- If these are ever inserted into LLM context (characters’ tool calls), they should be capped by items/bytes.

### B) Better prompt efficiency lever: reduce per-character schema duplication
- Character tool schemas are repeated in each character file (`_get_tool_definitions`).
- MCP server also has schemas.

**Recommendation:**
- Generate tool schemas from a single canonical definition (or at least reuse between characters).

---

## 8) Concrete ticket updates (what I would change now)

### Elevate to P0 (new)
- **Fix `verify_news` correctness:** remove duplicate def; ensure final fallback returns dict; import missing dependencies.
- **Fix `fetch_air_quality` return type:** remove trailing comma.
- **Fix `check_local_weather` contract:** make it always return dict; align sync/async usage in characters + MCP.
- **Fix eBird mock fallback signature:** accept `species` or stop passing it.
- **Wrap formatter calls in MCP server try/except**.

### Adjust existing tickets
- **P0-4 (cooldown lock):** keep as “define concurrency model + evaluate lock choice” (P1/P2) rather than immediate `asyncio.Lock` conversion.

### Add new P1 tickets
- Tool schema contract enforcement across:
  - MCP server handlers/formatters
  - character tool execution
- Standardize “tool result” envelope: `{success, data, error, source}`.
- Centralize tool definitions to avoid drift.

---

## Status
- This second pass completed the requested deep audit and produced concrete, file-specific findings.
- Next step: incorporate these P0 findings back into the ticket list/plan (if you want), but per your request this document is only the review.
