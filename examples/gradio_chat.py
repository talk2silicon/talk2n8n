from dotenv import load_dotenv; load_dotenv()
import gradio as gr
import os
from talk2n8n.agent.agent import Agent

# Load environment variables for agent config
N8N_WEBHOOK_BASE_URL = os.environ.get("N8N_WEBHOOK_BASE_URL")
N8N_API_KEY = os.environ.get("N8N_API_KEY")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL")
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY")

# Initialize the agent (adjust args as needed for your Agent class)
agent = Agent(
    n8n_base_url=N8N_WEBHOOK_BASE_URL,
    n8n_api_key=N8N_API_KEY,
    # Add LLM/model args if your Agent requires them
)

def chat_fn(message, history):
    """
    message: str, the latest user message
    history: list of [user, agent] pairs
    """
    try:
        response = agent.process_message(message)
    except Exception as e:
        response = f"Error: {str(e)}"
    return response

with gr.Blocks() as demo:
    gr.Markdown("# 💬 talk2n8n Chat Demo")
    chatbot = gr.Chatbot(type="messages")
    msg = gr.Textbox(
        label="Your prompt",
        placeholder="Send introduction email to John using the email as john@gmail.com",
        lines=2,
    )
    send_btn = gr.Button("Send")

    def respond(user_message, chat_history):
        # Convert old tuple/list format to messages format if needed
        messages = []
        if chat_history and isinstance(chat_history[0], list):
            for user, agent in chat_history:
                messages.append({"role": "user", "content": user})
                messages.append({"role": "assistant", "content": agent})
        else:
            messages = chat_history or []
        # Add new user message
        messages.append({"role": "user", "content": user_message})
        agent_response = chat_fn(user_message, messages)
        messages.append({"role": "assistant", "content": agent_response})
        return "", messages

    send_btn.click(
        respond,
        inputs=[msg, chatbot],
        outputs=[msg, chatbot],
    )

if __name__ == "__main__":
    demo.launch()
