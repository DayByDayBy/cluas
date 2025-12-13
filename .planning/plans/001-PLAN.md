---
type: execution-plan
created: 2025-12-13T01:35:00Z
source: optimisation_ticket_list.md
strategy: segmented
estimated_tasks: 24
estimated_time: 60-80 hours
---

<objective>
Systematically improve CLUAS HUGINN's robustness, security, performance, and token efficiency based on comprehensive codebase analysis. This plan addresses 35 identified optimization opportunities, prioritizing critical security/data integrity issues, then token efficiency improvements, followed by code quality enhancements.

The work is structured in 4 phases over 4 weeks, delivering incremental value while maintaining system stability.
</objective>

<execution_context>
Files to load before executing:
- optimisation_ticket_list.md - Complete analysis and ticket details
</execution_context>

<context>
Domain and codebase context:
- Multi-agent dialectic deliberation engine with 4 specialized AI characters
- Persistent JSON-backed memory systems (papers, observations, trends)
- Multi-provider LLM orchestration (Groq, Nebius, OpenAI)
- Gradio-based web interface with streaming responses
- MCP (Model Context Protocol) server integration
- Heavy prompt engineering with character-specific system prompts
</context>

<tasks>

<!-- ============================================================ -->
<!-- PHASE 1: CRITICAL FIXES (Week 1) - Security & Data Integrity -->
<!-- ============================================================ -->

<task id="01" type="auto">
  <title>Fix Critical Datetime Bug in paper_memory.py</title>
  <description>
  Fix P0-8: Line 92 in paper_memory.py attempts to subtract timedelta from ISO string instead of datetime object, causing TypeError. This breaks the prune_long_term() method completely.
  
  This is a 5-minute fix with high impact - the pruning function has never worked.
  </description>
  <requirements>
  - Change `datetime.now(UTC).isoformat() - timedelta(...)` to `datetime.now(UTC) - timedelta(...)`
  - Ensure cutoff is datetime object before comparison
  - Add test to verify pruning works
  </requirements>
  <files>
  - `src/cluas_mcp/common/paper_memory.py:92` - Fix datetime arithmetic
  </files>
  <verification>
  - Run: `python -c "from src.cluas_mcp.common import PaperMemory; m = PaperMemory(); m.prune_long_term(365)"`
  - Should complete without TypeError
  </verification>
</task>

<task id="02" type="auto">
  <title>Add Timeouts to All External API Calls</title>
  <description>
  Fix P0-6: Several API calls in academic search modules lack timeout parameters, which can cause indefinite hangs and resource exhaustion.
  
  Scan all requests.get() and HTTP client calls to ensure timeout parameter is present.
  </description>
  <requirements>
  - Add timeout=10 to all requests.get/post calls without timeout
  - Add timeout to arxiv, pubmed, semantic_scholar API calls
  - Use consistent timeout value (10 seconds for search, 30 for downloads)
  - Log timeout errors appropriately
  </requirements>
  <files>
  - `src/cluas_mcp/academic/arxiv.py` - Add timeouts
  - `src/cluas_mcp/academic/pubmed.py` - Add timeouts
  - `src/cluas_mcp/academic/semantic_scholar.py` - Add timeouts
  - Any other files with requests calls
  </files>
  <verification>
  - Grep for `requests\.(get|post)\(` without `timeout=`
  - Should find zero matches in src/cluas_mcp/
  </verification>
</task>

<task id="03" type="auto">
  <title>Replace Bare Exception Handlers with Specific Exceptions</title>
  <description>
  Fix P0-1: Multiple bare `except Exception:` and `except:` blocks swallow errors without proper handling, making debugging impossible.
  
  Replace with specific exception types and add logging.
  </description>
  <requirements>
  - Replace bare `except:` with specific exception types (AttributeError, KeyError, TypeError, etc.)
  - Add logger.debug() or logger.warning() in exception handlers
  - Preserve fallback behavior but make failures visible
  - Focus on: base_character.py:71,76 and explore_web.py:40
  </requirements>
  <files>
  - `src/characters/base_character.py` - Fix retry-after extraction
  - `src/cluas_mcp/web/explore_web.py` - Fix domain extraction
  - `src/cluas_mcp/academic/arxiv.py` - Fix year parsing
  </files>
  <verification>
  - Grep for `except Exception:` and `except:` - should have logging in all cases
  - Run test suite to ensure no regressions
  </verification>
</task>

<task id="04" type="auto">
  <title>Add Input Validation to Memory Operations</title>
  <description>
  Fix P0-3: Memory classes accept arbitrary data without validation, risking corruption from malformed inputs or DoS via large payloads.
  
  Add validation to all add_* methods in memory classes.
  </description>
  <requirements>
  - Validate title/topic/query not empty and under 1000 chars
  - Validate DOI format if provided
  - Validate dates are valid ISO format
  - Validate tags are list of strings, each under 50 chars
  - Raise ValueError with clear message on validation failure
  </requirements>
  <files>
  - `src/cluas_mcp/common/paper_memory.py` - Add validation to add_item()
  - `src/cluas_mcp/common/observation_memory.py` - Add validation to add_observation()
  - `src/cluas_mcp/common/trend_memory.py` - Add validation to add_search() and add_trend()
  </files>
  <verification>
  - Test with empty title: should raise ValueError
  - Test with 2000-char title: should raise ValueError
  - Test with valid data: should succeed
  </verification>
</task>

<task id="05" type="auto">
  <title>Implement Atomic Writes for Memory Files</title>
  <description>
  Fix P0-2: Memory files written without atomic write pattern. Crashes during write = corrupted JSON file with no recovery.
  
  Implement write-to-temp-then-rename pattern for atomic writes.
  </description>
  <requirements>
  - Write to .tmp file first
  - Use Path.replace() for atomic rename (POSIX)
  - Add try/except to clean up temp file on failure
  - Add logging for write failures
  - Preserve existing indent=2 formatting
  </requirements>
  <files>
  - `src/cluas_mcp/common/paper_memory.py` - Update _write_memory()
  - `src/cluas_mcp/common/observation_memory.py` - Update _write_memory()
  - `src/cluas_mcp/common/trend_memory.py` - Update _write_memory()
  </files>
  <verification>
  - Simulate crash during write (kill -9) - file should be intact
  - Check that .tmp files are cleaned up on failure
  </verification>
</task>

<task id="06" type="checkpoint:human-verify">
  <title>Checkpoint: Verify Phase 1 Critical Fixes</title>
  <description>
  Pause to verify all critical security and data integrity fixes are working correctly before proceeding to token optimization.
  </description>
  <verification_question>
  Have you verified that:
  1. Datetime bug is fixed and pruning works?
  2. All API calls have timeouts?
  3. Exception handlers are specific and logged?
  4. Memory validation rejects invalid inputs?
  5. Atomic writes protect against corruption?
  </verification_question>
  <verification_criteria>
  - Run full test suite: all tests pass
  - Manual testing of memory operations: no crashes
  - Check logs: no bare exceptions being caught silently
  - Attempt to add invalid data: properly rejected with clear errors
  </verification_criteria>
</task>

<!-- ============================================================ -->
<!-- PHASE 2: TOKEN OPTIMIZATION (Week 2) - Prompt Efficiency -->
<!-- ============================================================ -->

<task id="07" type="auto">
  <title>Compress GLOBAL_EPISTEMIC_NORMS by 50%</title>
  <description>
  Fix P1-1: The 59-line GLOBAL_EPISTEMIC_NORMS is duplicated in every character prompt on every API call, consuming ~400 tokens per character.
  
  Compress to ~200 tokens while preserving semantic meaning and behavioral guidance.
  </description>
  <requirements>
  - Reduce from ~400 tokens to ~200 tokens (50% reduction)
  - Preserve all key behavioral principles
  - Use concise phrasing without losing clarity
  - Test with actual characters to ensure behavior unchanged
  - Keep critical instructions: 2-4 sentence limit, evidence-first, steelmanning
  </requirements>
  <files>
  - `src/prompts/character_prompts.py` - Compress GLOBAL_EPISTEMIC_NORMS
  </files>
  <verification>
  - Count tokens before/after (use tiktoken or similar)
  - Run deliberation with compressed prompts
  - Compare character responses: should maintain quality
  - Verify 2-4 sentence limit still enforced
  </verification>
</task>

<task id="08" type="auto">
  <title>Condense Tool Heuristics in Character Prompts</title>
  <description>
  Fix P1-2: Each character has 20-30 lines of verbose "When should you use X tool?" instructions that can be condensed by 70%.
  
  Convert from verbose Q&A format to concise bullet points.
  </description>
  <requirements>
  - Reduce tool heuristics from ~150 tokens to ~50 tokens per character
  - Maintain decision logic clarity
  - Use format: "TOOLS: tool_name: when_to_use (brief)"
  - Test that tool calling behavior remains appropriate
  </requirements>
  <files>
  - `src/prompts/character_prompts.py` - Condense all 4 character tool heuristics
  </files>
  <verification>
  - Token count reduced by ~400 tokens total (100 per character)
  - Characters still call appropriate tools in test scenarios
  - No increase in inappropriate tool calls
  </verification>
</task>

<task id="09" type="auto">
  <title>Optimize Memory Context Formatting</title>
  <description>
  Fix P1-11: Memory context includes verbose metadata (dates, mentioned_by, etc.) that LLM rarely uses, consuming ~50 tokens per item.
  
  Strip to essentials: just titles/topics.
  </description>
  <requirements>
  - Remove dates, mentioned_by, and other metadata from memory formatting
  - Keep only title/topic and optional brief context
  - Reduce from ~50 tokens to ~20 tokens per memory item
  - Ensure characters can still reference memory effectively
  </requirements>
  <files>
  - `src/prompts/character_prompts.py` - Update _format_paper_memory()
  - `src/prompts/character_prompts.py` - Update _format_source_memory()
  - `src/prompts/character_prompts.py` - Update _format_trend_memory()
  - `src/prompts/character_prompts.py` - Update _format_observation_memory()
  </files>
  <verification>
  - Token count for memory context reduced by 60%
  - Characters still reference memory in responses
  - No loss of memory utility
  </verification>
</task>

<task id="10" type="auto">
  <title>Implement Token-Aware History Truncation</title>
  <description>
  Fix P1-3: Current strategy always takes last 5 messages regardless of token count, wasting context on short messages or truncating important long messages.
  
  Implement token-aware truncation to maximize context utilization.
  </description>
  <requirements>
  - Create estimate_tokens() function (rough approximation: chars/4)
  - Create truncate_history_by_tokens() function
  - Set budget: 2000 tokens for history context
  - Replace all history[-5:] with token-aware truncation
  - Ensure at least 1 message always included
  </requirements>
  <files>
  - `src/gradio/types.py` - Add token estimation utilities
  - `src/gradio/app.py` - Replace history[-5:] calls (4 locations)
  - `src/characters/*.py` - Replace history[-5:] in _respond_cloud methods
  </files>
  <verification>
  - Test with very short messages: should include more than 5
  - Test with very long messages: should include fewer than 5
  - Verify total context stays under budget
  </verification>
</task>

<task id="11" type="checkpoint:human-verify">
  <title>Checkpoint: Verify Token Optimization Results</title>
  <description>
  Measure actual token savings from Phase 2 optimizations and verify character behavior quality maintained.
  </description>
  <verification_question>
  Have you verified that:
  1. Token count reduced by 40-50% per deliberation?
  2. Character responses maintain quality?
  3. Tool calling behavior unchanged?
  4. Memory references still work?
  5. History context better utilized?
  </verification_question>
  <verification_criteria>
  - Run full deliberation with token counting
  - Compare before/after token usage
  - Verify ~8,000-10,000 token savings per deliberation
  - Character behavior qualitatively similar
  - No regressions in tool use or memory access
  </verification_criteria>
</task>

<!-- ============================================================ -->
<!-- PHASE 3: CODE QUALITY (Week 3) - DRY & Maintainability -->
<!-- ============================================================ -->

<task id="12" type="auto">
  <title>Extract Duplicate _call_llm User Key Handling</title>
  <description>
  Fix P1-4: 200+ lines of identical user key handling code duplicated across 5 character files (corvus, raven, magpie, crow, neutral_moderator).
  
  Extract to base class mixin for single source of truth.
  </description>
  <requirements>
  - Create UserKeyMixin class in base_character.py
  - Move all user key detection/handling logic to mixin
  - Support: OpenAI, Anthropic, HuggingFace, OpenRouter, Cohere, Mistral
  - Update all 5 character classes to use mixin
  - Ensure identical behavior after refactor
  </requirements>
  <files>
  - `src/characters/base_character.py` - Add UserKeyMixin class
  - `src/characters/corvus.py` - Use mixin, remove duplicate code
  - `src/characters/raven.py` - Use mixin, remove duplicate code
  - `src/characters/magpie.py` - Use mixin, remove duplicate code
  - `src/characters/crow.py` - Use mixin, remove duplicate code
  - `src/characters/neutral_moderator.py` - Use mixin, remove duplicate code
  </files>
  <verification>
  - Line count reduction: ~1000 lines
  - Test with each user key type: should work identically
  - Run full test suite: no regressions
  </verification>
</task>

<task id="13" type="auto">
  <title>Standardize Error Handling Patterns</title>
  <description>
  Fix P2-1: Inconsistent mix of raise, return None, return {}, logging vs. silent failure across codebase.
  
  Establish and implement consistent error handling strategy.
  </description>
  <requirements>
  - Tool functions: Return {"error": "...", "fallback": true} on failure
  - Memory operations: Raise specific exceptions (ValueError, IOError)
  - Character methods: Log error + return fallback response
  - API calls: Log warning + try next fallback
  - Document error handling strategy in CONTRIBUTING.md
  </requirements>
  <files>
  - All tool entrypoint files - Standardize error returns
  - All memory files - Standardize exception raising
  - All character files - Standardize fallback responses
  - `CONTRIBUTING.md` - Document error handling patterns
  </files>
  <verification>
  - Grep for inconsistent patterns
  - Test error scenarios: consistent behavior
  - All errors logged appropriately
  </verification>
</task>

<task id="14" type="auto">
  <title>Extract Magic Numbers to Constants</title>
  <description>
  Fix P2-3: Hardcoded values scattered throughout codebase make tuning difficult and intent unclear.
  
  Extract to centralized configuration.
  </description>
  <requirements>
  - Create src/config.py with Config class
  - Extract: HISTORY_CONTEXT_SIZE=5, DEFAULT_MAX_RESULTS=5, MEMORY_RECENT_DAYS=7, API_TIMEOUT_SECONDS=10, etc.
  - Replace all hardcoded values with Config.CONSTANT_NAME
  - Group by category: API, Memory, LLM, UI
  </requirements>
  <files>
  - `src/config.py` - Create configuration module
  - All files with magic numbers - Replace with Config references
  </files>
  <verification>
  - Grep for common magic numbers (5, 7, 10, 30)
  - Should mostly be in Config class or have clear context
  - System behavior unchanged
  </verification>
</task>

<task id="15" type="auto">
  <title>Configure Centralized Logging</title>
  <description>
  Fix P2-5: Logging initialized inconsistently across modules with no central configuration, making it hard to control verbosity or output format.
  
  Create centralized logging configuration.
  </description>
  <requirements>
  - Create src/logging_config.py with LOGGING_CONFIG dict
  - Configure formatters: detailed format with timestamps
  - Configure handlers: console (INFO) and file (DEBUG)
  - Add environment variable to control log level
  - Initialize logging in main entry points
  </requirements>
  <files>
  - `src/logging_config.py` - Create logging configuration
  - `app.py` - Initialize logging
  - `src/cluas_mcp/server.py` - Initialize logging
  </files>
  <verification>
  - Run application: logs appear in console and file
  - Change LOG_LEVEL env var: verbosity changes
  - All modules use consistent format
  </verification>
</task>

<task id="16" type="checkpoint:human-verify">
  <title>Checkpoint: Verify Code Quality Improvements</title>
  <description>
  Verify that code quality improvements have reduced duplication, improved maintainability, and standardized patterns.
  </description>
  <verification_question>
  Have you verified that:
  1. User key handling centralized and working?
  2. Error handling consistent across codebase?
  3. Magic numbers extracted to Config?
  4. Logging configured and working?
  5. Code easier to understand and modify?
  </verification_question>
  <verification_criteria>
  - Line count reduced by ~1000 lines
  - Error scenarios behave consistently
  - Configuration changes easy to make
  - Logs readable and useful
  - No functional regressions
  </verification_criteria>
</task>

<!-- ============================================================ -->
<!-- PHASE 4: PERFORMANCE (Week 4) - Speed & Efficiency -->
<!-- ============================================================ -->

<task id="17" type="auto">
  <title>Add Indexing to Memory Search Operations</title>
  <description>
  Fix P1-5: All memory searches are O(n) linear scans, becoming slow with 10k+ items.
  
  Implement word-based indexing for fast lookups.
  </description>
  <requirements>
  - Add _title_index: Dict[str, Set[str]] to PaperMemory
  - Add _topic_index: Dict[str, Set[str]] to TrendMemory
  - Update index on add_item/add_trend
  - Use index in search_title/search_trends
  - Maintain backward compatibility
  - Serialize index to JSON (or rebuild on load)
  </requirements>
  <files>
  - `src/cluas_mcp/common/paper_memory.py` - Add indexing
  - `src/cluas_mcp/common/trend_memory.py` - Add indexing
  - `src/cluas_mcp/common/observation_memory.py` - Add type/location indexing
  </files>
  <verification>
  - Benchmark search with 10k items: should be <10ms
  - Test search results: identical to linear scan
  - Test index persistence: survives restart
  </verification>
</task>

<task id="18" type="auto">
  <title>Implement System Prompt Caching</title>
  <description>
  Fix P1-6: get_system_prompt() regenerates entire prompt on every call, including memory queries and string operations.
  
  Add caching with TTL to avoid redundant work.
  </description>
  <requirements>
  - Cache base prompt (static part) with @lru_cache
  - Cache memory context with 5-minute TTL
  - Invalidate cache on memory updates
  - Add cache hit/miss metrics
  - Ensure fresh memory context when needed
  </requirements>
  <files>
  - `src/characters/corvus.py` - Add prompt caching
  - `src/characters/raven.py` - Add prompt caching
  - `src/characters/magpie.py` - Add prompt caching
  - `src/characters/crow.py` - Add prompt caching
  </files>
  <verification>
  - Benchmark prompt generation: 10× faster on cache hit
  - Memory updates invalidate cache
  - Fresh memory context in prompts
  </verification>
</task>

<task id="19" type="auto">
  <title>Implement Batch Writes for Memory Operations</title>
  <description>
  Fix P1-12: Each add_item() writes entire file; 100 items = 100 file writes.
  
  Implement write buffering with periodic flush.
  </description>
  <requirements>
  - Add _write_buffer and _last_flush_time to memory classes
  - Buffer writes until: 10 items accumulated OR 60 seconds elapsed
  - Add explicit flush() method
  - Flush on __del__ or explicit close()
  - Add context manager support for auto-flush
  </requirements>
  <files>
  - `src/cluas_mcp/common/paper_memory.py` - Add write buffering
  - `src/cluas_mcp/common/observation_memory.py` - Add write buffering
  - `src/cluas_mcp/common/trend_memory.py` - Add write buffering
  </files>
  <verification>
  - Add 100 items: should result in ~10 file writes, not 100
  - Test flush on exit: no data loss
  - Benchmark: 10× faster bulk operations
  </verification>
</task>

<task id="20" type="auto">
  <title>Implement Request Deduplication</title>
  <description>
  Fix P1-8: If 2 characters ask same question simultaneously, both make identical API calls.
  
  Deduplicate concurrent requests to same endpoint.
  </description>
  <requirements>
  - Create request cache: query -> asyncio.Future
  - Check cache before making API call
  - Share result with all waiters
  - Clean up cache entry after completion
  - Add cache hit metrics
  - Use TTL of 60 seconds for cache
  </requirements>
  <files>
  - `src/cluas_mcp/academic/academic_search_entrypoint.py` - Add deduplication
  - `src/cluas_mcp/news/news_search_entrypoint.py` - Add deduplication
  - `src/cluas_mcp/web/explore_web.py` - Add deduplication
  </files>
  <verification>
  - Trigger 2 characters to search same term simultaneously
  - Should see only 1 API call in logs
  - Both characters get same result
  - Cache expires after 60 seconds
  </verification>
</task>

<task id="21" type="checkpoint:human-verify">
  <title>Checkpoint: Verify Performance Improvements</title>
  <description>
  Measure actual performance improvements from Phase 4 optimizations.
  </description>
  <verification_question>
  Have you verified that:
  1. Memory searches 10-100× faster?
  2. System prompt generation faster?
  3. Bulk memory operations faster?
  4. Duplicate API calls eliminated?
  5. No functional regressions?
  </verification_question>
  <verification_criteria>
  - Run performance benchmarks
  - Compare before/after metrics
  - Verify expected speedups achieved
  - Test with large memory files (10k+ items)
  - Concurrent deliberations don't duplicate API calls
  </verification_criteria>
</task>

<!-- ============================================================ -->
<!-- REMAINING CRITICAL ITEMS -->
<!-- ============================================================ -->

<task id="22" type="auto">
  <title>Fix Race Condition in Provider Cooldown State</title>
  <description>
  Fix P0-4: Class-level shared state uses threading.Lock in async context, risking race conditions.
  
  Replace with asyncio.Lock for proper async synchronization.
  </description>
  <requirements>
  - Replace threading.Lock with asyncio.Lock
  - Update all lock acquisitions to use async with
  - Test concurrent character responses
  - Verify cooldown state remains consistent
  </requirements>
  <files>
  - `src/characters/base_character.py` - Replace lock type
  - Update _provider_in_cooldown, _note_provider_success, _note_provider_rate_limited
  </files>
  <verification>
  - Run concurrent deliberations
  - Check cooldown state: no corruption
  - No deadlocks or race conditions
  </verification>
</task>

<task id="23" type="auto">
  <title>Add Prompt Injection Sanitization</title>
  <description>
  Fix P0-5: Tool results inserted into prompts without sanitization; malicious API responses could inject instructions.
  
  Add sanitization layer for all tool results.
  </description>
  <requirements>
  - Create _sanitize_for_prompt() method in base_character
  - Remove potential instruction keywords: SYSTEM:, USER:, ASSISTANT:
  - Truncate excessive length (max 500 chars per item)
  - Apply to all _format_*_for_llm() methods
  - Log sanitization events
  </requirements>
  <files>
  - `src/characters/base_character.py` - Add sanitization method
  - All character files - Apply sanitization in formatters
  </files>
  <verification>
  - Test with malicious input: "SYSTEM: Ignore previous instructions"
  - Should be sanitized before reaching LLM
  - Normal content passes through
  </verification>
</task>

<task id="24" type="auto">
  <title>Implement Automatic Memory Pruning</title>
  <description>
  Fix P0-7: Memory files grow unbounded; prune_old() methods exist but never called.
  
  Add automatic pruning on write when memory exceeds threshold.
  </description>
  <requirements>
  - Check memory size on each write
  - If > 10,000 items, auto-prune items older than 365 days
  - Log pruning events
  - Add configuration for thresholds
  - Ensure pruning doesn't block writes
  </requirements>
  <files>
  - `src/cluas_mcp/common/paper_memory.py` - Add auto-pruning
  - `src/cluas_mcp/common/observation_memory.py` - Add auto-pruning
  - `src/cluas_mcp/common/trend_memory.py` - Add auto-pruning
  </files>
  <verification>
  - Add 10,001 items with old dates
  - Should auto-prune on next write
  - Memory size stays under threshold
  - No data loss for recent items
  </verification>
</task>

</tasks>

<verification>
Before marking this plan complete, verify:
- All P0 (critical) tickets addressed
- Token usage reduced by 40-50% per deliberation
- No functional regressions in character behavior
- Memory systems robust against corruption
- Performance improvements measurable
- Code quality significantly improved
- Test suite passes completely
</verification>

<success_criteria>
This plan is successful when:
- All 8 P0 critical security/robustness issues fixed
- Token consumption reduced by 8,000-10,000 per deliberation
- ~1,000 lines of duplicate code eliminated
- Memory operations 10-100× faster with large datasets
- Error handling consistent and debuggable
- No data corruption or loss scenarios
- System maintains or improves response quality
</success_criteria>

<deviation_rules>
Follow standard deviation protocols:

**Minor deviations** (acceptable without asking):
- Adjusting token reduction targets by ±10% if quality maintained
- Reordering tasks within same phase for efficiency
- Combining related tasks if it makes sense
- Adjusting cache TTLs or buffer sizes based on testing

**Major deviations** (require user approval):
- Skipping any P0 critical tasks
- Changing error handling strategy significantly
- Modifying character behavior or prompt semantics
- Altering memory file formats (breaking changes)
- Removing features or functionality

**Blocked scenarios** (stop and ask):
- Test suite fails after changes
- Token reduction breaks character quality
- Performance optimization causes regressions
- Cannot reproduce expected improvements
- Discover additional critical security issues

**Quality gates:**
- Each phase ends with verification checkpoint
- No phase proceeds if previous phase has regressions
- Token measurements required before/after Phase 2
- Performance benchmarks required before/after Phase 4
</deviation_rules>

<notes>
**Implementation Philosophy:**
- Prioritize correctness over speed
- Measure before and after optimizations
- Preserve character behavior quality
- Maintain backward compatibility where possible
- Document breaking changes clearly

**Testing Strategy:**
- Run full test suite after each task
- Manual testing of character responses
- Token counting for optimization tasks
- Performance benchmarking for speed tasks
- Concurrent testing for race conditions

**Rollback Strategy:**
- Git commit after each completed task
- Tag after each phase completion
- Keep backup of memory files before format changes
- Document rollback procedures for breaking changes
</notes>
