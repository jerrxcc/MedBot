"""
Conversation history management for MedBot CLI.
"""

from typing import List, Dict, Optional


class ConversationHistory:
    """
    Manages conversation history with a sliding window.
    Keeps last 10 turns (20 messages) for context.
    """

    # Valid role values for conversation history
    # Note: 'system' role is handled separately in build_messages(), not in history
    VALID_ROLES = ('user', 'assistant')

    def __init__(self, max_turns: int = 10):
        """
        Initialize conversation history.

        Args:
            max_turns: Maximum number of conversation turns to keep (default: 10)
        """
        self.max_turns = max_turns
        self.messages: List[Dict[str, str]] = []

    def add(self, role: str, content: str, intent: Optional[str] = None) -> None:
        """
        Add a message to history.

        Args:
            role: Message role ('user' or 'assistant')
            content: Message content
            intent: Optional intent label for routing/rewriting

        Raises:
            ValueError: If role is not a valid value
        """
        # Validate role to ensure API compatibility
        if role not in self.VALID_ROLES:
            raise ValueError(
                f"Invalid role: '{role}'. Must be one of: {', '.join(self.VALID_ROLES)}"
            )

        msg = {'role': role, 'content': content}
        if intent:
            msg['intent'] = intent
        self.messages.append(msg)

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

    def get_messages_for_intent(
        self,
        intent: Optional[str],
        max_turns: Optional[int] = None,
        recent_context_turns: int = 3
    ) -> List[Dict[str, str]]:
        """
        Get messages with intent awareness while preserving cross-intent context.

        This method keeps recent messages regardless of intent to maintain
        conversation context when users switch topics mid-conversation
        (e.g., asking about symptoms then medication).

        Args:
            intent: Intent label to prioritize
            max_turns: Optional max turns to keep (defaults to history max_turns)
            recent_context_turns: Number of recent turns to always include
                                  regardless of intent (default: 3)

        Returns:
            List of message dictionaries with recent context preserved
        """
        if not intent:
            return self.get_messages()

        max_turns = self.max_turns if max_turns is None else max_turns
        max_messages = max_turns * 2
        recent_messages = recent_context_turns * 2

        # Always include the most recent messages for cross-intent context
        recent = self.messages[-recent_messages:] if len(self.messages) >= recent_messages else self.messages[:]

        # Get older messages filtered by intent
        older = self.messages[:-recent_messages] if len(self.messages) > recent_messages else []
        older_filtered = [msg for msg in older if msg.get('intent') == intent]

        # Combine: intent-filtered older messages + all recent messages
        combined = older_filtered + recent
        return combined[-max_messages:]

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
            content = msg['content'][:80] + ("..." if len(msg['content']) > 80 else "")
            lines.append(f"{i}. {role_label}: {content}")

        return "\n".join(lines)

    def has_context(self) -> bool:
        """Check if there's conversation context."""
        return bool(self.messages)

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
