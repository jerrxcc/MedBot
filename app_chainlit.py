"""
MedBot - Chainlit Interface
A modern chat UI for the medical assistant.
"""
import chainlit as cl
from src.retriever import retrieve, format_context
from src.llm import get_response, build_messages, is_api_configured, APIKeyMissingError, APICallError
from src.prompts import get_prompt

# Feature configurations
FEATURES = {
    "symptoms": {
        "collection": "medquad_symptoms",
        "icon": "🩺",
        "name": "Symptom Analysis"
    },
    "medication": {
        "collection": "fda_drugs",
        "icon": "💊",
        "name": "Medication Info"
    },
    "records": {
        "collection": "medical_records",
        "icon": "📋",
        "name": "Records Analysis"
    }
}

# Default feature
DEFAULT_FEATURE = "symptoms"


@cl.on_chat_start
async def start():
    """Initialize the chat session."""
    # Set default feature
    cl.user_session.set("feature", DEFAULT_FEATURE)

    # Check API status
    api_status = "✅ Online" if is_api_configured() else "⚠️ API Key Required"

    # Send welcome message
    await cl.Message(
        content=f"""# 🏥 Welcome to MedBot

Your AI-powered medical information assistant.

**Current Status:** {api_status}

I can help you with:
- 🩺 **Symptom Analysis** - Describe your symptoms for information
- 💊 **Medication Info** - Ask about drugs, dosages, and interactions
- 📋 **Records Analysis** - Understand medical reports and lab results

---

**💡 Tips:**
- Type `/symptoms`, `/medication`, or `/records` to switch modes
- Be specific in your questions for better answers
- Always consult a healthcare professional for medical advice

**Current mode:** 🩺 Symptom Analysis

---
*Start typing your question below...*
""",
        author="MedBot"
    ).send()


@cl.on_message
async def main(message: cl.Message):
    """Handle incoming messages."""
    user_input = message.content.strip()

    # Handle mode switching commands
    if user_input.lower() in ["/symptoms", "/symptom"]:
        cl.user_session.set("feature", "symptoms")
        await cl.Message(
            content="🩺 **Switched to Symptom Analysis mode**\n\nDescribe your symptoms and I'll provide relevant medical information.",
            author="MedBot"
        ).send()
        return

    if user_input.lower() in ["/medication", "/med", "/drug"]:
        cl.user_session.set("feature", "medication")
        await cl.Message(
            content="💊 **Switched to Medication Info mode**\n\nAsk me about any medication, its usage, side effects, or interactions.",
            author="MedBot"
        ).send()
        return

    if user_input.lower() in ["/records", "/record", "/lab"]:
        cl.user_session.set("feature", "records")
        await cl.Message(
            content="📋 **Switched to Records Analysis mode**\n\nPaste or describe medical records, lab results, or diagnoses for explanation.",
            author="MedBot"
        ).send()
        return

    if user_input.lower() in ["/help", "/h"]:
        await cl.Message(
            content="""# 📖 Help

**Available Commands:**
- `/symptoms` - Switch to symptom analysis mode
- `/medication` - Switch to medication info mode
- `/records` - Switch to records analysis mode
- `/help` - Show this help message

**Tips for better results:**
1. Be specific about your symptoms or questions
2. Include relevant details (duration, severity, etc.)
3. One topic at a time works best

**Disclaimer:** This is an AI assistant for informational purposes only. Always consult a healthcare professional for medical advice.
""",
            author="MedBot"
        ).send()
        return

    # Get current feature
    feature = cl.user_session.get("feature", DEFAULT_FEATURE)
    feature_config = FEATURES[feature]

    # Show thinking indicator
    msg = cl.Message(content="", author="MedBot")
    await msg.send()

    try:
        # Step 1: Retrieve relevant documents
        await msg.stream_token("🔍 Searching knowledge base...\n\n")

        collection_name = feature_config["collection"]
        results = retrieve(user_input, collection_name, top_k=5)
        context = format_context(results)

        num_docs = len(results.get("documents", []))
        await msg.stream_token(f"📚 Found {num_docs} relevant documents\n\n")

        # Step 2: Generate response
        await msg.stream_token("💭 Generating response...\n\n---\n\n")

        system_prompt = get_prompt(feature)
        messages = build_messages(system_prompt, user_input, context)

        response = get_response(messages)

        # Clear the progress messages and show response
        msg.content = response
        await msg.update()

        # Add sources as a collapsible element
        if results.get("metadatas"):
            sources = []
            for i, meta in enumerate(results["metadatas"][:3], 1):
                source = meta.get("source", "Unknown")
                sources.append(f"{i}. {source}")

            if sources:
                elements = [
                    cl.Text(
                        name="Sources",
                        content="\n".join(sources),
                        display="side"
                    )
                ]
                msg.elements = elements
                await msg.update()

    except APIKeyMissingError:
        msg.content = """### ⚠️ API Key Required

To use MedBot, please configure your DeepSeek API key:

1. Create a `.env` file in the project root
2. Add: `DEEPSEEK_API_KEY=your_key_here`
3. Get your key at [platform.deepseek.com](https://platform.deepseek.com/)
4. Restart the application

---
*The knowledge base is ready with {num_docs} relevant documents.*
"""
        await msg.update()

    except APICallError as e:
        msg.content = f"""### ⚠️ Connection Error

Failed to connect to the AI service: {str(e)}

Please check your internet connection and try again.
"""
        await msg.update()

    except Exception as e:
        msg.content = f"""### ⚠️ Error

Something went wrong: {str(e)}

Please try again or rephrase your question.
"""
        await msg.update()


# Chainlit configuration
if __name__ == "__main__":
    from chainlit.cli import run_chainlit
    run_chainlit(__file__)
