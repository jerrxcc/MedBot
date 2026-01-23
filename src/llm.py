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


def _get_client():
    """Get or initialize the OpenAI client (lazy loading)."""
    global _client
    if _client is None:
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise APIKeyMissingError(
                "DeepSeek API key not found. Please set DEEPSEEK_API_KEY in your .env file.\n"
                "1. Copy .env.example to .env\n"
                "2. Add your API key: DEEPSEEK_API_KEY=your_key_here\n"
                "3. Get a key at: https://platform.deepseek.com/"
            )
        _client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
    return _client


def is_api_configured() -> bool:
    """Check if API key is configured (without initializing client)."""
    return bool(os.getenv("DEEPSEEK_API_KEY"))


def get_response(messages: list, model: str = "deepseek-chat") -> str:
    """
    Send messages to DeepSeek API and get response.

    Args:
        messages: List of message dicts with 'role' and 'content'
        model: Model name to use

    Returns:
        Response content string

    Raises:
        APIKeyMissingError: If API key is not configured
        APICallError: If API call fails
    """
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


def build_messages(system_prompt: str, user_message: str, context: str = "") -> list:
    """
    Build message list for API call.

    Args:
        system_prompt: System instruction
        user_message: User's question
        context: Retrieved context from RAG

    Returns:
        List of message dicts
    """
    messages = [{"role": "system", "content": system_prompt}]

    if context:
        full_message = f"### Reference Information:\n{context}\n\n### Question:\n{user_message}"
    else:
        full_message = user_message

    messages.append({"role": "user", "content": full_message})
    return messages
