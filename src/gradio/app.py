import gradio as gr
import os
import logging
import asyncio
import html
import random
import re
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
from gradio.themes import Monochrome



logger = logging.getLogger(__name__)

# Tool call sanitization
TOOL_CALL_PATTERN = re.compile(r"function=(\w+)>(.*?)</function>", re.DOTALL)

def sanitize_tool_calls(text: str) -> str:
    """Replace raw tool call markup with readable format."""
    def _replace(match):
        func = match.group(1)
        payload = match.group(2)
        return f"*Tool call · {func} {payload}*"
    return TOOL_CALL_PATTERN.sub(_replace, text)

# instantiate characters (as you already do)
corvus = Corvus()
magpie = Magpie()
raven = Raven()
crow = Crow()
moderator_instance = Moderator()

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

def clear_chat():
    """Clear the chat history."""
    return []

theme = Monochrome(
    font=["Söhne", "sans-serif"],
    font_mono=[gr.themes.GoogleFont("JetBrains Mono"), "monospace"],
    text_size="lg",
    primary_hue="blue",
    secondary_hue="blue",
    radius_size="lg",
)

theme.set(
    body_background_fill="#f5f4ef",
    block_background_fill="#ffffffd8",
)



def render_chat_html(history: List[Dict]) -> str:
    """Render chat history to HTML (supports streaming)."""
    html_parts = []
    
    for message in history:
        role = message.get("role", "")
        content = message.get("content", "")
        name = message.get("name", "")
        emoji = message.get("emoji", "")
        is_typing = message.get("typing", False)
        is_streaming = message.get("streaming", False)
        
        if role == "user":
            html_parts.append(f'''
                <div class="chat-message user">
                    <div class="chat-content">
                        <div class="chat-bubble">{html.escape(content)}</div>
                    </div>
                </div>
            ''')
        elif role == "assistant":
            css_class = f"chat-message {name.lower()}"
            if is_typing:
                css_class += " typing"
            elif is_streaming:
                css_class += " streaming"
            
            html_parts.append(f'''
                <div class="{css_class}">
                    <div class="chat-avatar">{emoji}</div>
                    <div class="chat-content">
                        <div class="chat-name">{name}</div>
                        <div class="chat-bubble">{html.escape(content)}</div>
                    </div>
                </div>
            ''')
    
    return ''.join(html_parts)



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
    color = getattr(character, "color", "#121314")
    name = getattr(character, "name", "counsel") 
    
    formatted = f'{emoji} <span style="color:{color}; font-weight:bold;">{name}</span>: {message}'
    
    return formatted, name

async def get_character_response_stream(char: Character, message: str, llm_history: List[Dict], user_key: Optional[str] = None):
    """Stream character response in real-time chunks."""
    try:
        logger.debug(f"Streaming {char.name}.respond() with message: {message[:50]}...")
        
        # Get the streaming response from character
        async for chunk in char.respond_stream(message, llm_history, user_key=user_key):
            if chunk:
                logger.debug(f"{char.name} streaming chunk: {chunk[:50]}...")
                yield chunk
        
        logger.debug(f"{char.name} stream completed")
        
    except Exception as e:
        logger.error(f"{char.name} streaming error: {str(e)}")
        # Fallback response
        error_messages = {
            "Corvus": "*pauses mid-thought, adjusting spectacles* I seem to have lost my train of thought...",
            "Magpie": "*distracted by something shiny* Oh! Sorry, what were we talking about?",
            "Raven": "Connection acting up again. Typical.",
            "Crow": "*silent, gazing into the distance*"
        }
        fallback = error_messages.get(char.name, f"*{char.name} seems distracted*")
        yield fallback

async def get_character_response(char: Character, message: str, llm_history: List[Dict], user_key: Optional[str] = None) -> str:
    """Get response from a character; uses pre-formatted llm_history"""
    try:
        logger.debug(f"Calling {char.name}.respond() with message: {message[:50]}...")
        full_response = ""
        async for chunk in get_character_response_stream(char, message, llm_history, user_key):
            full_response += chunk
        response = full_response
        logger.debug(f"{char.name} responded with: {response[:100] if response else '<EMPTY>'}")
        
        if not response or not response.strip():
            logger.warning(f"{char.name} returned empty response")
            # Fallback response when LLM returns empty
            error_messages = {
                "Corvus": "*pauses mid-thought, adjusting spectacles* I seem to have lost my train of thought...",
                "Magpie": "*distracted by something shiny* Oh! Sorry, what were we talking about?",
                "Raven": "Connection acting up again. Typical.",
                "Crow": "*silent, gazing into the distance*"
            }
            return error_messages.get(char.name, f"*{char.name} seems distracted*")
            
        return response
    except Exception as e:
        logger.error(f"{char.name} error: {str(e)}")
        import traceback
        logger.debug(f"Full traceback for {char.name}: {traceback.format_exc()}")
        
        # character-specific error messages
        error_messages = {
            "Corvus": "*pauses mid-thought, adjusting spectacles* Hmm, I seem to have lost my train of thought...",
            "Magpie": "*distracted by something shiny* Oh! Sorry, what were we talking about?",
            "Raven": "Internet being slow again. Typical.",
            "Crow": "*silent, gazing into the distance*"
        }
        return error_messages.get(char.name, f"*{char.name} seems distracted*")
        


async def chat_fn_stream(msg: str, history: List[Dict], user_key: Optional[str] = None):
    """Streaming chat function - yields updates in real-time."""
    if not msg or not msg.strip():
        yield history
        return
    
    internal_history = [from_gradio_format(msg) for msg in history]
    internal_history.append(BaseMessage(role="user", speaker="user", content=msg))
    
    # Parse mentions
    mentioned_names = parse_mentions(msg)
    if not mentioned_names:
        mentioned_names = [char.name for char in CHARACTERS]
    
    # Get mentioned characters (case insensitive)
    mentioned = []
    for name in mentioned_names:
        char = REGISTRY.get(name.lower())
        if char:
            mentioned.append(char)
        else:
            logger.warning(f"Character '{name}' not found in registry")
    
    if not mentioned:
        yield render_chat_html(history)
        return 
    
    # Add typing indicators
    for char in mentioned:
        history.append({
            "role": "assistant",
            "content": f"*{char.name} is thinking...*",
            "name": char.name,
            "emoji": char.emoji,
            "typing": True
        })
    
    yield render_chat_html(history)  # Show typing indicators
    
    # Remove typing indicators and add responses
    history.pop()  # Remove last typing indicator
    
    for char in mentioned:
        try:
            llm_history = to_llm_history(internal_history[-5:])
            await asyncio.sleep(0.5)  # Rate limiting delay
            
            # Stream response
            response = ""
            async for chunk in get_character_response_stream(char, msg, llm_history, user_key):
                response += chunk
                # Update with partial response (sanitized)
                sanitized_partial = sanitize_tool_calls(response)
                history.append({
                    "role": "assistant", 
                    "content": sanitized_partial,
                    "name": char.name,
                    "emoji": char.emoji,
                    "streaming": True
                })
                yield render_chat_html(history)
                history.pop()  # Remove for next update
            
            # Sanitize and final response
            sanitized_response = sanitize_tool_calls(response)
            history.append({
                "role": "assistant",
                "content": sanitized_response,
                "name": char.name,
                "emoji": char.emoji
            })
            internal_history.append(BaseMessage(role="assistant", speaker=char.name, content=sanitized_response))
            
        except Exception as e:
            logger.error(f"Error in chat_fn_stream for {char.name}: {e}")
            history.append({
                "role": "assistant",
                "content": f"*{char.name} seems distracted*",
                "name": char.name,
                "emoji": char.emoji
            })
    
    yield render_chat_html(history)  # Final result


async def chat_fn(msg: str, history: List[Dict], user_key: Optional[str] = None) -> str:
    """Non-streaming chat function that returns HTML."""
    result = []
    async for html_update in chat_fn_stream(msg, history, user_key):
        result.append(html_update)
    return result[-1] if result else render_chat_html(history)



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
    if moderator is None:
        moderator = moderator_instance

    prompt = (
        "You are the moderator. "
        "Summarize the key points, agreements, and disagreements succinctly..\n\n"
        f"TRANSCRIPT:\n{history_text}"
    )
    return await get_character_response(moderator, prompt, [], user_key=user_key)

async def _summarize_cycle(history_text: str, moderator: Character = None, user_key: Optional[str] = None) -> str:
    
    if moderator is None:
        moderator = moderator_instance
    
    prompt = (
        "Provide a concise recap (3 sentences max) capturing the thesis, antithesis, "
        "and synthesis highlights from the transcript below.\n\n"
        f"{history_text}"
    )
    return await get_character_response(moderator, prompt, [], user_key=user_key)



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
    Run a dialectic deliberation (thesis → antithesis → synthesis) with the council.

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
                text = sanitize_tool_calls(response.strip())
                logger.debug("Phase %s: %s response: '%s'", phase, name, text[:100] if text else "<EMPTY>")

            conversation_llm.append(f"[{phase.upper()} | Cycle {cycle_idx + 1}] {name}: {text}")
            # Don't escape here - format_message will handle HTML properly
            formatted, _ = format_message(char_obj, text)
            chat_entry = {
                "role": "assistant",
                "content": [{"type": "text", "text": formatted}]
            }
            chat_history.append(chat_entry)
            
            entry = {
                "cycle": cycle_idx + 1,
                "phase": phase,
                "name": char_obj.name,
                "content": text,
                "char": char_obj, 
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
        logger.info("Using moderator for final summary")
        final_summary = await _neutral_summary(full_history_text, user_key=user_key)
        summary_author = "Moderator"
    else:
        name_map = {char.name.lower(): char for char in CHARACTERS}
        selected = name_map.get(summariser_normalized)
        if not selected:
            logger.warning(f"Summariser '{summariser}' not found in characters; falling back to moderator")
            selected = moderator_instance
            summary_author = "Moderator"
        else:
            logger.info(f"Using {selected.name} for final summary")
            summary_author = summariser.title()
        
        if selected is None:
            raise RuntimeError(f"Failed to resolve summariser: '{summariser}' and moderator unavailable")
        
        summary_prompt = (
            "Provide a concise synthesis (3 sentences max) from your perspective, referencing the discussion below.\n\n"
            f"{full_history_text}"
        )
        final_summary = await get_character_response(selected, summary_prompt, [], user_key=user_key)

    if format == "chat":
        # Use proper HTML formatting for chat format
        if structure == "nested":
            history_output = format_deliberation_html(phase_records)
        else:
            history_output = format_deliberation_html(flattened_records)
    else:
        # LLM format returns plain text
        if structure == "nested":
            history_output = phase_records
        else:
            history_output = flattened_records

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
        
        # Handle different history formats
        history = result["history"]
        if isinstance(history, str):
            # HTML format - already a single string
            text_content = history
        elif isinstance(history, list):
            # LLM format - list of strings, join them
            if all(isinstance(item, str) for item in history):
                text_content = "\n\n".join(history)
            else:
                # Mixed format - extract text from dicts
                text_parts = []
                for item in history:
                    if isinstance(item, str):
                        text_parts.append(item)
                    elif isinstance(item, dict) and "content" in item:
                        if isinstance(item["content"], str):
                            text_parts.append(item["content"])
                        elif isinstance(item["content"], list):
                            # Extract text from Gradio format
                            for content_block in item["content"]:
                                if isinstance(content_block, dict) and "text" in content_block:
                                    text_parts.append(content_block["text"])
                text_content = "\n\n".join(text_parts)
        else:
            text_content = str(history)
        
        
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


# Create Gradio interface
with gr.Blocks(title="Cluas Huginn") as demo:

    # Branding / tagline
    gr.Markdown("""
    <div style="text-align:center; color:#806565;">
        <h1>cluas huginn</h1>
        <p><i>a gathering of guides, a council of counsels</i></p>
        <p>chat with a council of four corvid-obsessed agents</p>
    </div>
    """)

    # Tabs for Chat and Deliberation modes
    with gr.Tabs():
        
        # TAB 1: Chat mode
        with gr.Tab("Chat"):
            gr.Markdown("**Chat Mode:** Talk directly with the council. Use @CharacterName to address specific members.")

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
                    scale=4,
                    container=False,
                )
                submit_btn = gr.Button("Send", variant="primary", scale=1)
                clear_btn = gr.Button("Clear Chat", variant="secondary", scale=1)
            
            # Example questions
            gr.Examples(
                examples=[
                    "What do you think about artificial intelligence?",
                    "@Corvus Can you explain Stoicism?",
                    "@Crow @Raven Compare birds and technology",
                    "Tell me about something fascinating",
                    "@Magpie What's the most interesting thing you've found?"
                ],
                inputs=[msg],
                label="Example Questions"
            )
            
            # API Key input (separated with spacing)
            gr.HTML("<div style='margin-top: 20px;'></div>")  # Spacer
            with gr.Column(scale=2, min_width=300):
                user_key = gr.Textbox(
                    label="API Key (Optional)",
                    placeholder="OpenAI (sk-...), Anthropic (sk-ant-...), or HF (hf_...)",
                    type="password",
                    container=True,
                )

            # Handle submit with streaming
            msg.submit(chat_fn, [msg, chat_state, user_key], [chat_html], queue=True)\
                .then(lambda: "", None, [msg])

            submit_btn.click(chat_fn, [msg, chat_state, user_key], [chat_html], queue=True)\
                .then(lambda: "", None, [msg])
            
            clear_btn.click(clear_chat, outputs=[chat_state, chat_html])\
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

            deliberate_btn = gr.Button("Deliberate", variant="primary", scale=1, elem_id="deliberate-btn")
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
    Cluas Huginn is a multi-agent system where four specialized AI characters collaborate to answer questions.
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
    
    # Minimal fix for loading_status undefined error
    demo.load(js="window.loading_status = window.loading_status || {};")
    
    demo.queue()
    demo.launch(theme=theme, css=CUSTOM_CSS)