"""LLM client management and API utilities."""
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

_client = None


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
                # Match various error message formats from different API providers:
                # - "temperature ... unsupported"
                # - "parameter temperature is not valid"
                # - "temperature not supported/allowed"
                # - "invalid parameter: temperature"
                is_temperature_error = (
                    "temperature" in error_msg and
                    any(keyword in error_msg for keyword in [
                        "unsupported", "not supported", "not allowed",
                        "invalid", "not valid", "does not support"
                    ])
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


def rewrite_query_with_context(user_message: str, history: list, max_history: int = 4) -> str:
    """
    Rewrite user query with conversation context for better RAG retrieval.

    When users ask follow-up questions like "what about fever?", this function
    rewrites the query to include relevant context from history.
    """
    if not history or len(user_message) > 50:
        return user_message

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
