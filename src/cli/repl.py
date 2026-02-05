"""
Main REPL (Read-Eval-Print Loop) for MedBot CLI.
"""

import sys
from typing import Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings

from .completer import CommandCompleter
from .commands import CommandHandler
from .handlers import FeatureHandler
from .history import ConversationHistory
from .intent import IntentDetector
from ..llm import is_api_configured, APIKeyMissingError, APICallError


class MedBotREPL:
    """
    Interactive CLI for MedBot with conversation support.
    """

    BANNER = """╔══════════════════════════════════════╗
║          MedBot CLI                  ║
║     AI Medical Assistant             ║
╚══════════════════════════════════════╝"""

    def __init__(self):
        """Initialize REPL components."""
        self.history = ConversationHistory(max_turns=10)
        self.intent_detector = IntentDetector()
        self.feature_handler = FeatureHandler()
        self.command_handler = CommandHandler(
            history=self.history,
            api_status_func=self._get_api_status
        )

        self.interactive = sys.stdin.isatty()
        self.session = None

        if self.interactive:
            # Setup prompt-toolkit
            self.prompt_history = InMemoryHistory()
            self.completer = CommandCompleter(
                self.command_handler.get_completions()
            )

            # Create key bindings
            kb = KeyBindings()

            @kb.add('c-c')
            def _(event):
                """Cancel current input on Ctrl+C."""
                event.app.current_buffer.reset()

            @kb.add('c-d')
            def _(event):
                """Exit on Ctrl+D."""
                event.app.exit(result='__exit__')

            self.session = PromptSession(
                history=self.prompt_history,
                completer=self.completer,
                key_bindings=kb,
            )

    def _get_api_status(self) -> str:
        """Get current API configuration status."""
        if not is_api_configured():
            return "not configured"

        try:
            from ..llm import get_llm_client
            client = get_llm_client()
            # Try to determine which API is being used
            if hasattr(client, 'base_url'):
                if 'deepseek' in str(client.base_url).lower():
                    return "deepseek connected"
            return "openai connected"
        except Exception:
            # Catch only standard exceptions, not KeyboardInterrupt/SystemExit
            return "error"

    def _show_banner(self):
        """Display welcome banner."""
        print(self.BANNER)
        print()
        status = self._get_api_status()
        print(f"[API: {status}]")

        if status == "not configured":
            print("\n⚠️  No API key configured!")
            print("Set OPENAI_API_KEY or DEEPSEEK_API_KEY environment variable.")
            print("See README.md for setup instructions.\n")

        print()

    def _handle_input(self, user_input: str) -> bool:
        """
        Handle user input (command or query).

        Args:
            user_input: User input string

        Returns:
            True if should quit, False otherwise
        """
        # Check for slash commands
        if self.command_handler.is_command(user_input):
            should_quit, response = self.command_handler.handle(user_input)
            if response:
                print(response)
                print()
            return should_quit

        # Handle natural language query
        try:
            # Detect intent
            mode = self.command_handler.get_mode()
            intent = self.intent_detector.detect(user_input, mode)
            confidence = self.intent_detector.get_confidence(user_input, intent)

            # Show detected intent with confidence indicator
            if mode is None:
                confidence_indicator = "" if confidence >= 0.7 else " (?)"
                print(f"[Detected: {intent}{confidence_indicator}]")
            else:
                print(f"[Mode: {intent}]")

            # Get response from feature handler
            history_for_intent = self.history.get_messages_for_intent(intent)
            response = self.feature_handler.handle(
                query=user_input,
                intent=intent,
                history=history_for_intent,
            )

            # Update conversation history
            self.history.add('user', user_input, intent=intent)
            self.history.add('assistant', response, intent=intent)

            # Display response
            print()
            print(response)
            print()

            return False

        except APIKeyMissingError:
            print("\n⚠️  API key not configured!")
            print("Set OPENAI_API_KEY or DEEPSEEK_API_KEY environment variable.\n")
            return False

        except APICallError as e:
            print(f"\n❌ API Error: {e}\n")
            return False

        except KeyboardInterrupt:
            print("\n[Interrupted]")
            return False

        except Exception as e:
            print(f"\n❌ Error: {e}\n")
            return False

    def run(self):
        """
        Run the REPL loop.
        """
        self._show_banner()

        if not self.interactive:
            for line in sys.stdin:
                user_input = line.strip()
                if not user_input:
                    continue
                should_quit = self._handle_input(user_input)
                if should_quit:
                    break
            return

        while True:
            try:
                # Get input using prompt-toolkit
                user_input = self.session.prompt("medbot> ")

                # Handle special exit signal from Ctrl+D
                if user_input == '__exit__':
                    print("Goodbye!")
                    break

                # Skip empty input
                if not user_input.strip():
                    continue

                # Process input
                should_quit = self._handle_input(user_input.strip())

                if should_quit:
                    break

            except KeyboardInterrupt:
                # Ctrl+C pressed - continue loop
                print()
                continue

            except EOFError:
                # Ctrl+D pressed
                print("Goodbye!")
                break

            except Exception as e:
                print(f"\n❌ Unexpected error: {e}\n")
                continue
