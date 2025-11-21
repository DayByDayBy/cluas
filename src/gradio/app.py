import gradio as gr
import asyncio
from typing import List, Tuple
from src.characters.corvus import Corvus
from src.characters.magpie import Magpie
from src.characters.raven import Raven
from src.characters.crow import Crow

# Initialize all characters
corvus = Corvus()
magpie = Magpie()
raven = Raven()
crow = Crow()

# Character avatars/emojis
CHARACTER_EMOJIS = {
    "Corvus": "🐦‍⬛",
    "Magpie": "🪶",
    "Raven": "🦅",
    "Crow": "🕊️"
}

def format_message(character_name: str, message: str) -> Tuple[str, str]:
    """Format message with character name and emoji"""
    emoji = CHARACTER_EMOJIS.get(character_name, "💬")
    formatted = f"{emoji} **{character_name}**: {message}"
    return formatted, character_name

async def get_character_response(character, message: str, history: List[Tuple[str, str]]) -> str:
    """Get response from a character"""
    # Convert Gradio history format to character format
    conversation_history = []
    for user_msg, assistant_msg in history:
        conversation_history.append({"role": "user", "content": user_msg})
        conversation_history.append({"role": "assistant", "content": assistant_msg})
    
    try:
        response = await character.respond(message, conversation_history)
        return response
    except Exception as e:
        return f"[{character.name} encountered an error: {str(e)}]"

def chat_fn(message: str, history: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    """Handle chat messages - all 4 characters respond sequentially"""
    if not message.strip():
        return history
    
    # Add user message to history
    history.append((message, None))
    
    # Get responses from all 4 characters sequentially
    # For MVP, we'll do this synchronously (no async handling yet)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Corvus responds first
        corvus_response = loop.run_until_complete(
            get_character_response(corvus, message, history[:-1])
        )
        corvus_formatted, _ = format_message("Corvus", corvus_response)
        history.append((None, corvus_formatted))
        
        # Magpie responds
        magpie_response = loop.run_until_complete(
            get_character_response(magpie, message, history[:-1])
        )
        magpie_formatted, _ = format_message("Magpie", magpie_response)
        history.append((None, magpie_formatted))
        
        # Raven responds
        raven_response = loop.run_until_complete(
            get_character_response(raven, message, history[:-1])
        )
        raven_formatted, _ = format_message("Raven", raven_response)
        history.append((None, raven_formatted))
        
        # Crow responds
        crow_response = loop.run_until_complete(
            get_character_response(crow, message, history[:-1])
        )
        crow_formatted, _ = format_message("Crow", crow_response)
        history.append((None, crow_formatted))
        
    finally:
        loop.close()
    
    return history

# Create Gradio interface
with gr.Blocks(title="Cluas - Corvid Council", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🐦‍⬛ Cluas - Corvid Council
    ## *A gathering of guides, a council of counsels*
    
    Chat with the council of four corvid experts:
    - **Corvus** 🐦‍⬛ (Melancholic - Scholar): Academic researcher
    - **Magpie** 🪶 (Sanguine - Enthusiast): Trend-spotter and fact-finder
    - **Raven** 🦅 (Choleric - Activist): News monitor and fact-checker
    - **Crow** 🕊️ (Phlegmatic - Observer): Nature watcher and pattern analyzer
    """)
    
    chatbot = gr.Chatbot(
        label="Council Discussion",
        height=600,
        show_label=True,
        avatar_images=(None, None),  # Can add custom avatars later
    )
    
    with gr.Row():
        msg = gr.Textbox(
            label="Your Message",
            placeholder="Ask the council a question...",
            scale=4,
            container=False,
        )
        submit_btn = gr.Button("Send", variant="primary", scale=1)
    
    # Handle submit
    msg.submit(chat_fn, [msg, chatbot], [chatbot]).then(
        lambda: "", None, [msg]
    )
    submit_btn.click(chat_fn, [msg, chatbot], [chatbot]).then(
        lambda: "", None, [msg]
    )
    
    gr.Markdown("""
    ### About
    The Corvid Council is a multi-agent system where four specialized AI characters collaborate to answer questions.
    Each character has access to different tools and brings their unique perspective to the discussion.
    """)

# Export for app.py
my_gradio_app = demo

if __name__ == "__main__":
    demo.launch()

