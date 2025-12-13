# Ticket Review — First Pass

This document reviews:
- `optimisation_ticket_list.md`
- `.planning/plans/001-PLAN.md`

Scope of this pass:
- Check ticket accuracy/priority (based on what’s already been inspected)
- Identify missing tickets / mis-prioritizations
- Check whether the plan is internally consistent and realistically executable

---

## 1) Overall assessment

### What’s good
- The ticket list is largely on-target: memory integrity + prompt/token burn are the two highest-ROI areas.
- The plan structure (phases with checkpoints) is appropriate for a codebase where regressions are easy and hard to detect.
- The ticket list already captures at least one *real* bug (`PaperMemory.prune_long_term` datetime arithmetic).

### What’s weak / needs refinement
- Some tickets mix **code-quality concerns** with **runtime-safety/security** and assign them P0 when they’re closer to P1/P2.
- A few recommendations are technically correct but **non-trivial** given the current sync/async boundary (e.g. switching locks to `asyncio.Lock`).
- Several important, concrete operational risks were *not* ticketed (dependency/lockfile mismatch, tool function return inconsistency / missing returns, MCP schema mismatches).

---

## 2) Ticket list review (corrections / adjustments)

### P0-4 (cooldown lock: threading vs asyncio)
- **Ticket is directionally correct**: shared mutable state needs disciplined concurrency.
- **However, the proposed fix (replace `threading.Lock` with `asyncio.Lock`) is not drop-in**, because the lock is used inside *sync* helper methods (`_provider_in_cooldown`, `_note_provider_*`).
  - Making them `async` cascades changes through all `_call_llm` paths.
  - Using `asyncio.Lock` inside sync functions is not viable.

**Refined recommendation:**
- Keep `threading.Lock` if you intend these helpers to stay sync.
- Add a ticket to clarify the concurrency model:
  - **If single-process, single-thread event loop:** `threading.Lock` is acceptable (very short critical sections) though it can block the loop briefly.
  - **If multi-threaded workers:** `threading.Lock` is appropriate.
  - **If multi-process:** locks don’t help; use file locks or per-process state.

**Priority suggestion:** drop from P0 to **P1/P2** unless you have observed real contention or deadlocks.

---

### P0-1 (bare exception handlers)
- The codebase does have overly broad exception handling (e.g. `except:` in `explore_web._extract_domain`).
- But not all broad exception handling is automatically “critical”; some is defensive coding for best-effort tools.

**Refined recommendation:**
- Keep a ticket to remove `except:` (bare) → **always** specify exception types.
- For `except Exception:` blocks, standardize:
  - Log at `debug` for non-critical parsing errors
  - Log at `warning` for expected external failures
  - Log at `error` for unexpected internal errors

**Priority suggestion:** P0 is fine for *bare `except:`*, but most `except Exception:` items are **P1/P2**.

---

### P0-5 (prompt injection sanitization)
- The concern is valid: external tool payloads are inserted into LLM context.
- The suggested sanitization (removing `SYSTEM:`/`USER:` strings) is **not sufficient by itself**.

**Refined recommendation:**
- “Sanitization” should be treated as *risk reduction* not a guarantee.
- Better practical measures:
  - Hard caps on tool result size (characters, items)
  - Quote tool results as data (clear delimiters, e.g. `BEGIN TOOL RESULT … END TOOL RESULT`)
  - Avoid letting tool output look like a chat transcript
  - Avoid including raw HTML / markdown that can look like instructions

**Priority suggestion:** keep as **P0/P1** depending on threat model.

---

### P1-10 (streaming tool results)
- Streaming tool results *into an LLM call* is not directly supported unless you restructure the conversation (multiple messages / iterative summarization).
- This is likely **P2/P3** and requires careful design to avoid *more* tokens.

---

### P1-7 (sync tool calls block event loop)
- The code often uses `run_in_executor`, which prevents event loop blocking, but can still saturate the threadpool.
- The right framing is “threadpool pressure / throughput limitation”, not “blocks the event loop”.

**Priority suggestion:** P1 is reasonable if you expect multi-user concurrency.

---

## 3) Missing / under-specified tickets (additions recommended)

### NEW-P0: Tool return-type contract violations (implicit `None`)
- At least one tool entrypoint appears to allow falling off the end of a function without returning a dict (example: `verify_news` needs verification in second pass).
- This is a *hard reliability failure* because downstream code expects dict-like results.

**Why it matters:** one `None` return can cascade into LLM tool formatting failures and produce character crashes.

---

### NEW-P0/P1: Dependency management inconsistency (`requirements.txt` vs `pyproject.toml`)
- You have both `requirements.txt` and `pyproject.toml`, with **inconsistent version constraints**.
  - Example: `openai>=1.45.0` vs `openai>=2.8.1`.

**Why it matters:** nondeterministic installs, hard-to-reproduce bugs, and inconsistent runtime API behavior.

**Ticket recommendation:** pick *one* authoritative dependency source (likely `pyproject.toml` since you’re using `uv`) and either:
- Remove `requirements.txt`, or
- Generate it automatically from `pyproject.toml`.

---

### NEW-P0/P1: Memory read corruption handling
- Current memory `_read_memory()` calls don’t appear to catch `json.JSONDecodeError`.

**Why it matters:** a single partial write / external edit bricks the app.

**Recommendation:** on decode failure:
- Move corrupted file to `*.corrupt-<timestamp>.json`
- Start fresh with `{}`
- Log loudly

---

### NEW-P1: MCP tool schema quality + enforcement
- The MCP server tool registry (`src/cluas_mcp/server.py`) appears to define `required_args` **and** `inputSchema.required`. These can drift.

**Recommendation:**
- Make one canonical source of truth.
- Add a startup validation pass that checks consistency.

---

### NEW-P1: Tests for memory + tool contract
- Current plan refers to “add tests” but does not define a minimal test matrix.

**Recommendation:** add explicit test tickets:
- Memory read/write roundtrip
- Memory corruption recovery
- Tool functions return schema validation

---

## 4) Plan review (`001-PLAN.md`)

### Strengths
- Correctly front-loads the memory datetime bug.
- Uses checkpoints (human verification) at phase boundaries.
- Separates token efficiency work from robustness work.

### Plan weaknesses / changes recommended
- **Phase sequencing for P0 items is incomplete:**
  - The plan defers “prompt injection sanitization” (P0-5) and “automatic memory pruning” (P0-7) to tasks 23/24 at the end.
  - If these are truly P0, they should live in Phase 1.

- **Task 22 (async lock conversion) is underspecified and likely wrong as-written** (see ticket review above).

- **Index serialization requirement is risky:**
  - The plan suggests serializing indices to JSON; sets are not JSON-serializable.
  - A better approach is to rebuild indices on load (cheap enough) unless perf proves otherwise.

- **The plan needs an explicit dependency management task** (see missing tickets).

---

## 5) Actionable outputs from this pass

### Recommended edits to ticket list (summary)
- Downgrade P0-4 to P1/P2 unless you formalize concurrency model.
- Add new P0/P1 tickets:
  - Tool return contract correctness (no implicit `None`)
  - Dependency definition single source of truth
  - Memory corruption read recovery
  - MCP tool schema consistency validation

### Recommended edits to plan (summary)
- Move sanitization + memory pruning (if kept as P0) into Phase 1.
- Replace “asyncio.Lock conversion” task with a concurrency-model ticket.
- Add dependency management task early.

---

## Next steps
- Proceed with **second-pass code audit** focusing on:
  - `src/cluas_mcp/server.py` and `src/cluas_mcp/formatters.py` contracts
  - `src/cluas_mcp/common/*memory*.py` integrity and failure handling
  - `src/characters/*` tool formatting + error paths

(Second pass will include concrete file/line references and will update priority recommendations based on confirmed findings.)
