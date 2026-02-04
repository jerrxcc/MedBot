import gradio as gr
from src.retriever import retrieve_with_fallback, format_context
from src.llm import get_response, build_messages, is_api_configured, APIKeyMissingError, APICallError
from src.prompts import get_prompt
from src.search_agent import MedicalSearchAgent
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize search agent for finding doctors
search_agent = MedicalSearchAgent()

# Collection names for each feature
COLLECTIONS = {
    "symptoms": "medquad_symptoms",
    "medication": "fda_drugs",
    "records": "medical_records"
}

# Feature descriptions
FEATURES = {
    "symptoms": {
        "title": "Symptom Analysis",
        "icon": "🩺",
        "description": "Describe your symptoms for medical information",
        "placeholder": "Describe your symptoms... (e.g., I have a headache and feel dizzy)",
        "examples": [
            "I have a persistent headache and feel dizzy",
            "I've been coughing for a week with chest tightness",
            "I'm experiencing fatigue and shortness of breath"
        ]
    },
    "medication": {
        "title": "Medication Info",
        "icon": "💊",
        "description": "Ask about drugs, dosages, and interactions",
        "placeholder": "Ask about any medication... (e.g., What is ibuprofen used for?)",
        "examples": [
            "What is ibuprofen used for?",
            "What are the side effects of metformin?",
            "Can I take aspirin with blood pressure medication?"
        ]
    },
    "records": {
        "title": "Records Analysis",
        "icon": "📋",
        "description": "Understand medical reports and lab results",
        "placeholder": "Paste or describe medical records... (e.g., What does a hemoglobin of 10.5 mean?)",
        "examples": [
            "What does a hemoglobin level of 10.5 g/dL mean?",
            "Explain this diagnosis: Type 2 Diabetes Mellitus",
            "What is a normal blood pressure reading?"
        ]
    },
    "doctors": {
        "title": "Find Doctor",
        "icon": "👨‍⚕️",
        "description": "Find specialists and clinics in Singapore",
        "placeholder": "Search for a doctor or specialty... (e.g., I need a Chinese speaking dentist)",
        "examples": [
            "I need a Chinese speaking dentist",
            "Find a heart specialist",
            "Search for Dr. Tan",
            "I have a bone fracture, who should I see?"
        ]
    }
}


def chat_handler(message: str, history: list, feature: str) -> str:
    """Process a chat message based on the selected feature."""
    if not message.strip():
        return ""

    try:
        # Doctor Search Logic
        if feature == "doctors":
            return search_agent.search(message)

        # RAG Logic for other features
        collection_name = COLLECTIONS.get(feature, "medquad_symptoms")
        results = retrieve_with_fallback(message, collection_name, top_k=5)
        context = format_context(results)

        system_prompt = get_prompt(feature)
        messages = build_messages(system_prompt, message, context)

        response = get_response(messages)
        return response

    except APIKeyMissingError:
        return (
            "### ⚠️ API Key Required\n\n"
            "Please configure your DeepSeek API key to use this feature:\n\n"
            "1. Create a `.env` file in the project root\n"
            "2. Add: `DEEPSEEK_API_KEY=your_key_here`\n"
            "3. Get your key at [platform.deepseek.com](https://platform.deepseek.com/)\n"
            "4. Restart the application\n"
        )
    except APICallError as e:
        return f"### ⚠️ Connection Error\n\n{str(e)}\n\nPlease check your internet connection and try again."
    except Exception as e:
        return f"### ⚠️ Error\n\nSomething went wrong: {str(e)}"


def create_chat_handler(feature: str):
    """Create a chat handler for a specific feature."""
    def handler(message: str, history: list):
        return chat_handler(message, history, feature)
    return handler


# Modern CSS styling
CUSTOM_CSS = """
.gradio-container { max-width: 1200px !important; margin: 0 auto !important; font-family: sans-serif; }
.header-container { text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 16px; color: white; margin-bottom: 2rem; }
.chatbot { border-radius: 12px !important; }
.submit-btn { background: #764ba2 !important; color: white !important; }
"""

with gr.Blocks(title="MedBot - AI Medical Assistant") as app:
    gr.HTML(f"""
        <div class="header-container">
            <h1>🏥 MedBot</h1>
            <p>Your AI-Powered Medical Information Assistant</p>
        </div>
    """)

    with gr.Tabs() as tabs:
        for feature_key, feature_info in FEATURES.items():
            with gr.Tab(f"{feature_info['icon']} {feature_info['title']}"):
                with gr.Column():
                    chatbot = gr.Chatbot(label="", height=450)
                    with gr.Row():
                        msg_input = gr.Textbox(placeholder=feature_info['placeholder'], scale=9, container=False)
                        submit_btn = gr.Button("Send", variant="primary", scale=1, elem_classes=["submit-btn"])
                    
                    gr.Examples(examples=feature_info['examples'], inputs=msg_input)
                    clear_btn = gr.Button("🗑️ Clear Chat", variant="secondary", size="sm")

                    handler = create_chat_handler(feature_key)

                    def respond(message, history):
                        if not message.strip(): return "", history
                        response = handler(message, history)
                        history.append({"role": "user", "content": message})
                        history.append({"role": "assistant", "content": response})
                        return "", history

                    msg_input.submit(respond, [msg_input, chatbot], [msg_input, chatbot])
                    submit_btn.click(respond, [msg_input, chatbot], [msg_input, chatbot])
                    clear_btn.click(lambda: (None, []), None, [msg_input, chatbot])

if __name__ == "__main__":
    app.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        css=CUSTOM_CSS
    )
