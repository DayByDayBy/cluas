## 2025-11-26
- Ported the Raven-style multi-provider logic into Corvus, Crow, and Magpie so each character now shares the same client bootstrapping, fallback strategy, and tool definition structure while keeping their unique prompts and tool behaviors intact.

## 2025-11-27
- Refactored the news SerpAPI integrations to the modern `serpapi.search` flow with shared formatting helpers, restored the Bing fallback path, and noted that the local smoke test failed early because the `serpapi` package is missing from the environment despite being listed in pyproject/uv.lock.

