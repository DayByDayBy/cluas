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



# 🐦‍⬛ cluas huginn (thought's ear)  🐦‍⬛
## - A Multi-Agent Research Council


<div class="corvid-banner">
  <div class="corvid-banner-inner">
    <h1>CLUAS HUGINN</h1>
    <h2>A Multi-Agent Deliberation Engine</h2>
    <div class="corvid-banner-meta">Anno MMXXV — MCP 1st Birthday Hackathon Edition</div>
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
    background-size: 300px;
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

*A gathering of guides, a council of counsels*

## What It Does

Four specialised AI agents with **distinct epistemic roles** debate questions using **structured dialectic**, building knowledge over time.

- **Thesis**: Present findings with evidence  
- **Antithesis**: Challenge, verify, and provide counterpoints  
- **Synthesis**: Build consensus and update shared memory

- **Evolution**: Future discussions build on accumulated knowledge


##  Why It's Different
- **Distinct epistemic roles**: Each agent uses specialized tools  
- **Structured dialectic**: Reduces bias, promotes steelmanning  
- **Persistent memory**: Knowledge accumulates over time  
- **Tool-personality mapping**: Raven verifies news, Corvus searches literature, etc.


### Modes

- **Collaborative Mode**: Ask a question and receive synthesised research with sources  
- **Active Mode**: Join the discussion, steer research, challenge claims, be 'the human in the loop'


## The Council
| Agent   | Role | Icon |
|---------|------|------|
| Corvus  | Academic verifier (literature) | 🐦‍⬛ |
| Raven   | Accountability enforcer (news, verification)  | 🦅 |
| Magpie  | Trend explorer (patterns, connections)       | 🪶 |
| Crow    | Grounded observer (data, environment)  | 🕊️ |



### Dialectic Process

1. **Thesis**: Characters present initial findings using specialized tools  
2. **Antithesis**: Characters challenge, verify, and provide counter-evidence  
3. **Synthesis**: Council builds consensus and adds to collective memory  
4. **Evolution**: Future discussions build on accumulated knowledge

### Why It Matters

Most AI assistants are stateless. cluas_huginn remembers, learns, and builds knowledge over time.

## 🛠 Tech Stack
- **Base**: Python, Gradio  
- **LLMs**: UserKeys/Groq/Nebius/etc (various models, llama3.3 main)  
- **Tools**: Academic search, news verification, web exploration  
- **Memory**: Persistent character memories  


### Taglines

- "A gathering of guides, a council of counsels"  
- "Research that remembers, knowledge that accumulates"  
- "Multi-agent MCP research collective"



## Key Innovations / What Makes This Different
1. Unified inheritance architecture
2. Shared epistemic principles with "Four Temperament" character differentiation
3. Tool-use heuristics per character, guided by personality
4. Steelmanning and collaborative disagreement built-in
5. Structured dialectic reduces bias (thesis/antithesis/synthesis)
6. Persistent memory: knowledge accumulates over time



---

This project is licensed under the [Apache 2.0 License](LICENSE).