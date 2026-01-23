import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)


def get_response(messages: list, model: str = "deepseek-chat") -> str:
    """
    Send messages to DeepSeek API and get response.

    Args:
        messages: List of message dicts with 'role' and 'content'
        model: Model name to use

    Returns:
        Response content string
    """
    response = client.chat.completions.create(
        model=model,
        messages=messages
    )
    return response.choices[0].message.content


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
