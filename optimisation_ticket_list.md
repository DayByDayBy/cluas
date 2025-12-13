# CLUAS HUGINN: Optimization & Improvement Tickets

**Analysis Date:** December 13, 2025  
**Codebase Version:** Multi-agent dialectic deliberation engine  
**Analysis Focus:** Clean code, maintainability, efficiency, robustness, token optimization

---

## Executive Summary

CLUAS HUGINN demonstrates strong architectural foundations with clear separation of concerns, well-structured inheritance patterns, and thoughtful multi-agent orchestration. However, there are opportunities for optimization across code quality, prompt efficiency, error handling robustness, and operational resilience.

**Priority Distribution:**
- 🔴 **Critical (P0):** 8 tickets - Security, data integrity, error handling
- 🟠 **High (P1):** 12 tickets - Performance, maintainability, token efficiency  
- 🟡 **Medium (P2):** 10 tickets - Code quality, DRY violations, refactoring
- 🟢 **Low (P3):** 5 tickets - Nice-to-haves, polish, future-proofing

---

## 🔴 CRITICAL PRIORITY (P0) - Security & Robustness

### P0-1: Bare Exception Handlers Create Silent Failures
**Location:** `src/characters/base_character.py:71,76`, `src/cluas_mcp/web/explore_web.py:40`  
**Issue:** Multiple bare `except Exception:` and `except:` blocks swallow errors without proper handling or logging.

```python
# Current (DANGEROUS):
try:
    value = headers.get("retry-after")
except Exception:  # Too broad, hides bugs
    value = None

# Should be:
try:
    value = headers.get("retry-after")
except (AttributeError, KeyError, TypeError) as e:
    logger.debug(f"Failed to extract retry-after: {e}")
    value = None
```

**Impact:** Silent failures make debugging impossible; rate-limit extraction failures go unnoticed.  
**Fix Effort:** 2-3 hours  
**Token Impact:** None

---

### P0-2: Memory System Has No Corruption Protection
**Location:** `src/cluas_mcp/common/paper_memory.py`, `observation_memory.py`, `trend_memory.py`  
**Issue:** JSON files written without atomic writes, validation, or backup. Concurrent access or crashes during write = data loss.

```python
# Current (VULNERABLE):
def _write_memory(self, data: Dict):
    with open(self.memory_file, "w") as f:
        json.dump(data, f, indent=2)  # Crash here = corrupted file

# Should use atomic write pattern:
def _write_memory(self, data: Dict):
    temp_file = self.memory_file.with_suffix('.tmp')
    try:
        with open(temp_file, 'w') as f:
            json.dump(data, f, indent=2)
        temp_file.replace(self.memory_file)  # Atomic on POSIX
    except Exception as e:
        logger.error(f"Failed to write memory: {e}")
        if temp_file.exists():
            temp_file.unlink()
        raise
```

**Impact:** User data loss on crashes; no recovery mechanism.  
**Fix Effort:** 4-6 hours  
**Token Impact:** None

---

### P0-3: No Input Validation on Memory Operations
**Location:** All memory classes  
**Issue:** `add_item()`, `add_observation()`, `add_search()` accept arbitrary data without validation.

```python
# Current (UNSAFE):
def add_item(self, title: str, doi: Optional[str] = None, ...):
    key = title.lower()  # What if title is empty? Or 10MB?
    self.memory[key] = {...}

# Should validate:
def add_item(self, title: str, doi: Optional[str] = None, ...):
    if not title or not title.strip():
        raise ValueError("Title cannot be empty")
    if len(title) > 1000:
        raise ValueError("Title too long (max 1000 chars)")
    # ... validate other fields
```

**Impact:** Memory corruption from malformed data; potential DoS via large inputs.  
**Fix Effort:** 3-4 hours  
**Token Impact:** None

---

### P0-4: Race Conditions in Shared Provider Cooldown State
**Location:** `src/characters/base_character.py:21-23`  
**Issue:** Class-level shared state accessed by multiple async characters without proper synchronization beyond basic lock.

```python
# Current (RACE PRONE):
_provider_state_lock = threading.Lock()  # Threading lock in async context!
_provider_cooldown_until: Dict[str, float] = {}

# Should use asyncio primitives:
_provider_state_lock = asyncio.Lock()
# OR use thread-safe data structures if truly multi-threaded
```

**Impact:** Cooldown state corruption in concurrent scenarios; rate-limit bypass or over-throttling.  
**Fix Effort:** 2-3 hours  
**Token Impact:** None

---

### P0-5: Prompt Injection Vulnerability in Tool Results
**Location:** All `_format_*_for_llm()` methods in character files  
**Issue:** Tool results inserted into prompts without sanitization; malicious API responses could inject instructions.

```python
# Current (VULNERABLE):
def _format_news_for_llm(self, result: Dict[str, Any]) -> str:
    title = article.get("title", "Untitled")  # Unsanitized!
    lines.append(f"{idx}. {title} — {source}. {summary[:160]}...")
    return "\n".join(lines)

# Should sanitize:
def _sanitize_for_prompt(self, text: str) -> str:
    # Remove potential instruction injections
    text = text.replace("SYSTEM:", "").replace("USER:", "")
    # Truncate excessive length
    return text[:500]
```

**Impact:** Malicious news/paper titles could inject instructions to LLM.  
**Fix Effort:** 4-5 hours  
**Token Impact:** Minimal (sanitization overhead)

---

### P0-6: No Timeout on External API Calls
**Location:** `src/cluas_mcp/academic/arxiv.py`, `pubmed.py`, `semantic_scholar.py`  
**Issue:** Some API calls lack timeout parameters; can hang indefinitely.

```python
# Current (HANGS):
response = requests.get(url)  # No timeout!

# Should always have timeout:
response = requests.get(url, timeout=10)
```

**Impact:** Hung characters; degraded user experience; resource exhaustion.  
**Fix Effort:** 1-2 hours  
**Token Impact:** None

---

### P0-7: Memory Files Grow Unbounded
**Location:** All memory classes  
**Issue:** `prune_old()` methods exist but are never called automatically; memory files grow forever.

```python
# Should implement automatic pruning:
def _write_memory(self, data: Dict):
    # ... write logic ...
    
    # Auto-prune if memory exceeds threshold
    if len(self.memory) > 10000:
        self.prune_old(older_than_days=365)
```

**Impact:** Disk space exhaustion; slow memory operations; JSON parse failures on huge files.  
**Fix Effort:** 2-3 hours  
**Token Impact:** None

---

### P0-8: Datetime Arithmetic Bug in `paper_memory.py:92`
**Location:** `src/cluas_mcp/common/paper_memory.py:92`  
**Issue:** Subtracting timedelta from ISO string instead of datetime object.

```python
# Current (BROKEN):
cutoff = datetime.now(UTC).isoformat() - timedelta(days=older_than_days)
# TypeError: unsupported operand type(s) for -: 'str' and 'timedelta'

# Should be:
cutoff = datetime.now(UTC) - timedelta(days=older_than_days)
```

**Impact:** `prune_long_term()` method completely broken; never prunes old papers.  
**Fix Effort:** 5 minutes  
**Token Impact:** None

---

## 🟠 HIGH PRIORITY (P1) - Performance & Token Efficiency

### P1-1: Massive Prompt Duplication Across Characters
**Location:** `src/prompts/character_prompts.py`  
**Issue:** `GLOBAL_EPISTEMIC_NORMS` (59 lines) duplicated in every character's system prompt on every API call.

**Current Token Cost per Character:**
- Global norms: ~400 tokens
- Character-specific: ~600 tokens  
- **Total: ~1000 tokens per character per turn**

**In 4-character deliberation (3 phases):**
- 4 characters × 3 phases × 1000 tokens = **12,000 tokens just for system prompts**
- With tool calls (2× per phase): **~20,000 tokens**

**Optimization Strategy:**
```python
# Option 1: Compress global norms (50% reduction possible)
GLOBAL_EPISTEMIC_NORMS_COMPRESSED = """
EVIDENCE-FIRST: Prioritize verifiable info; admit uncertainty; distinguish data/interpretation/values.
DIALECTIC: Collaborate, not oppose. Critique claims, not people. Steelman disagreements. Build on each other.
TOOLS: Only when necessary to resolve contradictions. One per turn.
STYLE: 2-4 sentences. Concise. Pick 1-2 key points.
"""

# Option 2: Move repetitive instructions to user message
# Option 3: Use few-shot examples instead of verbose rules
```

**Impact:** 40-50% reduction in prompt tokens = faster responses + lower cost.  
**Fix Effort:** 6-8 hours (requires testing to maintain quality)  
**Token Savings:** ~8,000 tokens per deliberation

---

### P1-2: Redundant Tool Heuristics in Every Prompt
**Location:** `src/prompts/character_prompts.py:244-268` (repeated 4×)  
**Issue:** Each character has 20-30 lines of "When should you use X tool?" that could be condensed.

**Current (Verbose):**
```
When should you use `academic_search`?
→ When a claim lacks peer-reviewed backing
→ When someone references a topic you should verify
→ When you want to cite findings precisely

When should you use `explore_web`?
→ Rarely, mainly in support of academic_search...
```

**Optimized (Concise):**
```
TOOLS:
- academic_search: Verify claims, cite papers
- explore_web: Fill literature gaps (rare)
- check_local_weather: Contextual only
```

**Impact:** 30% reduction in character-specific prompt tokens.  
**Fix Effort:** 4-5 hours  
**Token Savings:** ~2,000 tokens per deliberation

---

### P1-3: Inefficient History Truncation Strategy
**Location:** `src/gradio/app.py:411,428,450,507` (repeated pattern)  
**Issue:** Always takes last 5 messages (`history[-5:]`) regardless of token count; wastes context on short messages.

```python
# Current (WASTEFUL):
messages.extend(history[-5:])  # Could be 5 words or 5,000 tokens

# Should be token-aware:
def truncate_history_by_tokens(history: List[Dict], max_tokens: int = 2000) -> List[Dict]:
    """Keep as much history as fits in token budget."""
    truncated = []
    token_count = 0
    for msg in reversed(history):
        msg_tokens = estimate_tokens(msg["content"])
        if token_count + msg_tokens > max_tokens:
            break
        truncated.insert(0, msg)
        token_count += msg_tokens
    return truncated
```

**Impact:** Better context utilization; fewer truncated conversations.  
**Fix Effort:** 3-4 hours  
**Token Savings:** Variable, ~10-20% better context efficiency

---

### P1-4: Duplicate `_call_llm` Implementation Across 5 Files
**Location:** All character files (corvus, raven, magpie, crow, neutral_moderator)  
**Issue:** 300+ lines of identical user-key handling code duplicated 5 times.

**Current:** Each character has ~200 lines of identical OpenAI/Anthropic/HF/etc. key handling.

**Solution:** Extract to base class or mixin:
```python
# base_character.py
class UserKeyMixin:
    def _try_user_key(self, user_key, messages, tools, temp, max_tokens):
        """Centralized user key handling for all providers."""
        # ... 200 lines of key detection/handling ...

# Characters just call:
class Corvus(Character, UserKeyMixin):
    def _call_llm(self, messages, tools, ...):
        if user_key:
            response = self._try_user_key(...)
            if response:
                return response
        # ... provider-specific logic ...
```

**Impact:** 1000+ lines of code reduction; single source of truth for key handling.  
**Fix Effort:** 6-8 hours  
**Token Impact:** None

---

### P1-5: Memory Queries Are O(n) Linear Scans
**Location:** All memory classes  
**Issue:** Every search iterates entire memory dict; slow with 10k+ items.

```python
# Current (SLOW):
def search_title(self, query: str) -> List[Dict]:
    query_lower = query.lower()
    return [item for item in self.memory.values()  # O(n) scan
            if query_lower in item["title"].lower()]

# Should use indexing:
class PaperMemory:
    def __init__(self, ...):
        self.memory = {}
        self._title_index = {}  # title_word -> set of keys
    
    def add_item(self, title, ...):
        # ... add to memory ...
        # Update index
        for word in title.lower().split():
            self._title_index.setdefault(word, set()).add(key)
```

**Impact:** 10-100× faster searches with large memory; enables real-time search.  
**Fix Effort:** 8-10 hours  
**Token Impact:** None

---

### P1-6: No Caching of System Prompts
**Location:** All character classes  
**Issue:** `get_system_prompt()` regenerates entire prompt on every call; includes memory formatting.

```python
# Current (WASTEFUL):
def get_system_prompt(self) -> str:
    recent_papers = self.paper_memory.get_recent(days=7)  # DB query!
    memory_context = _format_paper_memory(recent_papers)  # String ops!
    return base_prompt + memory_context  # String concat!

# Should cache with TTL:
@lru_cache(maxsize=1)
def _get_base_prompt(self) -> str:
    return base_prompt

def get_system_prompt(self) -> str:
    # Cache memory context for 5 minutes
    if not hasattr(self, '_memory_cache_time') or \
       time.time() - self._memory_cache_time > 300:
        self._memory_cache = _format_paper_memory(...)
        self._memory_cache_time = time.time()
    return self._get_base_prompt() + self._memory_cache
```

**Impact:** Faster response generation; reduced memory I/O.  
**Fix Effort:** 3-4 hours  
**Token Impact:** None

---

### P1-7: Synchronous Tool Calls Block Async Event Loop
**Location:** All `_respond_cloud()` methods  
**Issue:** Tool functions are sync but called in async context with `run_in_executor()`.

```python
# Current (BLOCKS):
tool_result = await loop.run_in_executor(None, lambda: tool_func(**args))
# Blocks thread pool; limited parallelism

# Should make tools async:
async def academic_search_async(term: str) -> dict:
    async with aiohttp.ClientSession() as session:
        # ... async API calls ...

# Then:
tool_result = await tool_func(**args)  # True async
```

**Impact:** Better concurrency; faster multi-character responses.  
**Fix Effort:** 12-16 hours (requires refactoring all tool functions)  
**Token Impact:** None

---

### P1-8: No Request Deduplication for Identical Queries
**Location:** Tool entrypoints  
**Issue:** If 2 characters ask same question simultaneously, both make identical API calls.

```python
# Should implement request deduplication:
_pending_requests = {}  # query -> Future

async def academic_search(term: str) -> dict:
    if term in _pending_requests:
        return await _pending_requests[term]  # Wait for existing request
    
    future = asyncio.create_task(_do_search(term))
    _pending_requests[term] = future
    try:
        return await future
    finally:
        del _pending_requests[term]
```

**Impact:** 50% reduction in duplicate API calls during deliberations.  
**Fix Effort:** 4-6 hours  
**Token Impact:** None

---

### P1-9: Inefficient String Concatenation in Formatters
**Location:** All `_format_*_for_llm()` methods  
**Issue:** Using `+=` and `f-strings` in loops instead of list joining.

```python
# Current (SLOW):
lines = []
for item in items:
    lines.append(f"{idx}. {title} — {source}. {summary[:160]}...")
return "\n".join(lines)  # Good!

# But some places do:
result = ""
for item in items:
    result += f"{item}\n"  # BAD: O(n²) string copies
```

**Impact:** Minor performance improvement; better practice.  
**Fix Effort:** 1-2 hours  
**Token Impact:** None

---

### P1-10: No Streaming for Long Tool Results
**Location:** All tool result formatting  
**Issue:** Large tool results (100+ papers) formatted entirely before sending to LLM.

```python
# Should stream results:
async def _format_and_stream_results(self, results):
    yield "Search results:\n"
    for i, item in enumerate(results[:10]):  # Limit + stream
        yield f"{i+1}. {item['title']}\n"
```

**Impact:** Faster time-to-first-token; better UX for users.  
**Fix Effort:** 6-8 hours  
**Token Impact:** None

---

### P1-11: Memory Formatting Includes Irrelevant Data
**Location:** `src/prompts/character_prompts.py:66-200`  
**Issue:** Memory context includes dates, mentioned_by, full metadata that LLM rarely uses.

```python
# Current (VERBOSE):
line = f"- {title} (mentioned by {mentioned_by}) [{date}]"
# ~50 tokens per paper

# Optimized (CONCISE):
line = f"- {title}"
# ~20 tokens per paper
```

**Impact:** 40-60% reduction in memory context tokens.  
**Fix Effort:** 2-3 hours  
**Token Savings:** ~500 tokens per character with memory

---

### P1-12: No Batch Processing for Memory Operations
**Location:** All memory classes  
**Issue:** Each `add_item()` writes entire file; 100 items = 100 file writes.

```python
# Should batch writes:
class PaperMemory:
    def __init__(self):
        self._write_buffer = []
        self._last_flush = time.time()
    
    def add_item(self, ...):
        self._write_buffer.append(item)
        if len(self._write_buffer) >= 10 or \
           time.time() - self._last_flush > 60:
            self.flush()
    
    def flush(self):
        # Write all buffered items at once
        self._write_memory(self.memory)
        self._write_buffer.clear()
        self._last_flush = time.time()
```

**Impact:** 10-100× faster bulk operations; reduced I/O.  
**Fix Effort:** 4-5 hours  
**Token Impact:** None

---

## 🟡 MEDIUM PRIORITY (P2) - Code Quality & Maintainability

### P2-1: Inconsistent Error Handling Patterns
**Location:** Throughout codebase  
**Issue:** Mix of `raise`, `return None`, `return {}`, logging vs. silent failure.

**Recommendation:** Establish consistent error handling strategy:
- Tool functions: Return structured error dict `{"error": "...", "fallback": true}`
- Memory operations: Raise specific exceptions
- Character methods: Log + return fallback response

**Fix Effort:** 8-10 hours

---

### P2-2: No Type Validation at Runtime
**Location:** All public APIs  
**Issue:** Type hints exist but no runtime validation; easy to pass wrong types.

```python
# Should use pydantic or runtime checks:
from pydantic import BaseModel, validator

class PaperItem(BaseModel):
    title: str
    doi: Optional[str]
    
    @validator('title')
    def title_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v
```

**Fix Effort:** 10-12 hours

---

### P2-3: Magic Numbers and Strings Throughout
**Location:** Everywhere  
**Issue:** Hardcoded values like `history[-5:]`, `max_results=5`, `days=7`, `timeout=10`.

```python
# Should use constants:
class Config:
    HISTORY_CONTEXT_SIZE = 5
    DEFAULT_MAX_RESULTS = 5
    MEMORY_RECENT_DAYS = 7
    API_TIMEOUT_SECONDS = 10
```

**Fix Effort:** 3-4 hours

---

### P2-4: Inconsistent Naming Conventions
**Location:** Various  
**Issue:** Mix of `get_recent()`, `search_title()`, `all_items()`, `all_entries()`, `all_observations()`.

**Should standardize:**
- `get_*` for single item retrieval
- `list_*` for collections
- `search_*` for filtered queries
- `find_*` for lookups

**Fix Effort:** 4-5 hours

---

### P2-5: No Logging Configuration
**Location:** Root level  
**Issue:** Logging initialized inconsistently; no central config; hard to control verbosity.

```python
# Should have centralized logging config:
# src/logging_config.py
import logging.config

LOGGING_CONFIG = {
    'version': 1,
    'formatters': {
        'detailed': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'detailed',
            'level': 'INFO'
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'cluas.log',
            'formatter': 'detailed',
            'level': 'DEBUG'
        }
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['console', 'file']
    }
}
```

**Fix Effort:** 2-3 hours

---

### P2-6: Empty `orchestrator.py` File
**Location:** `src/orchestrator.py`  
**Issue:** File exists but is empty; unclear if planned feature or dead code.

**Action:** Either implement or delete.  
**Fix Effort:** 5 minutes

---

### P2-7: Inconsistent Return Types
**Location:** Tool functions  
**Issue:** Some return `dict`, some return `Dict[str, Any]`, some return custom objects.

**Should standardize:** All tools return `ToolResult` dataclass:
```python
@dataclass
class ToolResult:
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    source: str = "unknown"
```

**Fix Effort:** 6-8 hours

---

### P2-8: No Docstring Standards
**Location:** Throughout  
**Issue:** Mix of Google-style, NumPy-style, and missing docstrings.

**Should adopt:** Consistent style (recommend Google) and enforce with linter.  
**Fix Effort:** 4-6 hours

---

### P2-9: Commented-Out Code in Production
**Location:** `src/cluas_mcp/academic/academic_search_entrypoint.py:17-26`  
**Issue:** Semantic Scholar code commented out with TODO.

```python
# Current:
# try:
#     sem_scho = SemanticScholarClient.search(term)
# except Exception as e:
#     logger.warning("Semantic Scholar search failed: %s", e)
#     sem_scho = []
```

**Action:** Either implement properly with feature flag or remove.  
**Fix Effort:** 1 hour

---

### P2-10: No Health Check Endpoints
**Location:** Missing  
**Issue:** No way to verify system health, memory status, API connectivity.

**Should add:**
```python
# src/health.py
def health_check() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "memory_files": {
            "paper_memory": Path("~/.cluas_mcp/paper_memory.json").exists(),
            # ...
        },
        "api_keys": {
            "groq": bool(os.getenv("GROQ_API_KEY")),
            "nebius": bool(os.getenv("NEBIUS_API_KEY")),
            # ...
        },
        "characters": [c.name for c in REGISTRY.values()]
    }
```

**Fix Effort:** 2-3 hours

---

## 🟢 LOW PRIORITY (P3) - Polish & Future-Proofing

### P3-1: No Metrics/Telemetry
**Issue:** No tracking of token usage, API costs, response times, error rates.

**Should add:** Basic metrics collection for monitoring.  
**Fix Effort:** 6-8 hours

---

### P3-2: No Configuration File
**Issue:** All config hardcoded or in env vars; no central config file.

**Should add:** `config.yaml` or `config.toml` for settings.  
**Fix Effort:** 4-5 hours

---

### P3-3: No Graceful Shutdown Handling
**Issue:** No cleanup on SIGTERM/SIGINT; memory may not flush.

**Should add:** Signal handlers to flush buffers and close connections.  
**Fix Effort:** 2-3 hours

---

### P3-4: No Rate Limit Metrics
**Issue:** Cooldown system exists but no visibility into how often it triggers.

**Should add:** Metrics on rate limit hits per provider/model.  
**Fix Effort:** 2-3 hours

---

### P3-5: No Automated Dependency Updates
**Issue:** Manual dependency management; security vulnerabilities may go unnoticed.

**Should add:** Dependabot or Renovate configuration.  
**Fix Effort:** 1 hour

---

## Summary Statistics

**Total Tickets:** 35

**By Priority:**
- P0 (Critical): 8 tickets
- P1 (High): 12 tickets
- P2 (Medium): 10 tickets
- P3 (Low): 5 tickets

**By Category:**
- Security/Robustness: 8 tickets
- Performance: 7 tickets
- Token Efficiency: 5 tickets
- Code Quality: 10 tickets
- Maintainability: 5 tickets

**Estimated Total Effort:** 140-180 hours

**Expected Token Savings:** ~10,000-12,000 tokens per deliberation (40-50% reduction)

---

## Recommended Implementation Order

### Phase 1: Critical Fixes (Week 1)
1. P0-8: Fix datetime bug (5 min)
2. P0-6: Add timeouts (2 hours)
3. P0-1: Fix bare exception handlers (3 hours)
4. P0-3: Add input validation (4 hours)
5. P0-2: Implement atomic writes (6 hours)

### Phase 2: Token Optimization (Week 2)
1. P1-1: Compress global norms (8 hours)
2. P1-2: Condense tool heuristics (5 hours)
3. P1-11: Optimize memory formatting (3 hours)
4. P1-3: Token-aware history truncation (4 hours)

### Phase 3: Code Quality (Week 3)
1. P1-4: Extract duplicate _call_llm code (8 hours)
2. P2-1: Standardize error handling (10 hours)
3. P2-3: Extract magic numbers (4 hours)
4. P2-5: Configure logging (3 hours)

### Phase 4: Performance (Week 4)
1. P1-5: Index memory searches (10 hours)
2. P1-6: Cache system prompts (4 hours)
3. P1-12: Batch memory writes (5 hours)
4. P1-8: Deduplicate requests (6 hours)

---

## Notes

- This analysis prioritizes **functional correctness** and **token efficiency** over code aesthetics
- Token optimization recommendations preserve semantic meaning while reducing verbosity
- Security issues (P0) should be addressed immediately
- Performance optimizations (P1) have high ROI for user experience
- Code quality improvements (P2) pay dividends in long-term maintainability

**Codebase Health Score: 7.5/10**
- Strong architecture ✅
- Good separation of concerns ✅
- Needs robustness improvements ⚠️
- Token efficiency can be significantly improved ⚠️
