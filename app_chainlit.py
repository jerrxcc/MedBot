"""
MedBot - Chainlit Interface (Bilingual: English/Chinese)
A modern chat UI for the medical assistant.
"""
import chainlit as cl
from src.retriever import retrieve, format_context
from src.llm import get_response, build_messages, is_api_configured, APIKeyMissingError, APICallError
from src.prompts import get_prompt

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
        "records_name": "Records Analysis",
        "records_desc": "**Understand medical reports**, lab results, and diagnoses.\n\nGet explanations in plain language.",

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

        # Records starters
        "starter_hemoglobin": "Hemoglobin Levels",
        "starter_hemoglobin_msg": "What does a hemoglobin level of 10.5 g/dL mean? Is this normal?",
        "starter_bp": "Blood Pressure Reading",
        "starter_bp_msg": "What is considered a normal blood pressure reading? What do the numbers mean?",
        "starter_diabetes": "Diabetes Diagnosis",
        "starter_diabetes_msg": "Explain Type 2 Diabetes Mellitus diagnosis. What does it mean for daily life?",
        "starter_cholesterol": "Cholesterol Report",
        "starter_cholesterol_msg": "How do I interpret my cholesterol test results? What are healthy levels?",

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
    "zh": {
        # Profile names and descriptions
        "symptom_name": "症状分析",
        "symptom_desc": "**描述您的症状**，获取相关医学信息。\n\n基于 NIH 的 56,000+ 医学问答对。",
        "medication_name": "药物信息",
        "medication_desc": "**查询药物**用法、副作用和药物相互作用。\n\n数据来源：FDA 药品标签。",
        "records_name": "病历解读",
        "records_desc": "**理解医疗报告**、化验结果和诊断。\n\n用通俗语言解释医学术语。",

        # Symptom starters
        "starter_headache": "头痛头晕",
        "starter_headache_msg": "我头痛并且感到头晕，可能是什么原因？",
        "starter_cough": "持续咳嗽",
        "starter_cough_msg": "我咳嗽超过一周了，还有胸闷。需要担心吗？",
        "starter_fatigue": "疲劳乏力",
        "starter_fatigue_msg": "我经常感到疲劳和气短，可能是什么问题？",
        "starter_stomach": "胃部不适",
        "starter_stomach_msg": "我吃完饭后胃痛和恶心，可能是什么病症？",

        # Medication starters
        "starter_ibuprofen": "布洛芬是什么？",
        "starter_ibuprofen_msg": "布洛芬的用途是什么？有哪些常见副作用？",
        "starter_metformin": "二甲双胍副作用",
        "starter_metformin_msg": "治疗糖尿病的二甲双胍有什么副作用？",
        "starter_interactions": "药物相互作用",
        "starter_interactions_msg": "阿司匹林可以和降压药一起吃吗？有相互作用吗？",
        "starter_painrelief": "止痛药对比",
        "starter_painrelief_msg": "对乙酰氨基酚和布洛芬在止痛方面有什么区别？",

        # Records starters
        "starter_hemoglobin": "血红蛋白水平",
        "starter_hemoglobin_msg": "血红蛋白 10.5 g/dL 是什么意思？正常吗？",
        "starter_bp": "血压读数",
        "starter_bp_msg": "正常血压是多少？这些数字代表什么？",
        "starter_diabetes": "糖尿病诊断",
        "starter_diabetes_msg": "请解释 2 型糖尿病诊断，对日常生活有什么影响？",
        "starter_cholesterol": "胆固醇报告",
        "starter_cholesterol_msg": "如何解读胆固醇检测结果？健康水平是多少？",

        # UI messages
        "welcome_title": "欢迎使用 MedBot",
        "status": "状态",
        "online": "在线",
        "api_required": "需要 API 密钥",
        "ready_help": "我已准备好为您提供{feature}服务。您可以：",
        "click_prompt": "点击上方的建议提示",
        "type_question": "或在下方输入您的问题",
        "tip": "提示",
        "switch_modes": "使用左上角的选择器切换功能模式。",
        "disclaimer": "免责声明",
        "disclaimer_text": "本 AI 助手仅供参考。如有健康问题，请咨询专业医疗人员。",

        # Processing messages
        "searching": "正在搜索{feature}知识库...",
        "found_docs": "找到 **{count}** 条相关文档",
        "generating": "正在生成回复...",
        "sources_used": "参考来源：",

        # Help
        "help_title": "帮助",
        "help_usage": "如何使用 MedBot：",
        "help_step1": "**选择模式** - 使用左上角的选择器：",
        "help_step2": "**提问** - 点击建议提示或输入问题",
        "help_step3": "**查看回复** - 包含引用来源",
        "help_tips": "获得更好结果的技巧：",
        "help_tip1": "具体描述您的症状或问题",
        "help_tip2": "包含相关细节（持续时间、严重程度等）",
        "help_tip3": "一次询问一个主题效果最佳",

        # Errors
        "error_api_title": "需要 API 密钥",
        "error_api_text": "要使用 MedBot，请配置您的 DeepSeek API 密钥：",
        "error_connection": "连接错误",
        "error_connection_text": "无法连接到 AI 服务。",
        "error_generic": "错误",
        "error_generic_text": "出现问题：{error}",

        # Settings
        "settings_language": "语言 Language",
    }
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
    "records": {
        "collection": "medical_records",
        "icon": "📋",
        "name_key": "records_name"
    }
}


def t(key: str, lang: str = "en", **kwargs) -> str:
    """Get translation for a key."""
    text = TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)
    if kwargs:
        text = text.format(**kwargs)
    return text


def get_bilingual_starters(profile: str):
    """Get bilingual starters for a profile."""
    if profile == "symptoms":
        return [
            cl.Starter(
                label="头痛头晕 Headache",
                message="我头痛并且感到头晕，可能是什么原因？/ I have a headache and feel dizzy. What could be causing this?",
                icon="https://api.iconify.design/mdi:head-flash.svg?color=%23f59e0b",
            ),
            cl.Starter(
                label="咳嗽 Cough",
                message="我咳嗽超过一周了，还有胸闷。/ I've had a persistent cough for over a week with chest tightness.",
                icon="https://api.iconify.design/mdi:lungs.svg?color=%2310b981",
            ),
            cl.Starter(
                label="疲劳 Fatigue",
                message="我经常感到疲劳和气短。/ I'm experiencing constant fatigue and shortness of breath.",
                icon="https://api.iconify.design/mdi:sleep.svg?color=%238b5cf6",
            ),
            cl.Starter(
                label="胃痛 Stomach",
                message="我吃完饭后胃痛和恶心。/ I have stomach pain and nausea after eating.",
                icon="https://api.iconify.design/mdi:stomach.svg?color=%23ef4444",
            ),
        ]
    elif profile == "medication":
        return [
            cl.Starter(
                label="布洛芬 Ibuprofen",
                message="布洛芬的用途和副作用？/ What is ibuprofen used for and what are its side effects?",
                icon="https://api.iconify.design/mdi:pill.svg?color=%23f59e0b",
            ),
            cl.Starter(
                label="二甲双胍 Metformin",
                message="二甲双胍有什么副作用？/ What are the side effects of metformin?",
                icon="https://api.iconify.design/mdi:alert-circle.svg?color=%23ef4444",
            ),
            cl.Starter(
                label="药物相互作用 Interactions",
                message="阿司匹林可以和降压药一起吃吗？/ Can I take aspirin with blood pressure medication?",
                icon="https://api.iconify.design/mdi:swap-horizontal.svg?color=%238b5cf6",
            ),
            cl.Starter(
                label="止痛药 Pain Relief",
                message="对乙酰氨基酚和布洛芬有什么区别？/ What are the differences between acetaminophen and ibuprofen?",
                icon="https://api.iconify.design/mdi:medical-bag.svg?color=%2310b981",
            ),
        ]
    else:  # records
        return [
            cl.Starter(
                label="血红蛋白 Hemoglobin",
                message="血红蛋白 10.5 g/dL 正常吗？/ What does a hemoglobin level of 10.5 g/dL mean?",
                icon="https://api.iconify.design/mdi:water.svg?color=%23ef4444",
            ),
            cl.Starter(
                label="血压 Blood Pressure",
                message="正常血压是多少？/ What is considered a normal blood pressure reading?",
                icon="https://api.iconify.design/mdi:heart-pulse.svg?color=%23ec4899",
            ),
            cl.Starter(
                label="糖尿病 Diabetes",
                message="请解释 2 型糖尿病诊断。/ Explain Type 2 Diabetes Mellitus diagnosis.",
                icon="https://api.iconify.design/mdi:diabetes.svg?color=%23f59e0b",
            ),
            cl.Starter(
                label="胆固醇 Cholesterol",
                message="如何解读胆固醇检测结果？/ How do I interpret my cholesterol test results?",
                icon="https://api.iconify.design/mdi:chart-line.svg?color=%233b82f6",
            ),
        ]


@cl.set_chat_profiles
async def chat_profile():
    """Define chat profiles for different medical consultation modes."""
    return [
        cl.ChatProfile(
            name="Symptom Analysis",
            markdown_description="**症状分析 Symptom Analysis**\n\n描述您的症状，获取医学信息。\nDescribe symptoms and get medical information.",
            icon="https://api.iconify.design/mdi:stethoscope.svg?color=%23ec4899",
            starters=get_bilingual_starters("symptoms"),
        ),
        cl.ChatProfile(
            name="Medication Info",
            markdown_description="**药物信息 Medication Info**\n\n查询药物用法和副作用。\nQuery drug usage and side effects.",
            icon="https://api.iconify.design/mdi:pill.svg?color=%233b82f6",
            starters=get_bilingual_starters("medication"),
        ),
        cl.ChatProfile(
            name="Records Analysis",
            markdown_description="**病历解读 Records Analysis**\n\n理解医疗报告和化验结果。\nUnderstand medical reports and lab results.",
            icon="https://api.iconify.design/mdi:file-document.svg?color=%2310b981",
            starters=get_bilingual_starters("records"),
        ),
    ]


def detect_language_from_text(text: str) -> str:
    """Detect if text is primarily Chinese or English."""
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    return "zh" if chinese_chars > len(text) * 0.3 else "en"


@cl.on_chat_start
async def start():
    """Initialize the chat session."""
    # Default language - will be auto-detected from first message
    # or user can switch via /zh or /en
    lang = "en"
    cl.user_session.set("language", lang)
    cl.user_session.set("language_detected", False)

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

    # Check API status
    api_ok = is_api_configured()
    feature_info = FEATURES[feature]

    # Bilingual welcome message
    await cl.Message(
        content=f"""## {feature_info['icon']} MedBot

**English:** Type your question in English and I'll respond in English.
**中文:** 用中文提问，我会用中文回复。

---

💡 **Tip / 提示:** Type `/en` for English | 输入 `/zh` 切换中文

⚠️ **Disclaimer / 免责声明:** For informational purposes only. 仅供参考，如有健康问题请咨询医生。
""",
        author="MedBot"
    ).send()


@cl.on_settings_update
async def on_settings_update(settings):
    """Handle settings updates (language change)."""
    lang_setting = settings.get("Language", "English")
    lang = "zh" if lang_setting == "中文" else "en"
    cl.user_session.set("language", lang)

    # Notify user of language change
    if lang == "zh":
        await cl.Message(content="🌐 已切换到中文模式", author="MedBot").send()
    else:
        await cl.Message(content="🌐 Switched to English mode", author="MedBot").send()


@cl.on_message
async def main(message: cl.Message):
    """Handle incoming messages."""
    user_input = message.content.strip()
    lang = cl.user_session.get("language", "en")

    # Auto-detect language from first real message (not commands)
    if not cl.user_session.get("language_detected") and not user_input.startswith("/"):
        detected_lang = detect_language_from_text(user_input)
        cl.user_session.set("language", detected_lang)
        cl.user_session.set("language_detected", True)
        lang = detected_lang

    # Handle help command
    if user_input.lower() in ["/help", "/h", "/帮助"]:
        await cl.Message(
            content=f"""## 📖 {t('help_title', lang)}

**{t('help_usage', lang)}**

1. {t('help_step1', lang)}
   - 🩺 {t('symptom_name', lang)}
   - 💊 {t('medication_name', lang)}
   - 📋 {t('records_name', lang)}

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

    if user_input.lower() in ["/zh", "/中文", "/chinese"]:
        cl.user_session.set("language", "zh")
        await cl.Message(content="🌐 已切换到中文模式", author="MedBot").send()
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
    feature_name = t(feature_config["name_key"], lang)

    # Show processing message
    msg = cl.Message(content="", author="MedBot")
    await msg.send()

    try:
        # Step 1: Retrieve relevant documents
        await msg.stream_token(f"🔍 {t('searching', lang, feature=feature_name)}\n\n")

        collection_name = feature_config["collection"]
        results = retrieve(user_input, collection_name, top_k=5)
        context = format_context(results)

        num_docs = len(results.get("documents", []))
        await msg.stream_token(f"📚 {t('found_docs', lang, count=num_docs)}\n\n")
        await msg.stream_token(f"💭 {t('generating', lang)}\n\n---\n\n")

        # Step 2: Generate response
        system_prompt = get_prompt(feature)
        messages = build_messages(system_prompt, user_input, context)
        response = get_response(messages)

        # Update with final response
        msg.content = response
        await msg.update()

        # Add sources as elements
        if results.get("metadatas"):
            sources_text = f"**{t('sources_used', lang)}**\n"
            for i, meta in enumerate(results["metadatas"][:5], 1):
                source = meta.get("source", "Unknown")
                category = meta.get("category", "")
                if category:
                    sources_text += f"- [{i}] {source} ({category})\n"
                else:
                    sources_text += f"- [{i}] {source}\n"

            await cl.Message(
                content=sources_text,
                author="MedBot",
                parent_id=msg.id
            ).send()

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
