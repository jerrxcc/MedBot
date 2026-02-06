"""LLM client management and API utilities."""
import os
import re
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

_client = None

# Keywords indicating temperature parameter is not supported by the model
TEMPERATURE_ERROR_KEYWORDS = frozenset([
    "unsupported", "not supported", "not allowed",
    "invalid", "not valid", "does not support"
])


class APIKeyMissingError(Exception):
    """Raised when no API key is configured."""
    pass


class APICallError(Exception):
    """Raised when API call fails."""
    pass


def get_provider() -> str:
    """Get the current LLM provider based on environment variables."""
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    if os.getenv("DEEPSEEK_API_KEY"):
        return "deepseek"
    return "none"


def get_default_model() -> str:
    """Get the default model for the current provider."""
    provider = get_provider()
    if provider == "openai":
        return os.getenv("OPENAI_MODEL", "gpt-5.2-2025-12-11")
    return os.getenv("DEEPSEEK_MODEL", "deepseek-chat")


def get_llm_client() -> OpenAI:
    """Get or initialize the OpenAI-compatible client (lazy loading)."""
    global _client
    if _client is not None:
        return _client

    provider = get_provider()

    provider_configs = {
        "openai": {
            "key_var": "OPENAI_API_KEY",
            "base_url_var": "OPENAI_BASE_URL",
            "default_base_url": "https://api.openai.com/v1",
            "signup_url": "https://platform.openai.com/",
        },
        "deepseek": {
            "key_var": "DEEPSEEK_API_KEY",
            "base_url_var": "DEEPSEEK_BASE_URL",
            "default_base_url": "https://api.deepseek.com",
            "signup_url": "https://platform.deepseek.com/",
        },
    }

    if provider == "none":
        raise APIKeyMissingError(
            "No LLM API key found. Please set OPENAI_API_KEY or DEEPSEEK_API_KEY in your .env file.\n"
            "1. Copy .env.example to .env\n"
            "2. Add your API key: OPENAI_API_KEY=your_key or DEEPSEEK_API_KEY=your_key\n"
            "3. Get keys at: https://platform.openai.com/ or https://platform.deepseek.com/"
        )

    config = provider_configs[provider]
    api_key = os.getenv(config["key_var"])
    if not api_key:
        raise APIKeyMissingError(
            f"{config['key_var']} is not configured or is empty.\n"
            f"Get your key at: {config['signup_url']}"
        )

    base_url = os.getenv(config["base_url_var"], config["default_base_url"])
    _client = OpenAI(api_key=api_key, base_url=base_url)
    return _client


def is_api_configured() -> bool:
    """Check if any API key is configured (without initializing client)."""
    return bool(os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY"))


def get_response(messages: list, model: str = None, temperature: float = None) -> str:
    """
    Send messages to LLM API and get response.

    Args:
        messages: List of message dictionaries with 'role' and 'content'
        model: Optional model name, defaults to provider default
        temperature: Optional temperature (0.0-2.0). Some models (e.g., GPT-5 reasoning)
                    may not support custom temperature values.

    Raises:
        APIKeyMissingError: If API key is not configured
        APICallError: If API call fails
    """
    try:
        client = get_llm_client()
        model_name = model or get_default_model()

        # Build kwargs with optional temperature
        kwargs = {
            "model": model_name,
            "messages": messages
        }

        # Try with temperature if specified
        if temperature is not None:
            try:
                kwargs["temperature"] = temperature
                response = client.chat.completions.create(**kwargs)
                return response.choices[0].message.content
            except Exception as e:
                # Check if error is related to temperature parameter
                error_msg = str(e).lower()
                is_temperature_error = (
                    "temperature" in error_msg and
                    any(kw in error_msg for kw in TEMPERATURE_ERROR_KEYWORDS)
                )
                if is_temperature_error:
                    # Model doesn't support temperature, fall back
                    del kwargs["temperature"]
                else:
                    # Different error, re-raise
                    raise

        # Call without temperature (or after fallback)
        response = client.chat.completions.create(**kwargs)
        return response.choices[0].message.content
    except APIKeyMissingError:
        raise
    except Exception as e:
        raise APICallError(f"API call failed: {str(e)}")


def get_response_stream(messages: list, model: str = None, temperature: float = None):
    """
    Send messages to LLM API and yield response chunks as they arrive.

    Args:
        messages: List of message dictionaries with 'role' and 'content'
        model: Optional model name, defaults to provider default
        temperature: Optional temperature (0.0-2.0). Some models (e.g., GPT-5 reasoning)
                    may not support custom temperature values.

    Yields:
        str: Text chunks as they stream from the API

    Raises:
        APIKeyMissingError: If API key is not configured
        APICallError: If API call fails
    """
    try:
        client = get_llm_client()
        model_name = model or get_default_model()

        kwargs = {
            "model": model_name,
            "messages": messages,
            "stream": True,
        }

        # Try with temperature if specified, with fallback for unsupported models
        if temperature is not None:
            try:
                kwargs["temperature"] = temperature
                stream = client.chat.completions.create(**kwargs)
                for chunk in stream:
                    if not chunk.choices:
                        continue
                    delta = chunk.choices[0].delta
                    if not delta:
                        continue
                    content = getattr(delta, "content", None)
                    if content is not None:
                        yield content
                return
            except Exception as e:
                error_msg = str(e).lower()
                is_temperature_error = (
                    "temperature" in error_msg and
                    any(kw in error_msg for kw in TEMPERATURE_ERROR_KEYWORDS)
                )
                if is_temperature_error:
                    del kwargs["temperature"]
                else:
                    raise

        # Stream without temperature (or after fallback)
        stream = client.chat.completions.create(**kwargs)
        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if not delta:
                continue
            content = getattr(delta, "content", None)
            if content is not None:
                yield content
    except APIKeyMissingError:
        raise
    except Exception as e:
        raise APICallError(f"API call failed: {str(e)}")


def rewrite_query_with_context(user_message: str, history: list, max_history: int = 4) -> str:
    """
    Rewrite user query with conversation context for better RAG retrieval.

    When users ask follow-up questions like "what about fever?", this function
    rewrites the query to include relevant context from history.
    """
    if not history or len(user_message) > 80:
        return user_message
    if not _looks_like_followup(user_message):
        return user_message

    heuristic = _heuristic_rewrite(user_message, history)
    if heuristic:
        return heuristic

    recent_history = history[-max_history:]
    history_text = "\n".join([
        f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content'][:200]}"
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
        rewritten = get_response([{"role": "user", "content": prompt}])
        return rewritten.strip().strip('"').strip("'")
    except Exception as e:
        print(f"[WARN] Query rewrite failed: {e}")
        return user_message


def _looks_like_followup(user_message: str) -> bool:
    """Heuristic check for whether a query is a follow-up."""
    text = user_message.strip()
    if not text:
        return False

    lower = text.lower()

    followup_prefixes = ["what about", "how about", "and ", "also ", "then ", "so ", "what if"]
    followup_contains = ["what about", "how about", "and also", "also", "too", "else", "another", "besides"]

    if any(lower.startswith(p) for p in followup_prefixes):
        return True
    if any(p in lower for p in followup_contains) and len(lower.split()) <= 12:
        return True

    # Chinese follow-up markers
    if re.search(r"[那这].{0,4}呢$", text) or "还有" in text or "另外" in text or "也" in text:
        return True

    standalone_patterns = [
        r"\bwhat is\b",
        r"\bwhat's\b",
        r"\bdefine\b",
        r"\bdefinition of\b",
        r"\bexplain\b",
        r"\bmeaning of\b",
        r"\bside effects?\b",
        r"\bsymptoms of\b",
        r"\btreatment of\b",
        r"\bcauses of\b",
        r"\buses of\b",
        r"\bdosage\b",
        r"\bdose\b",
        r"\bcontraindications?\b",
        r"\bhow to take\b",
    ]
    if any(re.search(pat, lower) for pat in standalone_patterns):
        return False

    chinese_standalone = ["什么是", "解释", "定义", "副作用", "症状", "治疗", "用法", "剂量", "原因"]
    if any(term in text for term in chinese_standalone):
        return False

    # Very short queries often rely on context (e.g., "nausea?")
    word_count = len([w for w in re.split(r"\s+", text) if w])
    if word_count <= 3 or len(text) <= 12:
        # If user explicitly states their own symptom, treat as standalone
        if re.search(r"\b(i|my|me)\b", lower) or "我" in text:
            return False
        return True

    return False


def _heuristic_rewrite(user_message: str, history: list) -> Optional[str]:
    """Fast follow-up rewrite to avoid an extra LLM call."""
    last_user = None
    for msg in reversed(history):
        if msg.get("role") == "user":
            last_user = msg.get("content", "").strip()
            break
    if not last_user:
        return None

    # Keep heuristic rewrites short to avoid noise
    if len(last_user) > 140 or len(user_message) > 60:
        return None

    # Simple concatenation works well for retrieval
    return f"{last_user}. Follow-up: {user_message}"


def build_messages(system_prompt: str, user_message: str, context: str = "", history: list = None) -> list:
    """Build message list for API call with optional conversation history."""
    messages = [{"role": "system", "content": system_prompt}]

    if history:
        messages.extend({"role": msg["role"], "content": msg["content"]} for msg in history)

    if context:
        user_content = f"### Reference Information:\n{context}\n\n### Question:\n{user_message}"
    else:
        user_content = user_message

    messages.append({"role": "user", "content": user_content})
    return messages
