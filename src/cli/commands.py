"""
Slash command handler for MedBot CLI.
"""

from typing import Optional, Tuple


class CommandHandler:
    """
    Handles slash commands for CLI control.
    """

    COMMANDS = {
        '/help': 'Show usage instructions',
        '/mode': 'Switch feature mode (auto/symptoms/medication/doctors/clinics)',
        '/clear': 'Clear conversation history',
        '/status': 'Show current mode and API status',
        '/history': 'Show recent conversation',
        '/quit': 'Exit MedBot CLI',
        '/exit': 'Exit MedBot CLI',
    }

    VALID_MODES = ['auto', 'symptoms', 'medication', 'doctors', 'clinics']

    def __init__(self, history, api_status_func):
        """
        Initialize command handler.

        Args:
            history: ConversationHistory instance
            api_status_func: Function that returns API status string
        """
        self.history = history
        self.api_status_func = api_status_func
        self.mode = 'auto'

    def is_command(self, text: str) -> bool:
        """
        Check if text is a slash command.

        Args:
            text: Input text

        Returns:
            True if text starts with '/'
        """
        return text.strip().startswith('/')

    def handle(self, command: str) -> Tuple[bool, Optional[str]]:
        """
        Handle a slash command.

        Args:
            command: Command string (including '/')

        Returns:
            Tuple of (should_quit, response_message)
        """
        parts = command.strip().split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else None

        if cmd in ['/quit', '/exit']:
            return True, "Goodbye!"

        elif cmd == '/help':
            return False, self._help()

        elif cmd == '/mode':
            return False, self._mode(args)

        elif cmd == '/clear':
            self.history.clear()
            return False, "Conversation history cleared."

        elif cmd == '/status':
            return False, self._status()

        elif cmd == '/history':
            return False, self._history()

        else:
            return False, f"Unknown command: {cmd}\nType /help for available commands."

    def _help(self) -> str:
        """Generate help message."""
        lines = [
            "MedBot CLI - AI Medical Assistant",
            "",
            "FEATURES:",
            "  • Symptoms - Describe symptoms for medical information",
            "  • Medication - Ask about drugs and medicines",
            "  • Doctors - Search for healthcare providers",
            "  • Clinics - Find medical facilities near you",
            "",
            "COMMANDS:",
        ]

        for cmd, desc in self.COMMANDS.items():
            lines.append(f"  {cmd:12} - {desc}")

        lines.extend([
            "",
            "USAGE:",
            "  medbot> I have a headache and fever",
            "  medbot> what are side effects of ibuprofen?",
            "  medbot> find a Chinese speaking dentist",
            "  medbot> clinic near 123456",
            "  medbot> /mode doctors",
            "",
            "TIPS:",
            "  • The system auto-detects intent from your query",
            "  • Use /mode to force a specific feature mode",
            "  • Ask follow-up questions naturally",
            "  • Ctrl+C cancels input, Ctrl+D exits",
        ])

        return "\n".join(lines)

    def _mode(self, args: Optional[str]) -> str:
        """Handle /mode command."""
        if not args:
            return f"Current mode: {self.mode}\nUsage: /mode <{'/'.join(self.VALID_MODES)}>"

        new_mode = args.strip().lower()
        if new_mode not in self.VALID_MODES:
            return f"Invalid mode: {new_mode}\nValid modes: {', '.join(self.VALID_MODES)}"

        self.mode = new_mode
        return f"Switched to '{new_mode}' mode."

    def _status(self) -> str:
        """Generate status message."""
        api_status = self.api_status_func()
        return f"Mode: {self.mode}\nAPI: {api_status}\nHistory: {len(self.history.messages)} messages"

    def _history(self) -> str:
        """Get conversation history summary."""
        if not self.history.has_context():
            return "No conversation history."

        return "Recent conversation:\n" + self.history.get_summary()

    def get_mode(self) -> Optional[str]:
        """
        Get current mode for intent detection.

        Returns:
            Current mode if not 'auto', else None
        """
        return None if self.mode == 'auto' else self.mode

    def get_completions(self) -> list:
        """
        Get list of available commands for auto-completion.

        Returns:
            List of command strings
        """
        return list(self.COMMANDS.keys())
