"""
Conversation history management for MedBot CLI.
"""

from typing import List, Dict, Optional


class ConversationHistory:
    """
    Manages conversation history with a sliding window.
    Keeps last 10 turns (20 messages) for context.
    """

    # Valid role values for OpenAI/DeepSeek API compatibility
    VALID_ROLES = ('user', 'assistant', 'system')

    def __init__(self, max_turns: int = 10):
        """
        Initialize conversation history.

        Args:
            max_turns: Maximum number of conversation turns to keep (default: 10)
        """
        self.max_turns = max_turns
        self.messages: List[Dict[str, str]] = []

    def add(self, role: str, content: str) -> None:
        """
        Add a message to history.

        Args:
            role: Message role ('user' or 'assistant')
            content: Message content

        Raises:
            ValueError: If role is not a valid value
        """
        # Validate role to ensure API compatibility
        if role not in self.VALID_ROLES:
            raise ValueError(
                f"Invalid role: '{role}'. Must be one of: {', '.join(self.VALID_ROLES)}"
            )

        self.messages.append({
            'role': role,
            'content': content
        })

        # Maintain sliding window (2 messages per turn)
        max_messages = self.max_turns * 2
        if len(self.messages) > max_messages:
            self.messages = self.messages[-max_messages:]

    def clear(self) -> None:
        """Clear all conversation history."""
        self.messages = []

    def get_messages(self) -> List[Dict[str, str]]:
        """
        Get all messages in history.

        Returns:
            List of message dictionaries with 'role' and 'content' keys
        """
        return self.messages.copy()

    def get_summary(self) -> str:
        """
        Get a summary of conversation history.

        Returns:
            Human-readable summary of messages
        """
        if not self.messages:
            return "No conversation history"

        lines = []
        for i, msg in enumerate(self.messages, 1):
            role_label = "You" if msg['role'] == 'user' else "MedBot"
            # Truncate long messages
            content = msg['content'][:80]
            if len(msg['content']) > 80:
                content += "..."
            lines.append(f"{i}. {role_label}: {content}")

        return "\n".join(lines)

    def has_context(self) -> bool:
        """
        Check if there's conversation context.

        Returns:
            True if history contains messages
        """
        return len(self.messages) > 0

    def get_last_user_message(self) -> Optional[str]:
        """
        Get the last user message.

        Returns:
            Last user message content or None if no user messages
        """
        for msg in reversed(self.messages):
            if msg['role'] == 'user':
                return msg['content']
        return None
