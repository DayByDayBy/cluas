import gradio as gr
import tempfile
from pathlib import Path
import asyncio

# -------------------------------------------------------------------
# custom Theme (Space Grotesk, modern, clean, not too soft)
# -------------------------------------------------------------------
theme = gr.themes.Soft(
    primary_hue=gr.themes.colors.indigo,
    secondary_hue=gr.themes.colors.slate,
    neutral_hue=gr.themes.colors.gray,
    font=[gr.themes.GoogleFont("Space Grotesk"), "sans-serif"],
    font_mono=[gr.themes.GoogleFont("Space Grotesk"), "monospace"],
    radius_size=gr.themes.sizes.radius_md,
    spacing_size=gr.themes.sizes.spacing_md,
    text_size=gr.themes.sizes.text_md,
)

# -------------------------------------------------------------------
# export helper
# -------------------------------------------------------------------
async def run_deliberation_and_export(question, rounds, summariser):
    """Run the deliberation AND produce a downloadable .txt file."""
    
    if not question or question.strip() == "":
        return "Please enter a question.", None

    # Run your async deliberation
    history = await deliberate(question, rounds=rounds, summariser=summariser)

    # Format text for export
    text_content = "\n".join(f"{role}: {msg}" for role, msg in history)

    # create a temporary file
    tmp = Path(tempfile.mkstemp(suffix=".txt")[1])
    tmp.write_text(text_content, encoding="utf-8")

    return history, str(tmp)

# -------------------------------------------------------------------
# gradio Interface
# -------------------------------------------------------------------
with gr.Blocks() as demo:

    gr.Markdown(
        """
        # 🧠 Cluas Huginn — Council Deliberation
        Ask a question. Choose how many rounds the council debates.
        The characters then produce: **thesis → antithesis → synthesis**.
        """
    )

    chatbot = gr.Chatbot(
        label="Council Discussion",
        height=450,
        show_copy_button=True
    )

    with gr.Row():
        msg = gr.Textbox(
            placeholder="Ask the council a question...",
            label="Your Question",
            scale=4
        )

    with gr.Row():
        rounds_input = gr.Slider(
            minimum=1,
            maximum=4,
            value=1,
            step=1,
            label="Debate Rounds"
        )
        summariser_input = gr.Dropdown(
            ["Moderator", "Corvus", "Magpie", "Raven", "Crow"],
            value="Moderator",
            label="Summariser"
        )

    with gr.Row():
        deliberate_btn = gr.Button("Deliberate", elem_id="deliberate-btn").hover_text(
            "Enter a question, choose rounds, and watch the council deliberate:\n"
            "   thesis → antithesis → synthesis"
        )

        download_btn = gr.File(
            label="Download Chat",
            file_types=[".txt"],
            interactive=False,
        )

    # Wire it up
    deliberate_btn.click(
        fn=run_deliberation_and_export,
        inputs=[msg, rounds_input, summariser_input],
        outputs=[chatbot, download_btn]
    )

# -------------------------------------------------------------------
# launch (Gradio 6 theme pattern)
# -------------------------------------------------------------------
demo.launch(theme=theme, favicon_path=None)
