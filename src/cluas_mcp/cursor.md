# src/cluas_mcp — Purpose
MCP tools, clients, and entrypoints used by character agents.

# Architecture
- academic/
- news/
- web/
- observation/
- common/
- domain/

# Context rules
- Load only the specific submodule being edited.
- Do not refactor across tool types without ticket approval.
- Preserve MCP server contracts and entrypoint signatures.

# Important files
- server.py
- tool_router.py
- abstract_filtered.py

# Ignore
- __pycache__, result.xml, .DS_Store, blah.py
