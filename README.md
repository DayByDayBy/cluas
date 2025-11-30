---
title: cluas_huginn
emoji: 💬
colorFrom: yellow
colorTo: purple
sdk: docker
pinned: false
hf_oauth: true
hf_oauth_scopes:
- inference-api
license: apache-2.0
short_description: A gathering of guides, a council of counsels
---

<div class="corvid-banner">
  <div class="corvid-banner-inner">
    <h1>The Corvidian Council</h1>
    <h2>A Multi-Agent Deliberation Engine</h2>
    <div class="corvid-banner-meta">Anno MMXXV — Hackathon Edition</div>
  </div>
</div>

<style>
.corvid-banner {
    width: 100%;
    display: flex;
    justify-content: center;
    margin: 24px 0 32px;
}

.corvid-banner-inner {
    background: #f5f4ef url('/file=static/paper.png') repeat;
    background-size: 200px;
    border: 2px solid rgba(139, 88, 40, 0.55); /* copper ink */
    padding: 24px 32px;
    border-radius: 12px;
    max-width: 720px;
    text-align: center;
    font-family: Labrada, serif;
    box-shadow:
        0 0 1px rgba(0,0,0,0.05),
        0 2px 6px rgba(0,0,0,0.06),
        0 6px 12px rgba(0,0,0,0.04);
}

/* Title */
.corvid-banner-inner h1 {
    font-size: 1.9rem;
    margin: 0;
    color: #4a3524; /* ink brown */
    font-weight: 700;
    letter-spacing: 0.02em;
}

/* Subtitle */
.corvid-banner-inner h2 {
    font-size: 1.05rem;
    margin: 6px 0 10px;
    font-weight: 500;
    color: #6a5648;
    letter-spacing: 0.03em;
}

/* Meta line */
.corvid-banner-meta {
    font-size: 0.9rem;
    color: rgba(70, 50, 35, 0.75);
    font-style: italic;
    letter-spacing: 0.04em;
}
</style>



An example chatbot using [Gradio](https://gradio.app), [`huggingface_hub`](https://huggingface.co/docs/huggingface_hub/v0.22.2/en/index), and the [Hugging Face Inference API](https://huggingface.co/docs/api-inference/index).


the above is just a template readme they gave me when I created this space on hugging face, feel free to ignore it.


# 🐦‍⬛ Cluas
*A gathering of guides, a council of counsels*

> **Clúas** (Gaelic: "ear") — a dialectic research tool where AI experts collaborate, remember, and build knowledge over time.

## What it Does

Corvid Council is a multi-agent MCP system that enables dialectic research 
through collaborative AI agents. Present a question to the council and watch 
as four specialized experts research, debate, and synthesize knowledge—building 
on past discussions through shared memory.

### Modes

- **Collaborative Mode**: Ask a question and receive synthesized research with sources  
- **Active Mode**: Join the discussion, steer research, challenge claims

### Dialectic Process

1. **Thesis**: Characters present initial findings using specialized tools  
2. **Antithesis**: Characters challenge, verify, and provide counter-evidence  
3. **Synthesis**: Council builds consensus and adds to collective memory  
4. **Evolution**: Future discussions build on accumulated knowledge

### Why It Matters

Most AI assistants are stateless. cluas_huginn Council remembers, learns, and builds knowledge over time.


### Characters

- Corvus: 🐦‍⬛ (black bird)  
- Magpie: 🪶 (feather, playful)  
- Raven: 🦅 (eagle, serious)  
- Crow: 🕊️ (dove, peaceful observer)

### Taglines

- "A gathering of guides, a council of counsels"  
- "Research that remembers, knowledge that accumulates"  
- "Multi-agent MCP research collective"


v2:

# Cluas Huginn: Multi-Agent Dialectic System

## What It Does
Four AI agents with distinct roles debate questions using structured dialectic.

## Architecture
- **Corvus**: Academic verifier (literature search)
- **Raven**: Accountability enforcer (news verification)
- **Magpie**: Trend explorer (pattern connector)
- **Crow**: Grounded observer (environmental data)

## Key Innovations
1. Unified inheritance architecture
2. Shared epistemic principles with character differentiation
3. Tool-use heuristics per character
4. Steelmanning and collaborative disagreement built-in

## Tech Stack
- Base: Python, Gradio
- LLMs: Groq/Nebius (Qwen 3)
- Tools: Academic search, news verification, web exploration
- Memory: Persistent character memories

## What Makes This Different
- Not just multiple LLMs - distinct epistemic roles
- Structured dialectic (thesis/antithesis/synthesis)
- Tool usage guided by character personality
- Collaborative, not adversarial












av




---

This project is licensed under the [Apache 2.0 License](LICENSE).