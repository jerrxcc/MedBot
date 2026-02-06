"""MedBot - AI Medical Assistant web application."""
import gradio as gr
from dotenv import load_dotenv

from src.llm import APICallError, APIKeyMissingError, build_messages, get_response
from src.prompts import get_prompt
from src.retriever import format_context, retrieve_with_fallback
from src.search_agent import MedicalSearchAgent

load_dotenv()

search_agent = MedicalSearchAgent()

COLLECTIONS = {
    "symptoms": "medquad_symptoms",
    "medication": "fda_drugs",
}

FEATURES = {
    "symptoms": {
        "title": "Symptom Analysis",
        "icon": "stethoscope",
        "placeholder": "Describe your symptoms... (e.g., I have a headache and feel dizzy)",
        "examples": [
            "I have a persistent headache and feel dizzy",
            "I've been coughing for a week with chest tightness",
            "I'm experiencing fatigue and shortness of breath",
        ],
    },
    "medication": {
        "title": "Medication Info",
        "icon": "pill",
        "placeholder": "Ask about any medication... (e.g., What is ibuprofen used for?)",
        "examples": [
            "What is ibuprofen used for?",
            "What are the side effects of metformin?",
            "Can I take aspirin with blood pressure medication?",
        ],
    },
    "doctors": {
        "title": "Find Doctor",
        "icon": "user-md",
        "placeholder": "Search for a doctor or specialty... (e.g., I need a Chinese speaking dentist)",
        "examples": [
            "I need a Chinese speaking dentist",
            "Find a heart specialist",
            "Search for Dr. Tan",
            "I have a bone fracture, who should I see?",
        ],
    },
}

FEATURE_ICONS = {
    "symptoms": "stethoscope",
    "medication": "pill",
    "doctors": "user-md",
}


def build_confidence_warning(confidence_level: str, fallback_used: bool = False) -> str:
    """Build a confidence warning message based on retrieval quality."""
    if confidence_level in ["high", "medium"]:
        return ""

    if confidence_level == "low":
        warning = (
            "**Note:** The information below is based on limited matches in our knowledge base. "
            "Please verify with a healthcare professional."
        )
    else:
        warning = (
            "**Important:** Our knowledge base has limited information about this topic. "
            "The response below may be incomplete or general. "
            "Please consult a qualified healthcare provider for accurate medical advice."
        )

    if fallback_used:
        warning += "\n\n*Results include information from multiple sources in our database.*"

    return f"\n\n---\n{warning}\n\n---\n\n"


def chat_handler(message: str, history: list, feature: str) -> str:
    """Process a chat message based on the selected feature."""
    if not message.strip():
        return ""

    try:
        if feature == "doctors":
            return search_agent.search(message)

        return _handle_rag_query(message, feature)

    except APIKeyMissingError:
        return (
            "### API Key Required\n\n"
            "Please configure your API key to use this feature:\n\n"
            "1. Create a `.env` file in the project root\n"
            "2. Add: `DEEPSEEK_API_KEY=your_key_here` or `OPENAI_API_KEY=your_key_here`\n"
            "3. Restart the application\n"
        )
    except APICallError as e:
        return f"### Connection Error\n\n{str(e)}\n\nPlease check your internet connection and try again."
    except Exception as e:
        return f"### Error\n\nSomething went wrong: {str(e)}"


def _handle_rag_query(message: str, feature: str) -> str:
    """Handle RAG-based queries for symptoms and medication."""
    collection_name = COLLECTIONS.get(feature, "medquad_symptoms")
    results = retrieve_with_fallback(message, collection_name, top_k=5)

    system_prompt = get_prompt(feature)
    messages = build_messages(system_prompt, message, format_context(results))
    response = get_response(messages)

    warning = build_confidence_warning(
        results.get("confidence_level", "none"),
        results.get("fallback_used", False)
    )

    return warning + response if warning else response


def create_chat_handler(feature: str):
    """Create a chat handler for a specific feature."""
    return lambda message, history: chat_handler(message, history, feature)


CUSTOM_CSS = """
.gradio-container { max-width: 1200px !important; margin: 0 auto !important; font-family: sans-serif; }
.header-container { text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 16px; color: white; margin-bottom: 2rem; }
.chatbot { border-radius: 12px !important; }
.submit-btn { background: #764ba2 !important; color: white !important; }
"""

TAB_ICONS = {"symptoms": "stethoscope", "medication": "pill", "doctors": "user-md"}


def create_tab(feature_key: str, feature_info: dict):
    """Create a tab with chat interface for a feature."""
    with gr.Tab(f"{feature_info['title']}"):
        chatbot = gr.Chatbot(label="", height=450)

        with gr.Row():
            msg_input = gr.Textbox(placeholder=feature_info['placeholder'], scale=9, container=False)
            submit_btn = gr.Button("Send", variant="primary", scale=1, elem_classes=["submit-btn"])

        gr.Examples(examples=feature_info['examples'], inputs=msg_input)
        clear_btn = gr.Button("Clear Chat", variant="secondary", size="sm")

        handler = create_chat_handler(feature_key)

        def respond(message, history, h=handler):
            if not message.strip():
                return "", history
            response = h(message, history)
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": response})
            return "", history

        msg_input.submit(respond, [msg_input, chatbot], [msg_input, chatbot])
        submit_btn.click(respond, [msg_input, chatbot], [msg_input, chatbot])
        clear_btn.click(lambda: (None, []), None, [msg_input, chatbot])


with gr.Blocks(title="MedBot - AI Medical Assistant") as app:
    gr.HTML("""
        <div class="header-container">
            <h1>MedBot</h1>
            <p>Your AI-Powered Medical Information Assistant</p>
        </div>
    """)

    with gr.Tabs():
        for feature_key, feature_info in FEATURES.items():
            create_tab(feature_key, feature_info)


if __name__ == "__main__":
    app.launch(server_name="127.0.0.1", server_port=7860, share=False, css=CUSTOM_CSS)
