import gradio as gr
from ..orchestrator import CouncilOrchestrator

# Create a single, shared instance of the orchestrator
orchestrator = CouncilOrchestrator()

def respond(message, history):
    """
    This function is called when the user submits a message.
    It passes the query to the orchestrator and formats the results.
    """
    # Get the raw results from the orchestrator
    search_results = orchestrator.process_query(message)

    if not search_results:
        yield "I couldn't find any relevant academic papers for that query."
        return

    # Format the results into a markdown string
    response = f"I found {len(search_results)} papers related to your query:\n\n"
    for i, paper in enumerate(search_results, 1):
        response += f"**{i}. {paper.get('title', 'No Title')}**\n"
        response += f"   - **Authors:** {paper.get('authors', 'N/A')}\n"
        response += f"   - **Published:** {paper.get('published', 'N/A')}\n"
        if paper.get('doi'):
            response += f"   - **DOI:** {paper.get('doi')}\n"
        if paper.get('link'):
            response += f"   - **Link:** [Read Paper]({paper.get('link')})\n"
        response += "\n"
    
    yield response


# Define the Gradio ChatInterface
chatbot = gr.ChatInterface(
    respond,
    title="Corvid Council",
    description="Ask a question to the council of AI crow experts. Corvus, the scholar, will search for relevant academic papers.",
    examples=["corvid cognition", "tool use in crows", "raven social behavior"],
)

# Define the main Gradio app layout
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    with gr.Sidebar():
        gr.Markdown("## About\nThis is a demo of the Corvid Council, a multi-agent research system. Currently, only the agent **Corvus** is active.")
    chatbot.render()

if __name__ == "__main__":
    demo.launch()
