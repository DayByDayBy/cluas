import gradio as gr
import os
import logging
import asyncio
import html
import random
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple
from src.characters.corvus import Corvus
from src.characters.magpie import Magpie
from src.characters.raven import Raven
from src.characters.crow import Crow
from src.characters.neutral_moderator import Moderator
from src.characters.base_character import Character
from src.characters.registry import register_instance, get_all_characters, REGISTRY
from src.gradio.types import BaseMessage, UIMessage, to_llm_history, from_gradio_format


logger = logging.getLogger(__name__)

# instantiate characters (as you already do)
corvus = Corvus()
magpie = Magpie()
raven = Raven()
crow = Crow()
moderator_instance = Moderator()  # always available

# register them
register_instance(corvus)
register_instance(magpie)
register_instance(raven)
register_instance(crow)

# then use
CHARACTERS = get_all_characters()  # List[Character]


#  debate phases:
PHASE_INSTRUCTIONS = {
    "thesis": "Present your initial perspective. Offer concrete signals, data, or references that support your stance.",
    "antithesis": "Critique or challenge earlier answers. Highlight blind spots, weak evidence, or alternative interpretations.",
    "synthesis": "Integrate the best ideas so far. Resolve tensions and propose a balanced, actionable view.",
}

# load CSS:
CSS_PATH = Path(__file__).parent / "styles.css"
CUSTOM_CSS = CSS_PATH.read_text() if CSS_PATH.exists() else ""

def render_chat_html(history: list) -> str:
    html_parts = []
    
    for msg in history:
        if msg.speaker == "user":
            html_parts.append(f'''
                    <div class="chat-message user">
                        <div class="chat-avatar"><img src="avatars/user.png"></div>
                        <div class="chat-content">
                            <div class="chat-bubble">{html.escape(msg.content)}</div>
                        </div>
                    </div>
                ''')
        else:
            html_parts.append(f'''
                    <div class="chat-message {msg.speaker.lower()}">
                        <div class="chat-avatar"><img src="avatars/{msg.speaker.lower()}.png"></div>
                        <div class="chat-content">
                            <div class="chat-name">{msg.emoji} {msg.speaker}</div>
                            <div class="chat-bubble">{html.escape(msg.content)}</div>
                        </div>
                    </div>
                ''')    
    return "\n".join(html_parts)



def parse_mentions(message: str) -> list[str] | None:
    """Extract @CharacterName mentions. Returns None if no mentions (all respond)."""
    lookup = set(REGISTRY.keys())
    
    mentions = []
    for word in message.split():
        if not word.startswith("@"):
            continue
        name = word[1:].rstrip(".,!?;:").lower()
        if name in lookup:
            mentions.append(REGISTRY[name].name)
    return mentions or None


def format_message(character: Character, message: str) -> Tuple[str, str]:
    """Format message with character name and emoji"""
    emoji = getattr(character, "emoji", "💬")
    color = getattr(character, "color", "#FFFFFF")
    name = getattr(character, "name", "counsel") 
    
    formatted = f'{emoji} <span style="color:{color}; font-weight:bold;">{name}</span>: {message}'
    
    return formatted, name

async def get_character_response(char: Character, message: str, llm_history: List[Dict], user_key: Optional[str] = None) -> str:
    """Get response from a character; uses pre-formatted llm_history"""
    try:
        
        response = await char.respond(message, llm_history, user_key=user_key)
        return response
    except Exception as e:
        logger.error(f"{char.name} error: {str(e)}")
        
        # character-specific error messages
        error_messages = {
            "Corvus": "*pauses mid-thought, adjusting spectacles* Hmm, I seem to have lost my train of thought...",
            "Magpie": "*distracted by something shiny* Oh! Sorry, what were we talking about?",
            "Raven": "Internet being slow again. Typical.",
            "Crow": "*silent, gazing into the distance*"
        }
        return error_messages.get(char.name, f"*{char.name} seems distracted*")
        


async def chat_fn(message: str, history: list, user_key: Optional[str] = None):
    """async chat handler, using dataclasses internally"""
    if not message.strip():
        yield history
        return
    
    internal_history = [from_gradio_format(msg) for msg in history]
    
    user_msg = BaseMessage(role="user", speaker="user", content=message)
    internal_history.append(user_msg)
    
    history.append(user_msg.to_gradio_format())
    yield history
    
    mentioned_chars = parse_mentions(message)
    
    for char in CHARACTERS:
        if mentioned_chars and char.name not in mentioned_chars:
            continue
        
        # typing indicator
        for i in range(4):
            dots = "." * i
            typing_msg = UIMessage.from_character(char, f"{dots}", len(internal_history))

            if i == 0:
                history.append(typing_msg.to_gradio_format())
            else:
                history[-1] = typing_msg.to_gradio_format()
            yield history
            await asyncio.sleep(0.25)
        
        try:
            llm_history = to_llm_history(internal_history[-5:])
            response = await get_character_response(char, message, llm_history, user_key=user_key)
            
            history.pop()  # removes typing indicator
            
            ui_msg = UIMessage.from_character(char, response, len(internal_history))
            internal_history.append(ui_msg)
        
            
            formatted, _ = format_message(char, response)
            
            display_msg = BaseMessage(
                role="assistant",
                speaker=char.name.lower(),
                content=formatted
                )
            
            history.append(display_msg.to_gradio_format())
            yield history
            await asyncio.sleep(getattr(char, "delay", 1.0))
        except Exception as e:
            logger.error(f"{char.name} error: {e}")    
            history.pop()
            yield history
            
        

def _phase_instruction(phase: str) -> str:
    return PHASE_INSTRUCTIONS.get(phase, "")

def _build_phase_prompt(
    *,
    phase: str,
    char: Character,
    question: str,
    history_snippet: str,
) -> str:
    
    role = char.role
    tone = char.tone
    location = char.location
    phase_text = _phase_instruction(phase)
    history_block = history_snippet or "No prior discussion yet."

    return (
        f"You are {char.name}, {role} based in {location}. {tone}\n"
        f"PHASE: {phase.upper()}.\n"
        f"INSTRUCTION: {phase_text}\n\n"
        f"QUESTION / CONTEXT:\n{question}\n\n"
        f"RECENT COUNCIL NOTES:\n{history_block}\n\n"
        "Respond as a chat message (2-4 sentences is enough)."
    )


def _history_text(history: List[str], limit: int = 13) -> str:
    if not history:
        return ""
    return "\n".join(history[-limit:])


async def _neutral_summary(history_text: str, moderator: Character = None, user_key: Optional[str] = None) -> str:
    if not history_text.strip():
        return "No discussion to summarize."
    prompt = (
        "You are the moderator. "
        "Summarize the key points, agreements, and disagreements succinctly..\n\n"
        f"TRANSCRIPT:\n{history_text}"
    )
    return await get_character_response(moderator, prompt, [], user_key=user_key)


async def _summarize_cycle(history_text: str, moderator: Character = None, user_key: Optional[str] = None) -> str:
    prompt = (
        "Provide a concise recap (3 sentences max) capturing the thesis, antithesis, "
        "and synthesis highlights from the transcript below.\n\n"
        f"{history_text}"
    )
    return await get_character_response(moderator, prompt, [], user_key=user_key)

#  messaage format translators:

def to_llm_history(history: list[BaseMessage]) -> list[dict]:
    return [{"role": m.role, "content": m.content} for m in history]

def to_html(message: UIMessage) -> str:
    return f"""
    <div class="chat-message {message.speaker}">
        <div class="chat-avatar">{message.emoji}</div>
        <div class="chat-content">
            <div class="chat-bubble">{html.escape(message.content)}</div>
        </div>
    </div>
    """



async def deliberate(
    question: str,
    rounds: int = 1,
    summariser: str = "moderator",
    format: Literal["llm", "chat"] = "llm",
    structure: Literal["nested", "flat"] = "nested",
    seed: Optional[int] = None,
    user_key: Optional[str] = None,
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

    rounds = max(1, min(rounds, 3))
    
    if seed is None:
        seed = random.randint(0, 1_000_000)
    rng = random.Random(seed)

    char_order = CHARACTERS.copy()
    rng.shuffle(char_order)
    order_names = [char.name for char in char_order]

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
        
        for char in char_order:
            
            prompt = _build_phase_prompt(
                phase=phase,
                char=char,
                question=base_context,
                history_snippet=history_excerpt,
            )
            prompts.append((char.name, prompt))
            tasks.append(get_character_response(char, prompt, [], user_key=user_key))

        responses = await asyncio.gather(*tasks, return_exceptions=True)
        entries: List[Dict[str, Any]] = []

        for (name, prompt), response, char_obj in zip(prompts, responses, char_order):
            if isinstance(response, Exception):
                logger.error("Phase %s: %s failed (%s)", phase, name, response)
                text = f"*{name} could not respond.*"
            else:
                text = response.strip()

            conversation_llm.append(f"[{phase.upper()} | Cycle {cycle_idx + 1}] {name}: {text}")
            display_text = html.escape(text)
            formatted, _ = format_message(char_obj, display_text)
            chat_entry = {
                "role": "assistant",
                "content": [{"type": "text", "text": formatted}]
            }
            chat_history.append(chat_entry)
            
            entry = {
                "cycle": cycle_idx + 1,
                "phase": phase,
                "name": char.name,
                "content": text,
                "char": char, 
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
        summary_text = await _summarize_cycle(cycle_text, user_key=user_key)
        cycle_summaries.append({
            "cycle": cycle_idx + 1,
            "summary": summary_text,
        })
        cycle_context = f"{question}\n\nPrevious cycle summary:\n{summary_text}"

    full_history_text = "\n".join(conversation_llm)
    summariser_normalized = summariser.strip().lower()

    if summariser_normalized == "moderator":
        final_summary = await _neutral_summary(full_history_text, user_key=user_key)
        summary_author = "Moderator"
    else:
        name_map = {char.name.lower(): char for char in CHARACTERS}
        selected = name_map.get(summariser_normalized)
        if not selected:
            selected = moderator_instance  # fallback just in case
        summary_prompt = (
            "Provide a concise synthesis (3 sentences max) from your perspective, referencing the discussion below.\n\n"
            f"{full_history_text}"
        )
        final_summary = await get_character_response(selected, summary_prompt, [], user_key=user_key)
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


async def run_deliberation_and_export(question, rounds, summariser, user_key: Optional[str] = None):
    """Run the deliberation AND produce a downloadable .txt file."""
    
    if not question or question.strip() == "":
        return "<p>Please enter a question.</p>", None

    try:
        # run deliberation
        result = await deliberate(
            question, 
            rounds=rounds, 
            summariser=summariser,
            format="llm",  # to ensure it actually gets text format
            structure="flat",
            user_key=user_key
        )
        
       # format html for display
        display_html = format_deliberation_html(result["phases"])
        display_html += f'''
            <div class="delib-summary">
                <h3>Final Summary ({result['final_summary']['by']})</h3>
                <p>{html.escape(result['final_summary']['content'])}</p>
            </div>
        '''
        
        text_content = "\n\n".join(result["history"])
        
        
        # the code below could be it's own function, 
        # but it's not reused atm, so that seems wasteful.
        # worth keeping in mind for future use, tho.
        
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".txt")
        os.close(tmp_fd)
        
        header = (
                f"Question: {question}\n"
                f"Rounds: {rounds}\n"
                f"Summariser: {summariser}\n"
                f"Character Order: {', '.join(result['character_order'])}\n"
                + "=" * 80 + "\n\n"
            )

        footer = (
                "\n\n" + "=" * 80 + "\n"
                f"Final Summary ({result['final_summary']['by']}):\n"
                f"{result['final_summary']['content']}"
            )
    
        with open(tmp_path, "w", encoding="utf-8") as tmp_file:
            tmp_file.write(header)
            tmp_file.write(text_content)
            tmp_file.write(footer)
            
        return display_html, tmp_path
        
    except Exception as e:
        logger.error(f"Deliberation error: {e}", exc_info=True)
        return f"<p style='color: red;'>Error: {str(e)}</p>", None


def format_deliberation_html(entries: list | dict) -> str:
    
    """
        Convert flat list or nested dict of phase entries to styled HTML.
            - If dict: keys are phase names, values are lists of entries.
            - If list: expects structured entries with 'phase', 'cycle', 'name', 'content', 'char'.
    """    
    
    if isinstance(entries, dict):
        entries = [e for phase_list in entries.values() for e in phase_list]
    
    html_parts = ['<div class="deliberation-container">']
    
    for entry in entries:#
        phase = entry.get("phase", "unknown").lower()
        cycle = entry.get("cycle", 0)
        name = entry.get("name", "unknown")
        content = entry.get("content", "")
        char = entry.get("char")
        emoji = getattr(char, "emoji", "💬") if char else "💬"
        
        
        html_parts.append(f'''
                <div class="delib-message {phase} {name.lower()}">
                    <div class="delib-header">
                        <span class="delib-phase">{phase.capitalize()}</span>
                        <span class="delib-cycle">Cycle {cycle}</span>
                    </div>
                    <div class="delib-speaker">{emoji} {name}</div>
                    <div class="delib-content">{html.escape(content)}</div>
                </div>
            ''')
    
    html_parts.append('</div>')
    return ''.join(html_parts)

# Theme configuration
theme = gr.themes.Soft(
    primary_hue=gr.themes.colors.indigo,
    secondary_hue=gr.themes.colors.slate,
    neutral_hue=gr.themes.colors.gray,
    font=[gr.themes.GoogleFont("Labrada"), "serif"],
    font_mono=[gr.themes.GoogleFont("JetBrains Mono"), "monospace"],
    radius_size=gr.themes.sizes.radius_md,
    spacing_size=gr.themes.sizes.spacing_md,
    text_size=gr.themes.sizes.text_md,
)

# Create Gradio interface
with gr.Blocks(title="Cluas Huginn") as demo:

    # Branding / tagline
    gr.Markdown("""
    <div style="text-align:center; color:#ccc;">
        <h1>🐦‍⬛ Cluas Huginn</h1>
        <p><i>A gathering of guides, a council of counsels</i></p>
        <p>Chat with the council of four corvid experts</p>
    </div>
    """)

    # Tabs for Chat and Deliberation modes
    with gr.Tabs():
        
        # TAB 1: Chat mode
        with gr.Tab("Chat"):
            gr.Markdown("**Chat Mode:** Talk directly with the council. Use @CharacterName to address specific members.")
            
            # Optional accordion for full character bios
            with gr.Accordion("Character Bios", open=False):
                bio_lines = "\n".join([
                    f"- **{char.name}** {char.emoji}: {char.location}" 
                    for char in CHARACTERS
                ])
                gr.Markdown(bio_lines)

            # Load avatars dynamically from folder
            avatar_folder = Path("avatars")
            
            avatar_images = [
                str(avatar_folder / f"{char.name.lower()}.png") 
                for char in CHARACTERS
            ]

            # Chatbot with avatars
            chat_html = gr.HTML(elem_id="chat-container", interactive=True)
            chat_state = gr.State([])

            # User input row
            with gr.Row():
                msg = gr.Textbox(
                    label="Your Message",
                    placeholder="Ask the council a question...",
                    scale=3,
                    container=False,
                )
                user_key = gr.Textbox(
                    label="API Key (Optional)",
                    placeholder="OpenAI (sk-...), Anthropic (sk-ant-...), or HF (hf_...)",
                    type="password",
                    scale=2,
                    container=False,
                )
                submit_btn = gr.Button("Send", variant="primary", scale=1)

            # Handle submit
            msg.submit(chat_fn, [msg, chat_state, user_key], [chat_state], queue=True)\
                .then(render_chat_html, [chat_state], [chat_html])\
                .then(lambda: "", None, [msg])

            submit_btn.click(chat_fn, [msg, chat_state, user_key], [chat_state], queue=True)\
                .then(render_chat_html, [chat_state], [chat_html])\
                .then(lambda: "", None, [msg])
                
        # TAB 2: Deliberation mode
        with gr.Tab("Deliberation"):
            gr.Markdown("""
            ### 🧠 Council Deliberation
            Ask a question and let the council engage in structured debate:
            **thesis** (initial perspectives) → **antithesis** (critiques) → **synthesis** (integration).
            """)

            with gr.Row():
                question_input = gr.Textbox(
                    label="Question for the Council",
                    placeholder="What would you like the council to deliberate on?",
                    lines=3,
                    scale=2,
                )
                delib_user_key = gr.Textbox(
                    label="API Key (Optional)",
                    placeholder="OpenAI (sk-...), Anthropic (sk-ant-...), or HF (hf_...)",
                    type="password",
                    scale=1,
                )

            with gr.Row():
                rounds_input = gr.Slider(
                    minimum=1,
                    maximum=3,
                    value=1,
                    step=1,
                    label="Debate Rounds",
                    info="More rounds = deeper analysis"
                )
                summariser_input = gr.Dropdown(
                    ["Moderator", "Corvus", "Magpie", "Raven", "Crow"],
                    value="Moderator",
                    label="Final Summariser",
                    info="Who provides the final synthesis?"
                )

            deliberate_btn = gr.Button("🎯 Deliberate", variant="primary", scale=1, elem_id="deliberate-btn")
            deliberation_output = gr.HTML(label="Deliberation Output")

            download_btn = gr.DownloadButton(
                label="📥 Download Transcript",
                variant="secondary",
)

            # Wire up deliberation
            deliberate_btn.click(
                fn=run_deliberation_and_export,
                inputs=[question_input, rounds_input, summariser_input, delib_user_key],
                outputs=[deliberation_output, download_btn],
                queue=True,
                show_progress=True
            )

    gr.Markdown("""
    ### About
    The Corvid Council is a multi-agent system where four specialized AI characters collaborate to answer questions.
    Each character brings unique perspective and expertise to enrich the discussion.
    
    **Chat Mode:** Direct conversation with the council.
    **Deliberation Mode:** Structured debate using thesis-antithesis-synthesis framework.
    """)
    
    # Attribution footnote
    gr.Markdown("""
    <p style="font-size: 0.7em; color: #999; text-align: center; margin-top: 2em;">
    Data sources: <a href="https://ebird.org" style="color: #999;">eBird.org</a>, PubMed, ArXiv
    </p>
    """)

    gr.api(
        deliberate,
        api_name="deliberate",
    )


# Export for app.py
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
    demo.launch(theme=theme, css=CUSTOM_CSS)