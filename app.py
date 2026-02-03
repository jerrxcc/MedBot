import gradio as gr
from src.retriever import retrieve_with_fallback, format_context
from src.llm import get_response, build_messages, is_api_configured, APIKeyMissingError, APICallError
from src.prompts import get_prompt
from src.config import DEFAULT_TOP_K

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
    }
}


def build_confidence_warning(confidence_level: str, fallback_used: bool = False) -> str:
    """Build a confidence warning message based on retrieval quality."""
    if confidence_level == "high":
        return ""

    if confidence_level == "medium":
        return ""

    if confidence_level == "low":
        warning = (
            "**Note:** The information below is based on limited matches in our knowledge base. "
            "Please verify with a healthcare professional."
        )
    else:  # very_low or none
        warning = (
            "**Important:** Our knowledge base has limited information about this topic. "
            "The response below may be incomplete or general. "
            "Please consult a qualified healthcare provider for accurate medical advice."
        )

    if fallback_used:
        warning += "\n\n*Results include information from multiple sources in our database.*"

    return f"\n\n---\n{warning}\n\n---\n\n"


def chat_with_rag(message: str, history: list, feature: str) -> str:
    """Process a chat message with RAG and confidence-aware responses."""
    if not message.strip():
        return ""

    try:
        collection_name = COLLECTIONS.get(feature, "medquad_symptoms")

        # Use enhanced retrieval with fallback
        results = retrieve_with_fallback(message, collection_name, top_k=DEFAULT_TOP_K)
        context = format_context(results)

        confidence_level = results.get("confidence_level", "none")
        fallback_used = results.get("fallback_used", False)

        system_prompt = get_prompt(feature)
        messages = build_messages(system_prompt, message, context)

        response = get_response(messages)

        # Add confidence warning if needed
        warning = build_confidence_warning(confidence_level, fallback_used)
        if warning:
            response = warning + response

        return response

    except APIKeyMissingError:
        return (
            "### ⚠️ API Key Required\n\n"
            "Please configure your DeepSeek API key to use this feature:\n\n"
            "1. Create a `.env` file in the project root\n"
            "2. Add: `DEEPSEEK_API_KEY=your_key_here`\n"
            "3. Get your key at [platform.deepseek.com](https://platform.deepseek.com/)\n"
            "4. Restart the application\n\n"
            f"---\n*Knowledge base ready: {len(results.get('documents', []))} relevant documents found*"
        )

    except APICallError as e:
        return f"### ⚠️ Connection Error\n\n{str(e)}\n\nPlease check your internet connection and try again."

    except Exception as e:
        return f"### ⚠️ Error\n\nSomething went wrong: {str(e)}"


def create_chat_handler(feature: str):
    """Create a chat handler for a specific feature."""
    def handler(message: str, history: list):
        return chat_with_rag(message, history, feature)
    return handler


# Modern CSS styling
CUSTOM_CSS = """
/* Global Styles */
.gradio-container {
    max-width: 1200px !important;
    margin: 0 auto !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
}

/* Header */
.header-container {
    text-align: center;
    padding: 2rem 1rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 16px;
    margin-bottom: 1.5rem;
    color: white;
}

.header-container h1 {
    font-size: 2.5rem !important;
    font-weight: 700 !important;
    margin-bottom: 0.5rem !important;
    color: white !important;
}

.header-container p {
    font-size: 1.1rem !important;
    opacity: 0.9;
    margin: 0 !important;
}

/* Status Badge */
.status-badge {
    display: inline-block;
    padding: 0.5rem 1rem;
    border-radius: 50px;
    font-size: 0.85rem;
    font-weight: 500;
    margin-top: 1rem;
}

.status-online {
    background: rgba(52, 211, 153, 0.2);
    color: #10b981;
    border: 1px solid rgba(52, 211, 153, 0.3);
}

.status-offline {
    background: rgba(251, 191, 36, 0.2);
    color: #f59e0b;
    border: 1px solid rgba(251, 191, 36, 0.3);
}

/* Feature Cards */
.feature-card {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 1.25rem;
    transition: all 0.2s ease;
    cursor: pointer;
}

.feature-card:hover {
    border-color: #667eea;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
    transform: translateY(-2px);
}

.feature-icon {
    font-size: 2rem;
    margin-bottom: 0.5rem;
}

.feature-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #1f2937;
    margin-bottom: 0.25rem;
}

.feature-desc {
    font-size: 0.875rem;
    color: #6b7280;
}

/* Chat Container */
.chat-container {
    background: #f9fafb;
    border-radius: 16px;
    padding: 1rem;
    min-height: 500px;
}

/* Chatbot Styling */
.chatbot {
    background: transparent !important;
    border: none !important;
}

.chatbot .message {
    padding: 1rem 1.25rem !important;
    border-radius: 16px !important;
    margin: 0.5rem 0 !important;
    max-width: 85% !important;
    line-height: 1.6 !important;
}

.chatbot .user {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    margin-left: auto !important;
    border-bottom-right-radius: 4px !important;
}

.chatbot .bot {
    background: white !important;
    color: #1f2937 !important;
    border: 1px solid #e5e7eb !important;
    border-bottom-left-radius: 4px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
}

/* Input Area */
.input-area {
    background: white;
    border-radius: 12px;
    padding: 0.75rem;
    border: 1px solid #e5e7eb;
    margin-top: 1rem;
}

.input-area textarea {
    border: none !important;
    background: transparent !important;
    font-size: 1rem !important;
    resize: none !important;
}

.input-area textarea:focus {
    box-shadow: none !important;
    outline: none !important;
}

/* Submit Button */
.submit-btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.75rem 1.5rem !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}

.submit-btn:hover {
    opacity: 0.9 !important;
    transform: scale(1.02) !important;
}

/* Example Buttons */
.example-btn {
    background: white !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 8px !important;
    padding: 0.6rem 1rem !important;
    font-size: 0.875rem !important;
    color: #4b5563 !important;
    transition: all 0.2s ease !important;
}

.example-btn:hover {
    border-color: #667eea !important;
    color: #667eea !important;
    background: #f5f3ff !important;
}

/* Tabs */
.tabs {
    border: none !important;
    background: transparent !important;
}

.tab-nav {
    background: white !important;
    border-radius: 12px !important;
    padding: 0.5rem !important;
    border: 1px solid #e5e7eb !important;
    margin-bottom: 1rem !important;
}

.tab-nav button {
    border: none !important;
    border-radius: 8px !important;
    padding: 0.75rem 1.25rem !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
    background: transparent !important;
    color: #6b7280 !important;
}

.tab-nav button.selected {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
}

/* Disclaimer */
.disclaimer {
    background: #fef3c7;
    border: 1px solid #fcd34d;
    border-radius: 10px;
    padding: 1rem;
    margin-top: 1.5rem;
    font-size: 0.875rem;
    color: #92400e;
}

/* Footer */
.footer {
    text-align: center;
    padding: 1.5rem;
    color: #9ca3af;
    font-size: 0.875rem;
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
    .chat-container {
        background: #1f2937;
    }
    .chatbot .bot {
        background: #374151 !important;
        color: #f3f4f6 !important;
        border-color: #4b5563 !important;
    }
    .feature-card {
        background: #1f2937;
        border-color: #374151;
    }
    .feature-title {
        color: #f3f4f6;
    }
}

/* Responsive */
@media (max-width: 768px) {
    .header-container h1 {
        font-size: 1.75rem !important;
    }
    .chatbot .message {
        max-width: 95% !important;
    }
}

/* Hide default Gradio elements */
.gradio-container footer {
    display: none !important;
}
"""

# Build the interface
with gr.Blocks(css=CUSTOM_CSS, title="MedBot - AI Medical Assistant", theme=gr.themes.Base()) as app:

    # Header
    gr.HTML(f"""
        <div class="header-container">
            <h1>🏥 MedBot</h1>
            <p>Your AI-Powered Medical Information Assistant</p>
            <div class="status-badge {'status-online' if is_api_configured() else 'status-offline'}">
                {'● Online' if is_api_configured() else '○ API Key Required'}
            </div>
        </div>
    """)

    # Main content with tabs
    with gr.Tabs() as tabs:
        for feature_key, feature_info in FEATURES.items():
            with gr.Tab(f"{feature_info['icon']} {feature_info['title']}"):
                with gr.Column():
                    # Chat interface
                    chatbot = gr.Chatbot(
                        label="",
                        height=450,
                        show_copy_button=True,
                        bubble_full_width=False,
                        avatar_images=(
                            None,  # User avatar (None = default)
                            "https://api.dicebear.com/7.x/bottts/svg?seed=medbot&backgroundColor=667eea"  # Bot avatar
                        ),
                        render_markdown=True,
                    )

                    # Input area
                    with gr.Row():
                        msg_input = gr.Textbox(
                            placeholder=feature_info['placeholder'],
                            label="",
                            lines=1,
                            max_lines=5,
                            scale=9,
                            container=False,
                        )
                        submit_btn = gr.Button("Send", variant="primary", scale=1, elem_classes=["submit-btn"])

                    # Examples
                    gr.Examples(
                        examples=feature_info['examples'],
                        inputs=msg_input,
                        label="Try these examples",
                    )

                    # Clear button
                    clear_btn = gr.Button("🗑️ Clear Chat", variant="secondary", size="sm")

                    # Event handlers
                    handler = create_chat_handler(feature_key)

                    def respond(message, history):
                        if not message.strip():
                            return "", history
                        response = handler(message, history)
                        history.append((message, response))
                        return "", history

                    msg_input.submit(respond, [msg_input, chatbot], [msg_input, chatbot])
                    submit_btn.click(respond, [msg_input, chatbot], [msg_input, chatbot])
                    clear_btn.click(lambda: (None, []), None, [msg_input, chatbot])

    # Disclaimer
    gr.HTML("""
        <div class="disclaimer">
            <strong>⚠️ Medical Disclaimer:</strong> This AI assistant provides general health information only.
            It is not a substitute for professional medical advice, diagnosis, or treatment.
            Always consult a qualified healthcare provider for medical concerns.
        </div>
    """)

    # Footer
    gr.HTML("""
        <div class="footer">
            Built with Gradio • Powered by RAG Technology • ChromaDB + Sentence Transformers
        </div>
    """)


if __name__ == "__main__":
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )
