# CLUAS HUGINN: Updated Optimization & Improvement Tickets (01)

**Update Date:** December 13, 2025  
**Based on:** `optimisation_ticket_list.md`, `ticket_review_first_pass.md`, `ticket_review_second_pass.md`  
**Scope:** Robustness + correctness + token efficiency + maintainability

---

## Highest impact for the smallest diff (quick wins)

These are high-leverage changes that are likely **single-digit line diffs** but prevent real crashes / undefined behaviour.

- **[Fix PaperMemory pruning TypeError]**
  - **Location:** `src/cluas_mcp/common/paper_memory.py` (`prune_long_term`)  
  - **Issue:** `datetime.now(UTC).isoformat() - timedelta(...)`  
  - **Impact:** prevents pruning from ever working; any call can raise  
  - **Diff size:** ~1 line  

- **[Fix air quality tool returning a tuple]**
  - **Location:** `src/cluas_mcp/observation/airquality.py` (`fetch_air_quality`)  
  - **Issue:** trailing comma in final `return` makes it `({...},)`  
  - **Impact:** prevents downstream `.get(...)` calls; can crash tool handling  
  - **Diff size:** ~1 character / 1 line  

- **[Fix `verify_news` implicit `None` return + NewsAPI definition collision]**
  - **Location:** `src/cluas_mcp/news/news_search.py`  
  - **Issues:**
    - `verify_news()` can fall off end → returns `None`
    - `verify_news_newsapi` defined twice; second overwrites first; second uses `NewsApiClient` without import
  - **Impact:** news tool can fail unpredictably; formatters assume dict and may crash  
  - **Diff size:** small (a few lines), but high value

- **[Fix `academic_search` tool argument mismatch (`query` vs `term`) + arXiv call]**
  - **Locations:**
    - `src/cluas_mcp/academic/academic_search_entrypoint.py`
    - Tool schemas in `src/cluas_mcp/server.py` and `src/characters/*`  
  - **Issues:**
    - schemas call parameter `query`, function signature is `academic_search(term: str)` → `TypeError`
    - `ArxivClient.search(...)` expects a list, but is called with a string
  - **Impact:** academic tool calls can fail outright or behave incorrectly  
  - **Diff size:** small (rename param or add wrapper; pass `[query]`)

- **[Make `check_local_weather` consistently return a dict + fix async/sync dispatch]**
  - **Location:** `src/cluas_mcp/common/check_local_weather.py` + character tool execution  
  - **Issue:** function annotated `-> dict` but returns string for normal path; async used like sync in characters  
  - **Impact:** tool results may be `str`/`coroutine` instead of dict → formatter/tool crashes  
  - **Diff size:** moderate-small (wrap string in dict; ensure characters call sync wrapper or await async)

- **[Catch formatter exceptions in MCP server]**
  - **Location:** `src/cluas_mcp/server.py` (`call_tool`)  
  - **Issue:** `formatter_func(results)` not protected by try/except  
  - **Impact:** one bad tool result can take down tool call (and potentially the server)  
  - **Diff size:** a few lines

- **[Fix eBird mock fallback signature mismatch]**
  - **Location:** `src/cluas_mcp/observation/ebird.py`  
  - **Issue:** `_mock_sightings` doesn’t accept `species` but is called with it  
  - **Impact:** when `EBIRD_API_KEY` is missing (common), bird tool fallback can error  
  - **Diff size:** small (add param or stop passing it)

---

## What changed vs the original ticket list

- **[Added P0 correctness tickets]**
  - `academic_search` schema/signature mismatch + arXiv invocation bug
  - `verify_news` can return `None` + duplicate definition / missing import
  - `fetch_air_quality` returns a tuple
  - `check_local_weather` returns wrong type + async/sync mismatch
  - MCP `call_tool` doesn’t guard formatter exceptions
  - eBird mock fallback signature mismatch

- **[Reprioritized]**
  - Original **P0-4 (provider cooldown lock)** is now **P1/P2** (“define concurrency model + correct lock choice”), not an automatic `asyncio.Lock` swap.
  - Original **P0-6 (no timeout)** is now **P1/P2** because most `requests.get` calls already include timeouts; remaining risk is in non-`requests` network calls (e.g., `feedparser.parse`, `pytrends`).

- **[Added P1 operational ticket]**
  - Dependency source-of-truth mismatch (`pyproject.toml` + `uv.lock` vs `requirements.txt`).

---

## 🔴 CRITICAL PRIORITY (P0) — Correctness, Security, Data Integrity

### P0-1: Tool schema/handler signature mismatches (hard runtime failures)
**Locations:**
- `src/cluas_mcp/server.py` (tool schemas)
- `src/characters/*` (`_get_tool_definitions`)  
- `src/cluas_mcp/academic/academic_search_entrypoint.py`

**Issue:** tool schemas declare `query`, but handler is `academic_search(term: str)`.

**Impact:** `TypeError` at runtime; academic tool calls fail.

**Fix direction:**
- Make function signature accept `query`, or add a wrapper `academic_search(query: str)`.
- Ensure the same parameter name is used consistently across MCP + characters.

**Fix effort:** 30–60 minutes

---

### P0-2: `academic_search` calls arXiv with wrong argument type
**Location:** `src/cluas_mcp/academic/academic_search_entrypoint.py`

**Issue:** `ArxivClient.search(...)` expects a list of keywords but is called with a string.

**Impact:** incorrect query construction; degraded relevance / unexpected behaviour.

**Fix direction:** call `ArxivClient.search([query])`.

**Fix effort:** 5–10 minutes

---

### P0-3: `verify_news` can return `None` + NewsAPI implementation collision
**Location:** `src/cluas_mcp/news/news_search.py`

**Issues:**
- `verify_news()` has no final return path.
- `verify_news_newsapi` is defined twice; later definition overwrites earlier and references `NewsApiClient` without import.

**Impact:** news tool unpredictably fails; downstream code assumes dict.

**Fix direction:**
- Ensure exactly one `verify_news_newsapi` implementation.
- Ensure `verify_news()` always returns a dict (even if empty / mock).

**Fix effort:** 30–90 minutes

---

### P0-4: Air quality tool returns tuple due to trailing comma
**Location:** `src/cluas_mcp/observation/airquality.py`

**Issue:** trailing comma on return statement.

**Impact:** callers break on `.get(...)`.

**Fix effort:** 1 minute

---

### P0-5: `check_local_weather` return contract is inconsistent + async/sync mismatch
**Locations:**
- `src/cluas_mcp/common/check_local_weather.py`
- `src/characters/corvus.py`, `crow.py`, `raven.py`, `magpie.py` (tool dispatch)

**Issues:**
- `check_local_weather()` annotated as dict but returns a string on the normal path.
- Characters execute tools with `run_in_executor` assuming sync; async tool functions return coroutines.

**Impact:** tool results become `str`/`coroutine`/`dict` depending on path → formatter failures.

**Fix direction:**
- Make `check_local_weather` always return dict.
- Add a shared tool execution helper:
  - if tool is async: `await tool(**args)`
  - else: `await run_in_executor(...)`
- Or have characters use the provided sync wrapper (`check_local_weather_sync`).

**Fix effort:** 1–3 hours

---

### P0-6: MCP server doesn’t guard formatter failures
**Location:** `src/cluas_mcp/server.py` (`call_tool`)

**Issue:** exceptions are caught around handler execution, but not around `formatter_func(results)`.

**Impact:** malformed tool result can crash tool call / destabilize server.

**Fix direction:** wrap formatting in try/except and return a safe error `TextContent`.

**Fix effort:** 10–20 minutes

---

### P0-7: eBird mock fallback signature mismatch
**Location:** `src/cluas_mcp/observation/ebird.py`

**Issue:** `_mock_sightings` doesn’t accept `species` but callers pass it.

**Impact:** if `EBIRD_API_KEY` missing (common), fallback path errors.

**Fix effort:** 10–20 minutes

---

### P0-8: Memory system has no corruption protection or recovery
**Locations:**
- `src/cluas_mcp/common/paper_memory.py`
- `src/cluas_mcp/common/observation_memory.py`
- `src/cluas_mcp/common/trend_memory.py`

**Issues:**
- Non-atomic writes
- No `json.JSONDecodeError` handling on read

**Impact:** a partial write/corrupt JSON can brick the app.

**Fix direction:**
- Atomic write via temp file + rename
- If decode fails, move file aside (`*.corrupt-<timestamp>.json`) and start fresh

**Fix effort:** 4–6 hours

---

### P0-9: No input validation on memory operations
**Location:** all memory classes

**Issue:** `add_*` methods accept unbounded/unvalidated inputs.

**Impact:** malformed entries, DoS risk via huge strings.

**Fix effort:** 3–4 hours

---

### P0-10: Datetime arithmetic bug in `PaperMemory.prune_long_term`
**Location:** `src/cluas_mcp/common/paper_memory.py`

**Issue:** subtracting timedelta from an ISO string.

**Impact:** pruning broken.

**Fix effort:** 5 minutes

---

## 🟠 HIGH PRIORITY (P1) — Performance, Token Efficiency, Operational Resilience

### P1-1: Massive prompt duplication across characters
**Location:** `src/prompts/character_prompts.py`

**Issue:** global norms repeated in every character prompt on every call.

**Impact:** large, recurring token burn.

---

### P1-2: Redundant tool heuristics in every prompt
**Location:** `src/prompts/character_prompts.py`

**Issue:** repeated verbose tool-instructions.

**Impact:** avoidable prompt bloat.

---

### P1-3: Token-aware history truncation
**Location:** `src/gradio/app.py`

**Issue:** fixed `history[-5:]` rather than token-budget truncation.

**Impact:** context wasted or unpredictably truncated.

---

### P1-4: Duplicate `_call_llm` implementation across characters
**Location:** `src/characters/*`

**Issue:** ~200 lines duplicated in multiple classes.

**Impact:** bugs replicated; hard to update.

---

### P1-5: Memory queries are O(n) linear scans
**Location:** all memory classes

**Issue:** searches iterate full memory.

**Impact:** slow at scale.

---

### P1-6: No caching of system prompts
**Location:** all characters

**Issue:** system prompt regenerated every call.

**Impact:** extra CPU + memory I/O.

---

### P1-7: Threadpool pressure / throughput limits from sync tool calls
**Location:** character `_respond_cloud()` implementations

**Issue:** tools are run via `run_in_executor`; doesn’t block the event loop, but can saturate threadpool.

**Impact:** multi-user latency spikes.

---

### P1-8: No request deduplication for identical queries
**Location:** tool entrypoints

**Issue:** duplicate parallel API calls.

**Impact:** wasted quota + slower runs.

---

### P1-9: Tool schema duplication/drift (MCP vs characters)
**Locations:**
- `src/cluas_mcp/server.py` (canonical-ish tool schemas)
- `src/characters/*` (duplicated tool schemas)

**Issue:** schemas can diverge (already happened with `academic_search`).

**Impact:** runtime failures + confusing LLM behaviour.

**Fix direction:** derive character tool schemas from a single canonical definition.

---

### P1-10: Dependency single source of truth (pyproject vs requirements)
**Locations:**
- `pyproject.toml` + `uv.lock`
- `requirements.txt`

**Issue:** version mismatch exists (e.g., `openai>=2.8.1` vs `openai>=1.45.0`).

**Impact:** nondeterministic installs; hard-to-reproduce behaviour.

**Fix direction:** pick one authoritative source (likely `pyproject.toml` given `uv.lock`).

---

### P1-11: Memory files grow unbounded (pruning not invoked)
**Location:** all memory classes

**Issue:** pruning exists but is not automatically used.

**Impact:** eventual performance/disk issues.

---

### P1-12: Ensure timeouts for remaining non-`requests` network calls
**Locations:**
- `src/cluas_mcp/academic/arxiv.py` (`feedparser.parse`)
- `src/cluas_mcp/web/trending.py` (pytrends)

**Issue:** these libraries may not enforce explicit timeouts.

**Impact:** rare but painful hangs.

---

## 🟡 MEDIUM PRIORITY (P2) — Code Quality & Consistency

### P2-1: Inconsistent error handling patterns
**Location:** throughout

---

### P2-2: No runtime type validation
**Location:** public APIs / tools

---

### P2-3: Magic numbers/strings
**Location:** throughout

---

### P2-4: Inconsistent naming conventions
**Location:** various

---

### P2-5: Central logging configuration
**Location:** root-level logging setup

---

### P2-6: Empty `src/orchestrator.py`

---

### P2-7: Tool result schema mismatches in characters
**Examples:**
- Corvus stores arXiv “doi” using `paper.get("arxiv_id")` but arXiv uses `source_id`.
- Crow expects `count` but bird tool returns `total_sightings`.

---

### P2-8: Commented-out Semantic Scholar code
**Location:** `src/cluas_mcp/academic/academic_search_entrypoint.py`

---

### P2-9: No health check endpoints

---

## 🟢 LOW PRIORITY (P3) — Polish & Future-Proofing

### P3-1: Metrics/telemetry

### P3-2: Configuration file

### P3-3: Graceful shutdown

### P3-4: Rate limit metrics

### P3-5: Automated dependency updates

---

## Recommended implementation order (updated)

### Phase 1: Crash-prevention / correctness (P0 quick wins)
1. P0-10 PaperMemory prune TypeError
2. P0-4 airquality tuple return
3. P0-3 verify_news return-path + NewsAPI collision
4. P0-1/P0-2 academic_search schema + arXiv invocation
5. P0-6 MCP formatter try/except
6. P0-7 eBird mock signature
7. P0-5 check_local_weather contract + async/sync dispatch

### Phase 2: Memory resilience
1. P0-8 atomic writes + JSON corruption recovery
2. P0-9 input validation
3. P1-11 pruning invocation policy

### Phase 3: Token & maintainability
1. P1-1 prompt compression
2. P1-2 tool heuristic compression
3. P1-4 `_call_llm` dedupe
4. P1-3 history truncation by tokens

### Phase 4: Perf + ops
1. P1-5 memory indexing
2. P1-6 prompt caching
3. P1-8 request deduplication
4. P1-10 dependency single source of truth
