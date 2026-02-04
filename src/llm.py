import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Lazy client initialization (deferred until first API call)
_client = None


class APIKeyMissingError(Exception):
    """Raised when DeepSeek API key is not configured."""
    pass


class APICallError(Exception):
    """Raised when API call fails."""
    pass


def _get_provider() -> str:
    """
    Detect which LLM provider to use based on environment variables.
    Prefers OpenAI if configured, falls back to DeepSeek.
    """
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    elif os.getenv("DEEPSEEK_API_KEY"):
        return "deepseek"
    return "none"


def get_provider() -> str:
    """Get the current LLM provider name."""
    return _get_provider()


def get_default_model() -> str:
    """Get the default model for the current provider."""
    provider = _get_provider()
    if provider == "openai":
        return os.getenv("OPENAI_MODEL", "gpt-5.2-2025-12-11")
    return os.getenv("DEEPSEEK_MODEL", "deepseek-chat")


def _get_client():
    """Get or initialize the OpenAI-compatible client (lazy loading)."""
    global _client
    if _client is None:
        provider = _get_provider()

        if provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise APIKeyMissingError(
                    "OPENAI_API_KEY is set but empty. Please provide a valid API key.\n"
                    "Get your key at: https://platform.openai.com/"
                )
            base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
            _client = OpenAI(api_key=api_key, base_url=base_url)
        elif provider == "deepseek":
            api_key = os.getenv("DEEPSEEK_API_KEY")
            if not api_key:
                raise APIKeyMissingError(
                    "DEEPSEEK_API_KEY is set but empty. Please provide a valid API key.\n"
                    "Get your key at: https://platform.deepseek.com/"
                )
            base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
            _client = OpenAI(api_key=api_key, base_url=base_url)
        else:
            raise APIKeyMissingError(
                "No LLM API key found. Please set OPENAI_API_KEY or DEEPSEEK_API_KEY in your .env file.\n"
                "1. Copy .env.example to .env\n"
                "2. Add your API key: OPENAI_API_KEY=your_key or DEEPSEEK_API_KEY=your_key\n"
                "3. Get keys at: https://platform.openai.com/ or https://platform.deepseek.com/"
            )
    return _client


def get_llm_client():
    """
    Public API to get the LLM client.
    Use this instead of _get_client() for external modules.
    """
    return _get_client()


def is_api_configured() -> bool:
    """Check if any API key is configured (without initializing client)."""
    return bool(os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY"))


def get_response(messages: list, model: str = None) -> str:
    """
    Send messages to LLM API and get response.

    Args:
        messages: List of message dicts with 'role' and 'content'
        model: Model name to use (defaults to provider's default model)

    Returns:
        Response content string

    Raises:
        APIKeyMissingError: If API key is not configured
        APICallError: If API call fails
    """
    if model is None:
        model = get_default_model()
    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=model,
            messages=messages
        )
        return response.choices[0].message.content
    except APIKeyMissingError:
        raise
    except Exception as e:
        raise APICallError(f"API call failed: {str(e)}")


def translate_to_english(text: str) -> str:
    """
    Translate non-English text to English for better retrieval.

    The knowledge base and embedding model are optimized for English,
    so translating queries improves retrieval quality.

    Args:
        text: Input text (potentially in any language)

    Returns:
        English translation, or original text if already English
    """
    # Check if text contains Chinese characters
    if not any('\u4e00' <= char <= '\u9fff' for char in text):
        return text  # No Chinese characters, assume English

    try:
        messages = [
            {
                "role": "system",
                "content": "You are a medical translator. Translate the following to English. Only output the translation, nothing else."
            },
            {"role": "user", "content": text}
        ]
        translated = get_response(messages)
        print(f"[INFO] Translated query: '{text}' -> '{translated}'")
        return translated
    except Exception as e:
        print(f"[WARN] Translation failed, using original query: {e}")
        return text


def rewrite_query_with_context(user_message: str, history: list, max_history: int = 4) -> str:
    """
    Rewrite user query with conversation context for better RAG retrieval.

    When users ask follow-up questions like "那发烧呢？" (what about fever?),
    this function rewrites the query to include relevant context from history,
    producing queries like "腰腿酸痛伴随发烧" (back/leg pain with fever).

    Args:
        user_message: Current user message
        history: Conversation history (list of {role, content} dicts)
        max_history: Max recent messages to consider (default 4 = 2 turns)

    Returns:
        Rewritten query optimized for retrieval
    """
    # If no history or message is already detailed, return as-is
    if not history or len(user_message) > 50:
        return user_message

    # Take only recent history to save tokens
    recent_history = history[-max_history:] if len(history) > max_history else history

    # Build context summary
    history_text = "\n".join([
        f"{'用户' if msg['role'] == 'user' else '助手'}: {msg['content'][:200]}"
        for msg in recent_history
    ])

    prompt = f"""Based on this conversation:
{history_text}

The user now asks: "{user_message}"

Rewrite this as a standalone search query that captures the full context.
- If it's a follow-up question, include the relevant topic from history
- Keep it concise (under 50 words)
- Output ONLY the rewritten query, nothing else

Rewritten query:"""

    try:
        messages = [{"role": "user", "content": prompt}]
        rewritten = get_response(messages)
        rewritten = rewritten.strip().strip('"').strip("'")
        return rewritten
    except Exception as e:
        print(f"[WARN] Query rewrite failed: {e}")
        return user_message


def build_messages(system_prompt: str, user_message: str, context: str = "", history: list = None) -> list:
    """
    Build message list for API call with conversation history.

    Args:
        system_prompt: System instruction
        user_message: User's question
        context: Retrieved context from RAG
        history: Conversation history (optional)

    Returns:
        List of message dicts
    """
    messages = [{"role": "system", "content": system_prompt}]

    # Add conversation history if provided
    if history:
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})

    if context:
        full_message = f"### Reference Information:\n{context}\n\n### Question:\n{user_message}"
    else:
        full_message = user_message

    messages.append({"role": "user", "content": full_message})
    return messages
