import gradio as gr
from src.retriever import retrieve, format_context
from src.llm import get_response, build_messages, is_api_configured, APIKeyMissingError, APICallError
from src.prompts import get_prompt

# Collection names for each feature
COLLECTIONS = {
    "symptoms": "medquad_symptoms",
    "medication": "fda_drugs",
    "records": "medical_records"
}


def chat_with_rag(message: str, history: list, feature: str) -> str:
    """
    Process a chat message with RAG.

    Args:
        message: User's message
        history: Chat history
        feature: Feature type (symptoms/medication/records)

    Returns:
        Assistant's response
    """
    try:
        # Retrieve relevant context
        collection_name = COLLECTIONS.get(feature, "medquad_symptoms")
        results = retrieve(message, collection_name, top_k=5)
        context = format_context(results)

        # Build messages and get response
        system_prompt = get_prompt(feature)
        messages = build_messages(system_prompt, message, context)

        response = get_response(messages)
        return response

    except APIKeyMissingError:
        return (
            "**API Key Not Configured**\n\n"
            "To use this feature, please configure your DeepSeek API key:\n\n"
            "1. Copy `.env.example` to `.env`\n"
            "2. Add your API key: `DEEPSEEK_API_KEY=your_key_here`\n"
            "3. Get a key at: https://platform.deepseek.com/\n"
            "4. Restart the application\n\n"
            "---\n"
            f"*Retrieved {len(results.get('documents', []))} relevant documents from knowledge base.*"
        )

    except APICallError as e:
        return (
            "**API Error**\n\n"
            f"Failed to get response from DeepSeek API: {str(e)}\n\n"
            "Please check your internet connection and API key.\n\n"
            "---\n"
            f"*Retrieved {len(results.get('documents', []))} relevant documents from knowledge base.*"
        )

    except Exception as e:
        return (
            "**Error**\n\n"
            f"An unexpected error occurred: {str(e)}\n\n"
            "Please try again or contact support."
        )


def symptom_chat(message: str, history: list) -> str:
    """Handle symptom consultation chat."""
    return chat_with_rag(message, history, "symptoms")


def medication_chat(message: str, history: list) -> str:
    """Handle medication information chat."""
    return chat_with_rag(message, history, "medication")


def records_chat(message: str, history: list) -> str:
    """Handle medical records analysis chat."""
    return chat_with_rag(message, history, "records")


# Custom CSS for styling
custom_css = """
.gradio-container {
    max-width: 900px !important;
    margin: auto !important;
}
.tab-nav button {
    font-size: 16px !important;
    padding: 12px 24px !important;
}
.chatbot {
    min-height: 400px !important;
}
.api-status {
    padding: 10px;
    border-radius: 5px;
    margin-bottom: 10px;
}
.api-configured {
    background-color: #d4edda;
    color: #155724;
}
.api-missing {
    background-color: #fff3cd;
    color: #856404;
}
"""

# Check API status for display
api_status_text = (
    "**Status:** API Configured" if is_api_configured()
    else "**Status:** API Key Missing - Set `DEEPSEEK_API_KEY` in `.env` file"
)
api_status_class = "api-configured" if is_api_configured() else "api-missing"

# Build Gradio interface
with gr.Blocks(
    theme=gr.themes.Soft(
        primary_hue="blue",
        secondary_hue="green",
    ),
    css=custom_css,
    title="MedBot - AI Medical Assistant"
) as app:

    gr.Markdown(
        """
        # MedBot - AI Medical Assistant

        Welcome! I can help you with symptom information, medication details, and medical record analysis.

        > **Disclaimer:** This is an AI assistant for informational purposes only.
        > Always consult a healthcare professional for medical advice.
        """
    )

    gr.Markdown(api_status_text, elem_classes=[f"api-status {api_status_class}"])

    with gr.Tabs():
        # Symptom Consultation Tab
        with gr.Tab("Symptom Consultation"):
            gr.Markdown("Describe your symptoms and I'll provide relevant information.")
            symptom_interface = gr.ChatInterface(
                fn=symptom_chat,
                examples=[
                    "I have a headache and feel dizzy",
                    "I've had a persistent cough for a week",
                    "I'm experiencing chest pain when breathing deeply"
                ],
                retry_btn=None,
                undo_btn=None,
            )

        # Medication Information Tab
        with gr.Tab("Medication Information"):
            gr.Markdown("Ask about medications, their usage, side effects, and interactions.")
            medication_interface = gr.ChatInterface(
                fn=medication_chat,
                examples=[
                    "What is ibuprofen used for?",
                    "What are the side effects of metformin?",
                    "Can I take aspirin with blood pressure medication?"
                ],
                retry_btn=None,
                undo_btn=None,
            )

        # Medical Records Tab
        with gr.Tab("Records Analysis"):
            gr.Markdown("Paste medical record text or lab results for analysis.")
            records_interface = gr.ChatInterface(
                fn=records_chat,
                examples=[
                    "What does a hemoglobin level of 10.5 g/dL mean?",
                    "Explain this diagnosis: Type 2 Diabetes Mellitus",
                    "What is a normal blood pressure reading?"
                ],
                retry_btn=None,
                undo_btn=None,
            )

    gr.Markdown(
        """
        ---
        *Built with Gradio, ChromaDB, and RAG technology*
        """
    )


if __name__ == "__main__":
    app.launch()
