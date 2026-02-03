import os
from .llm import get_response

def translate_query_for_retrieval(query: str) -> str:
    """
    Translate a non-English query into English keywords for better retrieval.
    If the query is already in English, it returns it as is.
    """
    # Detect if contains Chinese characters
    has_chinese = any('\u4e00' <= char <= '\u9fff' for char in query)
    
    if not has_chinese:
        return query
        
    system_prompt = (
        "You are a medical query translator. Your task is to translate a Chinese medical question "
        "into essential English keywords or a concise English phrase suitable for semantic search "
        "in an English medical database (MedQuAD).\n"
        "Return ONLY the English translation, no explanation."
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Translate this query: {query}"}
    ]
    
    try:
        translated = get_response(messages).strip()
        # Clean up common LLM artifacts
        translated = translated.replace('"', '').replace("'", "")
        return translated
    except Exception:
        # Fallback to original query if translation fails
        return query
