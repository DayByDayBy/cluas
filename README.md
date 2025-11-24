---
title: cluas_huginn
emoji: 💬
colorFrom: yellow
colorTo: purple
sdk: gradio
sdk_version: '6'
app_file: app.py
pinned: false
hf_oauth: true
hf_oauth_scopes:
- inference-api
license: apache-2.0
short_description: a gathering of guides, a council of counsels
---

An example chatbot using [Gradio](https://gradio.app), [`huggingface_hub`](https://huggingface.co/docs/huggingface_hub/v0.22.2/en/index), and the [Hugging Face Inference API](https://huggingface.co/docs/api-inference/index).


the above is just a template readme they gave me when I created this space on hugging face, feel free to ignore it.


# 🐦‍⬛ Cluas
## *A gathering of guides, a council of counsels*

> **Clúas** (Gaelic: "ear") - A dialectic research tool where AI experts 
> collaborate, remember, and build knowledge over time.


## What if research could be conversational?

Corvid Council is a multi-agent MCP system that enables dialectic research 
through collaborative AI agents. Present a question to the council and watch 
as four specialized experts research, debate, and synthesize knowledge—building 
on past discussions through shared memory.

### Two Modes

**Collaborative Mode**: Ask a question, receive synthesized research with sources
**Active Mode**: Join the discussion, steer the research direction, challenge claims

### The Dialectic Process

1. **Thesis**: Characters present initial findings using specialized tools
2. **Antithesis**: Characters challenge, verify, and provide counter-evidence  
3. **Synthesis**: Council builds consensus, adds to collective memory
4. **Evolution**: Future discussions build on accumulated knowledge

### Why It Matters

Most AI assistants are stateless. Corvid Council remembers, learns, and 
builds institutional knowledge over time. It's not just answering questions—
it's conducting ongoing research.

- Corvus: 🐦‍⬛ (black bird)
- Magpie: 🪶 (feather, playful)
- Raven: 🦅 (eagle, serious)
- Crow: 🕊️ (dove, peaceful observer)

**Tagline variations**:

- "A gathering of guides, a council of counsels"
- Alt: "Research that remembers, knowledge that accumulates"
- Technical: "Multi-agent MCP research collective"

---

testing via pytest

live API calls:
```uv run --prerelease=allow pytest -q tests/clients```
non-calling tests:
```uv run --prerelease=allow pytest -q tests/clients/non_calling ```







This project is licensed under the [Apache 2.0 License](LICENSE).




"building-mcp-track-enterprise" for Track 1"
"building-mcp-track-consumer" for Track 1"
"building-mcp-track-creative" for Track 1"

"mcp-in-action-track-enterprise" for Track 2"
"mcp-in-action-track-consumer" for Track 2"
"mcp-in-action-track-creative" for Track 2"