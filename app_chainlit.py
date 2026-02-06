"""
MedBot - Chainlit Interface
A modern chat UI for the medical assistant.
"""
import asyncio
import chainlit as cl
from src.retriever import retrieve_with_fallback, format_context, distance_to_relevance
from src.llm import get_response, get_response_stream, build_messages, is_api_configured, APIKeyMissingError, APICallError, rewrite_query_with_context
from src.prompts import get_prompt
from src.config import DEFAULT_TOP_K, ENABLE_CONTEXT_AWARE_RETRIEVAL
from src.embeddings import get_model
from src.search_agent import MedicalSearchAgent
from src.clinic_search import get_clinic_agent

# Initialize search agents
search_agent = MedicalSearchAgent()
clinic_agent = get_clinic_agent()

# =============================================================================
# Translations
# =============================================================================
TRANSLATIONS = {
    "en": {
        # Profile names and descriptions
        "symptom_name": "Symptom Analysis",
        "symptom_desc": "**Describe your symptoms** and get relevant medical information.\n\nPowered by 56,000+ medical Q&A pairs from NIH.",
        "medication_name": "Medication Info",
        "medication_desc": "**Ask about medications**, dosages, side effects, and drug interactions.\n\nData from FDA drug labels.",
        "doctor_name": "Find Doctor",
        "doctor_desc": "**Find specialists and clinics** in Singapore.\n\nSearch by specialty, name, or symptoms.",
        "clinic_name": "Find Clinic",
        "clinic_desc": "**Find nearby clinics** in Singapore.\n\nSearch by postal code or area name.",

        # Symptom starters
        "starter_headache": "Headache & Dizziness",
        "starter_headache_msg": "I have a headache and feel dizzy. What could be causing this?",
        "starter_cough": "Persistent Cough",
        "starter_cough_msg": "I've had a persistent cough for over a week with chest tightness. Should I be concerned?",
        "starter_fatigue": "Fatigue & Weakness",
        "starter_fatigue_msg": "I'm experiencing constant fatigue and shortness of breath. What might be wrong?",
        "starter_stomach": "Stomach Issues",
        "starter_stomach_msg": "I have stomach pain and nausea after eating. What conditions could cause this?",

        # Medication starters
        "starter_ibuprofen": "What is Ibuprofen?",
        "starter_ibuprofen_msg": "What is ibuprofen used for and what are its common side effects?",
        "starter_metformin": "Metformin Side Effects",
        "starter_metformin_msg": "What are the side effects of metformin for diabetes?",
        "starter_interactions": "Drug Interactions",
        "starter_interactions_msg": "Can I take aspirin with blood pressure medication? Are there any interactions?",
        "starter_painrelief": "Pain Relief Options",
        "starter_painrelief_msg": "What are the differences between acetaminophen and ibuprofen for pain relief?",

        # UI messages
        "welcome_title": "Welcome to MedBot",
        "status": "Status",
        "online": "Online",
        "api_required": "API Key Required",
        "ready_help": "I'm ready to help you with {feature}. You can:",
        "click_prompt": "Click one of the suggested prompts above",
        "type_question": "Or type your own question below",
        "tip": "Tip",
        "switch_modes": "Switch modes using the profile selector in the top-left corner.",
        "disclaimer": "Disclaimer",
        "disclaimer_text": "This is an AI assistant for informational purposes only. Always consult a healthcare professional for medical advice.",

        # Processing messages
        "searching": "Searching {feature} knowledge base...",
        "found_docs": "Found **{count}** relevant documents",
        "generating": "Generating response...",
        "sources_used": "Sources used:",

        # Help
        "help_title": "Help",
        "help_usage": "How to use MedBot:",
        "help_step1": "**Select a mode** using the profile selector (top-left corner):",
        "help_step2": "**Ask your question** or click a suggested prompt",
        "help_step3": "**Review the response** with cited sources",
        "help_tips": "Tips for better results:",
        "help_tip1": "Be specific about your symptoms or questions",
        "help_tip2": "Include relevant details (duration, severity, etc.)",
        "help_tip3": "One topic at a time works best",

        # Errors
        "error_api_title": "API Key Required",
        "error_api_text": "To use MedBot, please configure your DeepSeek API key:",
        "error_connection": "Connection Error",
        "error_connection_text": "Failed to connect to the AI service.",
        "error_generic": "Error",
        "error_generic_text": "Something went wrong: {error}",

        # Settings
        "settings_language": "Language",
    },
}

# Feature configurations
FEATURES = {
    "symptoms": {
        "collection": "medquad_symptoms",
        "icon": "🩺",
        "name_key": "symptom_name"
    },
    "medication": {
        "collection": "fda_drugs",
        "icon": "💊",
        "name_key": "medication_name"
    },
    "doctors": {
        "icon": "👨‍⚕️",
        "name_key": "doctor_name"
    },
    "clinics": {
        "icon": "🏥",
        "name_key": "clinic_name"
    }
}

# Profile to feature mapping
PROFILE_TO_FEATURE = {
    "Symptom Analysis": "symptoms",
    "Medication Info": "medication",
    "Find Doctor": "doctors",
    "Find Clinic": "clinics"
}

def t(key: str, lang: str = "en", **kwargs) -> str:
    """Get translation for a key."""
    text = TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)
    if kwargs:
        text = text.format(**kwargs)
    return text


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

    confidence = results.get("confidence_score", results.get("confidence", 0))
    confidence_pct = int(confidence * 100)

    # Confidence indicator with color hint
    if confidence_pct >= 70:
        conf_indicator = "🟢"
    elif confidence_pct >= 50:
        conf_indicator = "🟡"
    else:
        conf_indicator = "🔴"

    lines = ["", "---", f"*References* {conf_indicator} confidence {confidence_pct}%", ""]

    # Low confidence warning
    if confidence_pct < 50:
        lines.append("> Note: Low retrieval confidence. Consider adding more details or verifying with a professional.")
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
    """Get English starters for a profile."""
    if profile == "symptoms":
        return [
            cl.Starter(
                label="Headache & Dizziness",
                message="I have a headache and feel dizzy. What could be causing this?",
                icon="https://api.iconify.design/mdi:head-flash.svg?color=%23f59e0b",
            ),
            cl.Starter(
                label="Persistent Cough",
                message="I've had a persistent cough for over a week with chest tightness.",
                icon="https://api.iconify.design/mdi:lungs.svg?color=%2310b981",
            ),
            cl.Starter(
                label="Fatigue & Shortness of Breath",
                message="I'm experiencing constant fatigue and shortness of breath.",
                icon="https://api.iconify.design/mdi:sleep.svg?color=%238b5cf6",
            ),
            cl.Starter(
                label="Stomach Pain After Eating",
                message="I have stomach pain and nausea after eating.",
                icon="https://api.iconify.design/mdi:stomach.svg?color=%23ef4444",
            ),
        ]
    elif profile == "medication":
        return [
            cl.Starter(
                label="Ibuprofen",
                message="What is ibuprofen used for and what are its side effects?",
                icon="https://api.iconify.design/mdi:pill.svg?color=%23f59e0b",
            ),
            cl.Starter(
                label="Metformin",
                message="What are the side effects of metformin?",
                icon="https://api.iconify.design/mdi:alert-circle.svg?color=%23ef4444",
            ),
            cl.Starter(
                label="Drug Interactions",
                message="Can I take aspirin with blood pressure medication?",
                icon="https://api.iconify.design/mdi:swap-horizontal.svg?color=%238b5cf6",
            ),
            cl.Starter(
                label="Pain Relief Options",
                message="What are the differences between acetaminophen and ibuprofen?",
                icon="https://api.iconify.design/mdi:medical-bag.svg?color=%2310b981",
            ),
        ]
    elif profile == "doctors":
        return [
            cl.Starter(
                label="Dentist (English-speaking)",
                message="I need an English-speaking dentist.",
                icon="https://api.iconify.design/mdi:tooth-outline.svg?color=%2310b981",
            ),
            cl.Starter(
                label="Heart Specialist",
                message="Find a heart specialist.",
                icon="https://api.iconify.design/mdi:heart-pulse.svg?color=%23ef4444",
            ),
            cl.Starter(
                label="Fracture",
                message="I had a bone fracture. Who should I see?",
                icon="https://api.iconify.design/mdi:bone.svg?color=%23f59e0b",
            ),
            cl.Starter(
                label="Search Doctor by Name",
                message="Search for Dr. Tan.",
                icon="https://api.iconify.design/mdi:account-search.svg?color=%238b5cf6",
            ),
        ]
    elif profile == "clinics":
        return [
            cl.Starter(
                label="Search by Postal Code",
                message="Find the clinic nearest to postal code 641652.",
                icon="https://api.iconify.design/mdi:map-marker.svg?color=%23ef4444",
            ),
            cl.Starter(
                label="Tampines",
                message="What clinics are near Tampines?",
                icon="https://api.iconify.design/mdi:hospital-building.svg?color=%233b82f6",
            ),
            cl.Starter(
                label="Bedok",
                message="Nearest clinic in Bedok area.",
                icon="https://api.iconify.design/mdi:map-search.svg?color=%2310b981",
            ),
            cl.Starter(
                label="Jurong West",
                message="Clinics in Jurong West.",
                icon="https://api.iconify.design/mdi:city.svg?color=%23f59e0b",
            ),
        ]


@cl.set_chat_profiles
async def chat_profile():
    """Define chat profiles for different medical consultation modes."""
    return [
        cl.ChatProfile(
            name="Symptom Analysis",
            markdown_description="Describe your symptoms and get relevant medical information.",
            icon="https://api.iconify.design/mdi:hospital-box.svg?color=%23ec4899",
            starters=get_starters("symptoms"),
        ),
        cl.ChatProfile(
            name="Medication Info",
            markdown_description="Ask about medications, dosages, side effects, and interactions.",
            icon="https://api.iconify.design/mdi:pill.svg?color=%233b82f6",
            starters=get_starters("medication"),
        ),
        cl.ChatProfile(
            name="Find Doctor",
            markdown_description="Find specialists and clinics in Singapore.",
            icon="https://api.iconify.design/mdi:doctor.svg?color=%23f59e0b",
            starters=get_starters("doctors"),
        ),
        cl.ChatProfile(
            name="Find Clinic",
            markdown_description="Find nearby clinics in Singapore by postal code or area.",
            icon="https://api.iconify.design/mdi:hospital-building.svg?color=%2322c55e",
            starters=get_starters("clinics"),
        ),
    ]


@cl.on_chat_start
async def start():
    """Initialize the chat session."""
    cl.user_session.set("language", "en")

    # Get the selected chat profile
    chat_profile = cl.user_session.get("chat_profile")

    feature = PROFILE_TO_FEATURE.get(chat_profile, "symptoms")
    cl.user_session.set("feature", feature)

    # Check API status
    api_ok = is_api_configured()
    feature_info = FEATURES[feature]

    # Welcome message
    await cl.Message(
        content=f"""## {feature_info['icon']} MedBot

Type your question and I'll respond in English.

---

Tip: Switch modes using the profile selector in the top-left corner.

Disclaimer: For informational purposes only. Consult a healthcare professional for medical advice.
""",
        author="MedBot"
    ).send()


@cl.on_settings_update
async def on_settings_update(settings):
    """Handle settings updates (language change)."""
    cl.user_session.set("language", "en")


@cl.on_message
async def main(message: cl.Message):
    """Handle incoming messages."""
    user_input = message.content.strip()
    lang = "en"

    # Handle help command
    if user_input.lower() in ["/help", "/h"]:
        await cl.Message(
            content=f"""## 📖 {t('help_title', lang)}

**{t('help_usage', lang)}**

1. {t('help_step1', lang)}
   - 🩺 {t('symptom_name', lang)}
   - 💊 {t('medication_name', lang)}

2. {t('help_step2', lang)}

3. {t('help_step3', lang)}

**{t('help_tips', lang)}**
- {t('help_tip1', lang)}
- {t('help_tip2', lang)}
- {t('help_tip3', lang)}

---

⚠️ **{t('disclaimer', lang)}:** {t('disclaimer_text', lang)}
""",
            author="MedBot"
        ).send()
        return

    # Handle language switch command
    if user_input.lower() in ["/en", "/english"]:
        cl.user_session.set("language", "en")
        await cl.Message(content="🌐 Switched to English mode", author="MedBot").send()
        return

    # Get current feature from chat profile
    chat_profile = cl.user_session.get("chat_profile")
    feature = PROFILE_TO_FEATURE.get(chat_profile, "symptoms")
    feature_config = FEATURES[feature]
    feature_name = t(feature_config["name_key"], lang)

    # Show processing message
    msg = cl.Message(content="", author="MedBot")
    await msg.send()
    # Chainlit UI may not render an empty message bubble until it receives at least
    # one streamed chunk. Prime the stream with a single whitespace token so the
    # built-in typing indicator (blinking dots) shows up immediately.
    await msg.stream_token(" ")

    try:
        # Special logic for doctor search
        if feature == "doctors":
            # Use make_async for blocking search call
            response = await cl.make_async(search_agent.search)(user_input)
            msg.content = response
            await msg.update()
            return

        # Special logic for clinic search
        if feature == "clinics":
            # Use make_async for blocking search call
            results, plan = await cl.make_async(clinic_agent.search)(user_input)
            response = clinic_agent.format_results(results, plan)

            msg.content = response
            await msg.update()
            return

        # Get conversation history for context-aware retrieval
        history = cl.user_session.get("conversation_history", [])

        # Step 1: Context-aware query rewriting for better follow-up handling
        collection_name = feature_config["collection"]
        search_query = user_input

        if ENABLE_CONTEXT_AWARE_RETRIEVAL and history:
            search_query = await cl.make_async(rewrite_query_with_context)(user_input, history)
            if search_query != user_input:
                print(f"[Context] Original: {user_input}")
                print(f"[Context] Rewritten: {search_query}")

        # Step 2: Retrieve relevant documents with confidence scoring
        results = await cl.make_async(retrieve_with_fallback)(search_query, collection_name, top_k=DEFAULT_TOP_K)
        context = format_context(results)

        # Step 3: Stream LLM response token-by-token
        system_prompt = get_prompt(feature)
        messages = build_messages(system_prompt, user_input, context, history)

        response = ""
        # Bound the queue to avoid unbounded growth under UI/network backpressure.
        queue: asyncio.Queue = asyncio.Queue(maxsize=256)
        loop = asyncio.get_running_loop()

        def _produce_chunks():
            try:
                for token in get_response_stream(messages):
                    # Apply backpressure if the consumer is slower than the producer.
                    asyncio.run_coroutine_threadsafe(queue.put(token), loop).result()
            finally:
                asyncio.run_coroutine_threadsafe(queue.put(None), loop).result()

        fut = loop.run_in_executor(None, _produce_chunks)
        while True:
            token = await queue.get()
            if token is None:
                break
            await msg.stream_token(token)
            response += token
        await fut  # propagate any exception from the thread

        # Update conversation history (store original question without RAG context)
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": response})

        # Limit history length to avoid token overflow (keep last 10 turns = 20 messages)
        MAX_HISTORY_TURNS = 10
        if len(history) > MAX_HISTORY_TURNS * 2:
            history = history[-(MAX_HISTORY_TURNS * 2):]

        cl.user_session.set("conversation_history", history)

        # Add confidence warning for low-quality retrievals
        confidence_level = results.get("confidence_level", "medium")
        if confidence_level in ["low", "very_low", "none"]:
            # Render as a subtle callout (smaller/less prominent than bold text).
            warning = "\n\n> ⚠️ Note: Limited information available in the knowledge base. Please verify with a healthcare professional."
            response += warning

        # Add retrieval visualization (shows what documents were used)
        retrieval_info = format_retrieval_display(results)
        if retrieval_info:
            response += retrieval_info

        # Update with final response (includes any appended warnings/retrieval info)
        msg.content = response
        await msg.update()

    except APIKeyMissingError:
        msg.content = f"""## ⚠️ {t('error_api_title', lang)}

{t('error_api_text', lang)}

1. Create a `.env` file in the project root
2. Add: `DEEPSEEK_API_KEY=your_key_here`
3. Get your key at [platform.deepseek.com](https://platform.deepseek.com/)
4. Restart the application
"""
        await msg.update()

    except APICallError as e:
        msg.content = f"""## ⚠️ {t('error_connection', lang)}

{t('error_connection_text', lang)}

**Error:** {str(e)}
"""
        await msg.update()

    except Exception as e:
        msg.content = f"""## ⚠️ {t('error_generic', lang)}

{t('error_generic_text', lang, error=str(e))}
"""
        await msg.update()


# Run with: chainlit run app_chainlit.py
