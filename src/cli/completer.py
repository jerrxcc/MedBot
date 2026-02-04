"""
Auto-completion support for MedBot CLI using prompt-toolkit.
"""

from prompt_toolkit.completion import Completer, Completion


class CommandCompleter(Completer):
    """
    Auto-completer for slash commands.
    """

    def __init__(self, commands: list):
        """
        Initialize completer with available commands.

        Args:
            commands: List of command strings (e.g., ['/help', '/mode'])
        """
        self.commands = sorted(commands)

    def get_completions(self, document, complete_event):
        """
        Generate completions for current input.

        Args:
            document: Current document
            complete_event: Completion event

        Yields:
            Completion objects
        """
        text = document.text_before_cursor.lstrip()

        # Only complete if input starts with '/'
        if not text.startswith('/'):
            return

        # Find matching commands
        for cmd in self.commands:
            if cmd.startswith(text):
                yield Completion(
                    cmd,
                    start_position=-len(text),
                    display=cmd,
                )
