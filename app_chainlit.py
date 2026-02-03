"""
MedBot - Chainlit Interface
A modern chat UI for the medical assistant.
"""
import chainlit as cl
from src.retriever import retrieve_with_fallback, format_context, distance_to_relevance
from src.llm import get_response, build_messages, is_api_configured, APIKeyMissingError, APICallError
from src.prompts import get_prompt
from src.config import DEFAULT_TOP_K
from src.embeddings import get_model

# Preload embedding model at startup for faster first response
print("[INFO] Preloading embedding model...")
get_model()
print("[INFO] Embedding model ready!")

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


def format_retrieval_display(results: dict) -> str:
    """
    Format retrieval results for user display.

    Shows the documents retrieved by RAG with relevance scores,
    helping users understand what information the AI based its answer on.

    Args:
        results: Dict from retrieve_with_fallback()

    Returns:
        Formatted markdown string for display
    """
    if not results.get("documents"):
        return ""

    confidence = results.get("confidence", 0)
    confidence_pct = int(confidence * 100)

    # Confidence indicator with color hint
    if confidence_pct >= 70:
        conf_indicator = "🟢"
    elif confidence_pct >= 50:
        conf_indicator = "🟡"
    else:
        conf_indicator = "🔴"

    lines = [
        "",
        "---",
        f"📚 **参考资料** {conf_indicator} 置信度 {confidence_pct}%",
        ""
    ]

    # Low confidence warning
    if confidence_pct < 50:
        lines.append("> ⚠️ 置信度较低，建议补充描述或咨询专业人士")
        lines.append("")

    documents = results.get("documents", [])
    metadatas = results.get("metadatas", [])
    distances = results.get("distances", [])

    # Only show top 3 most relevant documents for cleaner UI
    max_docs = 3
    for i, (doc, meta, dist) in enumerate(zip(documents[:max_docs], metadatas[:max_docs], distances[:max_docs]), 1):
        relevance = distance_to_relevance(dist)
        source = meta.get("source", "Unknown") if meta else "Unknown"
        condition = meta.get("condition", "") if meta else ""

        # Relevance indicator
        if relevance >= 60:
            rel_indicator = "🟢"
        elif relevance >= 40:
            rel_indicator = "🟡"
        else:
            rel_indicator = "🔴"

        # Create clean preview (first 100 characters)
        preview = doc[:100].replace("\n", " ").strip()
        if len(doc) > 100:
            preview += "..."

        # Topic line
        topic = f" · *{condition}*" if condition else ""

        lines.append(f"**{i}.** {rel_indicator} {relevance:.0f}% | {source}{topic}")
        lines.append(f"> {preview}")
        lines.append("")

    return "\n".join(lines)


def get_starters(profile: str):
    """Get starter prompts for a profile."""
    if profile == "symptoms":
        return [
            cl.Starter(
                label="Headache & Dizziness",
                message="I have a headache and feel dizzy. What could be causing this?",
                icon="https://api.iconify.design/mdi:head-flash.svg?color=%23f59e0b",
            ),
            cl.Starter(
                label="Persistent Cough",
                message="I've had a persistent cough for over a week with chest tightness. Should I be concerned?",
                icon="https://api.iconify.design/mdi:lungs.svg?color=%2310b981",
            ),
            cl.Starter(
                label="Fatigue & Weakness",
                message="I'm experiencing constant fatigue and shortness of breath. What might be wrong?",
                icon="https://api.iconify.design/mdi:sleep.svg?color=%238b5cf6",
            ),
            cl.Starter(
                label="Stomach Issues",
                message="I have stomach pain and nausea after eating. What conditions could cause this?",
                icon="https://api.iconify.design/mdi:stomach.svg?color=%23ef4444",
            ),
        ]
    elif profile == "medication":
        return [
            cl.Starter(
                label="What is Ibuprofen?",
                message="What is ibuprofen used for and what are its common side effects?",
                icon="https://api.iconify.design/mdi:pill.svg?color=%23f59e0b",
            ),
            cl.Starter(
                label="Metformin Side Effects",
                message="What are the side effects of metformin for diabetes?",
                icon="https://api.iconify.design/mdi:alert-circle.svg?color=%23ef4444",
            ),
            cl.Starter(
                label="Drug Interactions",
                message="Can I take aspirin with blood pressure medication? Are there any interactions?",
                icon="https://api.iconify.design/mdi:swap-horizontal.svg?color=%238b5cf6",
            ),
            cl.Starter(
                label="Pain Relief Options",
                message="What are the differences between acetaminophen and ibuprofen for pain relief?",
                icon="https://api.iconify.design/mdi:medical-bag.svg?color=%2310b981",
            ),
        ]
    else:  # records
        return [
            cl.Starter(
                label="Hemoglobin Levels",
                message="What does a hemoglobin level of 10.5 g/dL mean? Is this normal?",
                icon="https://api.iconify.design/mdi:water.svg?color=%23ef4444",
            ),
            cl.Starter(
                label="Blood Pressure Reading",
                message="What is considered a normal blood pressure reading? What do the numbers mean?",
                icon="https://api.iconify.design/mdi:heart-pulse.svg?color=%23ec4899",
            ),
            cl.Starter(
                label="Diabetes Diagnosis",
                message="Explain Type 2 Diabetes Mellitus diagnosis. What does it mean for daily life?",
                icon="https://api.iconify.design/mdi:diabetes.svg?color=%23f59e0b",
            ),
            cl.Starter(
                label="Cholesterol Report",
                message="How do I interpret my cholesterol test results? What are healthy levels?",
                icon="https://api.iconify.design/mdi:chart-line.svg?color=%233b82f6",
            ),
        ]


@cl.set_chat_profiles
async def chat_profile():
    """Define chat profiles for different medical consultation modes."""
    return [
        cl.ChatProfile(
            name="Symptom Analysis",
            markdown_description="**Describe your symptoms** and get relevant medical information.\n\nPowered by 35,000+ medical Q&A pairs from NIH.",
            icon="https://api.iconify.design/mdi:hospital-box.svg?color=%23ec4899",
            starters=get_starters("symptoms"),
        ),
        cl.ChatProfile(
            name="Medication Info",
            markdown_description="**Ask about medications**, dosages, side effects, and drug interactions.\n\nData from 1,800+ FDA drug labels.",
            icon="https://api.iconify.design/mdi:pill.svg?color=%233b82f6",
            starters=get_starters("medication"),
        ),
        cl.ChatProfile(
            name="Records Analysis",
            markdown_description="**Understand medical reports**, lab results, and diagnoses.\n\nGet explanations in plain language.",
            icon="https://api.iconify.design/mdi:file-document.svg?color=%2310b981",
            starters=get_starters("records"),
        ),
    ]


@cl.on_chat_start
async def start():
    """Initialize the chat session."""
    # Get the selected chat profile
    chat_profile = cl.user_session.get("chat_profile")

    # Map profile name to feature key
    profile_to_feature = {
        "Symptom Analysis": "symptoms",
        "Medication Info": "medication",
        "Records Analysis": "records"
    }

    feature = profile_to_feature.get(chat_profile, "symptoms")
    cl.user_session.set("feature", feature)
    feature_info = FEATURES[feature]

    # Initialize conversation history (cleared on new chat or profile switch)
    cl.user_session.set("conversation_history", [])

    # Welcome message
    await cl.Message(
        content=f"""## {feature_info['icon']} MedBot - {feature_info['name']}

Welcome! I'm here to help you with medical information.

- Click one of the **suggested prompts** above, or
- Type your own question below

---

**Disclaimer:** This is an AI assistant for informational purposes only. Always consult a healthcare professional for medical advice.
""",
        author="MedBot"
    ).send()


@cl.on_message
async def main(message: cl.Message):
    """Handle incoming messages."""
    user_input = message.content.strip()

    # Handle help command
    if user_input.lower() in ["/help", "/h"]:
        await cl.Message(
            content="""## Help

**How to use MedBot:**

1. **Select a mode** using the profile selector (top-left corner):
   - 🩺 Symptom Analysis
   - 💊 Medication Info
   - 📋 Records Analysis

2. **Ask your question** or click a suggested prompt

3. **Review the response** with cited sources

**Tips for better results:**
- Be specific about your symptoms or questions
- Include relevant details (duration, severity, etc.)
- One topic at a time works best

---

**Disclaimer:** This is an AI assistant for informational purposes only. Always consult a healthcare professional for medical advice.
""",
            author="MedBot"
        ).send()
        return

    # Get current feature from chat profile
    chat_profile = cl.user_session.get("chat_profile")
    profile_to_feature = {
        "Symptom Analysis": "symptoms",
        "Medication Info": "medication",
        "Records Analysis": "records"
    }
    feature = profile_to_feature.get(chat_profile, "symptoms")
    feature_config = FEATURES[feature]
    feature_name = feature_config["name"]

    # Show thinking indicator (GPT-style)
    msg = cl.Message(content="💭 *Thinking...*", author="MedBot")
    await msg.send()

    try:
        # Step 1: Retrieve relevant documents with confidence scoring
        collection_name = feature_config["collection"]
        results = retrieve_with_fallback(user_input, collection_name, top_k=DEFAULT_TOP_K)
        context = format_context(results)

        num_docs = len(results.get("documents", []))
        confidence_level = results.get("confidence_level", "none")
        fallback_used = results.get("fallback_used", False)

        # Update to show generation status
        msg.content = "✨ *Generating response...*"
        await msg.update()

        # Get conversation history
        history = cl.user_session.get("conversation_history", [])

        # Step 2: Generate response (with conversation history)
        system_prompt = get_prompt(feature)
        messages = build_messages(system_prompt, user_input, context, history)
        response = get_response(messages)

        # Update conversation history (store original question without RAG context)
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": response})

        # Limit history length to avoid token overflow (keep last 10 turns = 20 messages)
        MAX_HISTORY_TURNS = 10
        if len(history) > MAX_HISTORY_TURNS * 2:
            history = history[-(MAX_HISTORY_TURNS * 2):]

        cl.user_session.set("conversation_history", history)

        # Add confidence warning for low-quality retrievals
        if confidence_level in ["low", "very_low", "none"]:
            warning = "\n\n---\n⚠️ **Note:** Limited information available in knowledge base. Please verify with a healthcare professional."
            response = response + warning

        if fallback_used:
            response += "\n\n*Information gathered from multiple sources.*"

        # Add retrieval visualization (shows what documents were used)
        retrieval_info = format_retrieval_display(results)
        if retrieval_info:
            response += retrieval_info

        # Update with final response
        msg.content = response
        await msg.update()

    except APIKeyMissingError:
        msg.content = """## ⚠️ API Key Required

To use MedBot, please configure your DeepSeek API key:

1. Create a `.env` file in the project root
2. Add: `DEEPSEEK_API_KEY=your_key_here`
3. Get your key at [platform.deepseek.com](https://platform.deepseek.com/)
4. Restart the application
"""
        await msg.update()

    except APICallError as e:
        msg.content = f"""## ⚠️ Connection Error

Failed to connect to the AI service.

**Error:** {str(e)}
"""
        await msg.update()

    except Exception as e:
        msg.content = f"""## ⚠️ Error

Something went wrong: {str(e)}
"""
        await msg.update()


# Run with: chainlit run app_chainlit.py
