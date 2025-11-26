import gradio as gr
import logging
import asyncio
import html
import random
import re
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple
from src.characters.corvus import Corvus
from src.characters.magpie import Magpie
from src.characters.raven import Raven
from src.characters.crow import Crow




logger = logging.getLogger(__name__)

# init all characters
corvus = Corvus(location="Glasgow, Scotland")
magpie = Magpie(location="Brooklyn, NY")
raven = Raven(location="Seattle, WA")
crow = Crow(location="Tokyo, Japan")

CHARACTERS = [
    # (name, emoji, instance, delay, location)
    ("Corvus", "🐦‍⬛", corvus, 1.5, "Glasgow, Scotland"),
    ("Magpie", "🪶", magpie, 1.2, "Brooklyn, NY"),
    ("Raven", "🦅", raven, 1.0, "Seattle, WA"),
    ("Crow", "🕊️", crow, 1.0, "Tokyo, Japan")
]

CHARACTER_PERSONAS: Dict[str, Dict[str, str]] = {
    "Corvus": {
        "role": "Melancholic scholar focused on academic rigor",
        "tone": "Precise, evidence-driven, cites papers when relevant.",
    },
    "Magpie": {
        "role": "Sanguine trendspotter tracking cultural signals",
        "tone": "Upbeat, curious, highlights emerging stories and trivia.",
    },
    "Raven": {
        "role": "Choleric activist monitoring news and accountability",
        "tone": "Direct, justice-oriented, challenges misinformation.",
    },
    "Crow": {
        "role": "Phlegmatic observer studying patterns in nature",
        "tone": "Calm, methodical, references environmental signals.",
    },
}

CHARACTER_EMOJIS = {name: emoji for name, emoji, _, _, _ in CHARACTERS}




def parse_mentions(message: str) -> List[str] | None:
    """Extract @CharacterName mentions. Returns None if no mentions (all respond)."""
    pattern = r'@(Corvus|Magpie|Raven|Crow)'
    mentions = re.findall(pattern, message, re.IGNORECASE)
    return [m.capitalize() for m in mentions] if mentions else None



def format_message(character_name: str, message: str) -> Tuple[str, str]:
    """Format message with character name and emoji"""

    emoji = CHARACTER_EMOJIS.get(character_name, "💬")
    
    COLORS = {
        "Corvus": "#2596be",  # blue
        "Magpie": "#c91010",  # red
        "Raven": "#2E8B57",   # green
        "Crow": "#1C1C1C",    # dark gray
        "User": "#FFD700",    # gold/yellow
    }
    
    color = COLORS.get(character_name, "#FFFFFF")  # Default to white if not found
    formatted = f'{emoji} <span style="color:{color}; font-weight:bold;">{character_name}</span>: {message}'
    
    return formatted, character_name




async def get_character_response(character, message: str, history: List) -> str:
    """Get response from a character with graceful error handling"""
    conversation_history = []
    for msg in history:
        role = msg.get("role")
        content_blocks = msg.get("content", [])
        
        if content_blocks and isinstance(content_blocks, list):
            text = content_blocks[0].get("text", "") if content_blocks else ""
        else:
            text = ""
        
        conversation_history.append({"role": role, "content": text})
    
    try:
        response = await character.respond(message, conversation_history)
        return response
    except Exception as e:
        logger.error(f"{character.name} error: {str(e)}")
        
        # Character-specific error messages
        error_messages = {
            "Corvus": "*pauses mid-thought, adjusting spectacles* Hmm, I seem to have lost my train of thought...",
            "Magpie": "*distracted by something shiny* Oh! Sorry, what were we talking about?",
            "Raven": "*scowls* The systems are down. Typical.",
            "Crow": "*silent, gazing into the distance*"
        }
        return error_messages.get(character.name, f"*{character.name} seems distracted*")

async def chat_fn(message: str, history: list):
    """Async chat handler with sequential responses"""
    if not message.strip():
        yield history
        return
    
    sanitized_message = html.escape(message)
    
    history.append({
        "role": "user",
        "content": [{"type": "text", "text": sanitized_message}]
        })
    yield history
    
    mentioned_chars = parse_mentions(message)
    
    for name, emoji, char_obj, delay, location in CHARACTERS:
        if mentioned_chars and name not in mentioned_chars:
            continue
        # animated typing indicator
        for i in range(4):  # 4 states: "", ".", "..", "..."
            dots = "." * i  # Generates "", ".", "..", "..."
            typing_msg = {
            "role": "assistant",
            "content": [{"type": "text", "text": f"{emoji}{dots}"}]
        }
        if i == 0:
            history.append(typing_msg)
        else:
            history[-1]["content"][0]["text"] = f"{emoji}{dots}"
        yield history
        await asyncio.sleep(0.2)
            
        try:
            response = await get_character_response(
                char_obj, 
                sanitized_message, 
                history[:-1])
            history.pop()
            sanitized_response = html.escape(response)
            formatted, _ = format_message(name, sanitized_response)
            history.append({
                "role": "assistant", 
                "content": [{"type": "text", "text": formatted}]})
            yield history
            await asyncio.sleep(delay)
        except Exception as e:
            logger.error(f"{name} error: {e}")
            history.pop()
            yield history


def _phase_instruction(phase: str) -> str:
    instructions = {
        "thesis": "Present your initial perspective. Offer concrete signals, data, or references that support your stance.",
        "antithesis": "Critique or challenge earlier answers. Highlight blind spots, weak evidence, or alternative interpretations.",
        "synthesis": "Integrate the best ideas so far. Resolve tensions and propose a balanced, actionable view.",
    }
    return instructions.get(phase, "")


def _build_phase_prompt(
    *,
    phase: str,
    character_name: str,
    location: str,
    question: str,
    history_snippet: str,
) -> str:
    persona = CHARACTER_PERSONAS.get(character_name, {})
    role = persona.get("role", "council member")
    tone = persona.get("tone", "")
    phase_text = _phase_instruction(phase)
    history_block = history_snippet or "No prior discussion yet."

    return (
        f"You are {character_name}, {role} based in {location}. {tone}\n"
        f"PHASE: {phase.upper()}.\n"
        f"INSTRUCTION: {phase_text}\n\n"
        f"QUESTION / CONTEXT:\n{question}\n\n"
        f"RECENT COUNCIL NOTES:\n{history_block}\n\n"
        "Respond as a short chat message (2-4 sentences)."
    )


def _history_text(history: List[str], limit: int = 12) -> str:
    if not history:
        return ""
    return "\n".join(history[-limit:])


async def _neutral_summary(history_text: str) -> str:
    if not history_text.strip():
        return "No discussion available to summarize."
    prompt = (
        "You are the neutral moderator of the Corvid Council. "
        "Summarize the key points, agreements, and disagreements succinctly.\n\n"
        f"TRANSCRIPT:\n{history_text}"
    )
    return await get_character_response(corvus, prompt, [])


async def _summarize_cycle(history_text: str) -> str:
    prompt = (
        "Provide a concise recap (3 sentences max) capturing the thesis, antithesis, "
        "and synthesis highlights from the transcript below.\n\n"
        f"{history_text}"
    )
    return await get_character_response(corvus, prompt, [])


async def deliberate(
    question: str,
    rounds: int = 1,
    summariser: str = "moderator",
    format: Literal["llm", "chat"] = "llm",
    structure: Literal["nested", "flat"] = "nested",
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Run a dialectic deliberation (thesis → antithesis → synthesis) with the Corvid Council.

    Args:
        question: Topic to deliberate on.
        rounds: Number of full cycles (thesis/antithesis/synthesis). Each cycle deepens the analysis.
        summariser: "moderator" for neutral summary or one of the characters ("Corvus", ...).
        format: "llm" returns plain text history, "chat" returns display-ready HTML snippets.
        structure: "nested" groups responses by phase, "flat" returns a chronological list.
        seed: Optional seed to reproduce character ordering.

    Returns:
        Structured dict containing per-phase responses, cycle summaries, and final outcome.
    """
    question = question.strip()
    if not question:
        raise ValueError("Question is required for deliberation.")

    rounds = max(1, min(rounds, 5))
    rng = random.Random(seed)
    if seed is None:
        seed = rng.randint(0, 1_000_000)
        rng.seed(seed)

    char_order = CHARACTERS.copy()
    rng.shuffle(char_order)
    order_names = [name for name, *_ in char_order]

    conversation_llm: List[str] = []
    chat_history: List[Dict[str, Any]] = []
    phase_records: Dict[str, List[Dict[str, Any]]] = {
        "thesis": [],
        "antithesis": [],
        "synthesis": [],
    }
    flattened_records: List[Dict[str, Any]] = []
    cycle_summaries: List[Dict[str, Any]] = []

    async def run_phase(phase: str, base_context: str, cycle_idx: int) -> List[Dict[str, Any]]:
        history_excerpt = _history_text(conversation_llm)
        prompts = []
        tasks = []
        for name, _, character, _, location in char_order:
            prompt = _build_phase_prompt(
                phase=phase,
                character_name=name,
                location=location,
                question=base_context,
                history_snippet=history_excerpt,
            )
            prompts.append((name, prompt))
            tasks.append(get_character_response(character, prompt, []))

        responses = await asyncio.gather(*tasks, return_exceptions=True)
        entries: List[Dict[str, Any]] = []

        for (name, prompt), response in zip(prompts, responses):
            if isinstance(response, Exception):
                logger.error("Phase %s: %s failed (%s)", phase, name, response)
                text = f"*{name} could not respond.*"
            else:
                text = response.strip()

            conversation_llm.append(f"[{phase.upper()} | Cycle {cycle_idx + 1}] {name}: {text}")
            display_text = html.escape(text)
            formatted, _ = format_message(name, display_text)
            chat_entry = {"role": "assistant", "content": [{"type": "text", "text": formatted}]}
            chat_history.append(chat_entry)

            entry = {
                "cycle": cycle_idx + 1,
                "phase": phase,
                "name": name,
                "content": text,
                "prompt": prompt,
            }
            phase_records[phase].append(entry)
            flattened_records.append(entry)
            entries.append(entry)

        return entries

    cycle_context = question

    for cycle_idx in range(rounds):
        thesis_entries = await run_phase("thesis", cycle_context, cycle_idx)
        antithesis_entries = await run_phase("antithesis", cycle_context, cycle_idx)
        synthesis_entries = await run_phase("synthesis", cycle_context, cycle_idx)

        cycle_text = _history_text(conversation_llm, limit=36)
        summary_text = await _summarize_cycle(cycle_text)
        cycle_summaries.append({
            "cycle": cycle_idx + 1,
            "summary": summary_text,
        })
        cycle_context = f"{question}\n\nPrevious cycle summary:\n{summary_text}"

    full_history_text = "\n".join(conversation_llm)
    summariser_normalized = summariser.strip().lower()

    if summariser_normalized == "moderator":
        final_summary = await _neutral_summary(full_history_text)
        summary_author = "Moderator"
    else:
        name_map = {name.lower(): char for name, _, char, _, _ in CHARACTERS}
        selected = name_map.get(summariser_normalized)
        if not selected:
            raise ValueError(f"Unknown summariser '{summariser}'. Choose moderator or one of: {', '.join(order_names)}.")
        summary_prompt = (
            "Provide a concise synthesis (3 sentences max) from your perspective, referencing the discussion below.\n\n"
            f"{full_history_text}"
        )
        final_summary = await get_character_response(selected, summary_prompt, [])
        summary_author = summariser.title()

    history_output: List[Any]
    if format == "chat":
        history_output = chat_history
    else:
        history_output = conversation_llm

    if structure == "nested":
        phase_output: Dict[str, Any] = phase_records
    else:
        phase_output = flattened_records

    return {
        "question": question,
        "rounds": rounds,
        "seed": seed,
        "character_order": order_names,
        "structure": structure,
        "format": format,
        "phases": phase_output,
        "cycle_summaries": cycle_summaries,
        "final_summary": {
            "by": summary_author,
            "content": final_summary,
        },
        "history": history_output,
    }

# theme stuff

theme = gr.themes.Soft(
    primary_hue=gr.themes.colors.violet,       
    secondary_hue=gr.themes.colors.sky,       # accent
    neutral_hue=gr.themes.colors.slate,       # text, backgrounds, neutral elements

    spacing_size=gr.themes.sizes.spacing_md,  # mid spacing
    radius_size=gr.themes.sizes.radius_md,    # wee bit rounded
    text_size=gr.themes.sizes.text_md,        # readable body text

    font=gr.themes.GoogleFont("Space Grotesk"),           # main font: clarity & style
    font_mono=gr.themes.GoogleFont("IBM Plex Mono")       # monospace: system/chat/code
)

# create Gradio interface
with gr.Blocks(title="Cluas Huginn", theme=gr.themes.Base(theme="dark")) as demo:

    # Branding / tagline
    gr.Markdown("""
    <div style="text-align:center; color:#ccc;">
        <h1>🐦‍⬛ Cluas Huginn</h1>
        <p><i>A gathering of guides, a council of counsels</i></p>
        <p>Chat with the council of four corvid experts</p>
    </div>
    """)

    # Optional accordion for full character bios
    with gr.Accordion("Character Bios", open=False):
        bio_lines = "\n".join([
            f"- **{name}** {emoji}: {location}" 
            for name, emoji, _, _, location in CHARACTERS
        ])
        gr.Markdown(bio_lines)

    # Load avatars dynamically from folder
    avatar_folder = Path("avatars")
    avatar_images = [
        str(avatar_folder / f"{name.lower()}.png") 
        for name, *_ in CHARACTERS
    ]

    # Chatbot with avatars
    chatbot = gr.Chatbot(
        label="Council Discussion",
        height=600,
        show_label=True,
        avatar_images=tuple(avatar_images),
        user_avatar="avatars/user.png"
    )

    # User input row
    with gr.Row():
        msg = gr.Textbox(
            label="Your Message",
            placeholder="Ask the council a question...",
            scale=4,
            container=False,
        )
        submit_btn = gr.Button("Send", variant="primary", scale=1)

    # Handle submit
    msg.submit(chat_fn, [msg, chatbot], [chatbot], queue=True, show_progress=True)\
       .then(lambda: "", None, [msg])

    submit_btn.click(chat_fn, [msg, chatbot], [chatbot], queue=True, show_progress=True)\
              .then(lambda: "", None, [msg])
    
    gr.Markdown("""
    ### About
    The Corvid Council is a multi-agent system where four specialized AI characters collaborate to answer questions.
    Each character has access to different tools and brings their unique perspective to the discussion.
    """)
    
    # attribution footnote - small and unobtrusive
    gr.Markdown("""
    <p style="font-size: 0.7em; color: #999; text-align: center; margin-top: 2em;">
    Data sources: <a href="https://ebird.org" style="color: #999;">eBird.org</a>, PubMed, ArXiv
    </p>
    """)

    gr.api(
        deliberate,
        api_name="deliberate",
    )

# xxport for app.py
my_gradio_app = demo

if __name__ == "__main__":
    
    
    import sys
    
    if "--clear-memory" in sys.argv:
        print("Clearing all character memories...")
        corvus.clear_memory()
        magpie.clear_memory()
        raven.clear_memory()
        crow.clear_memory()
        print("Memory cleared!")
        sys.exit(0)
    
    demo.queue() 
    demo.launch(mcp_server=True, theme=theme)