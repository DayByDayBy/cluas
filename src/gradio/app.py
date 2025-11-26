import gradio as gr
import logging
import asyncio
import html
import re
from pathlib import Path
from typing import List, Tuple
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
    demo.launch(mcp_server=True)