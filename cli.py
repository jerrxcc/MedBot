#!/usr/bin/env python3
"""
MedBot CLI - Interactive conversational interface for MedBot.

Usage:
    python cli.py
"""

import sys
import warnings


def _suppress_cli_warnings() -> None:
    """Suppress known non-actionable warnings in CLI output."""
    # Filter by message first so it applies even if urllib3 is imported later.
    warnings.filterwarnings(
        "ignore",
        message="urllib3 v2 only supports OpenSSL*",
        category=Warning,
    )
    try:
        from urllib3.exceptions import NotOpenSSLWarning
        warnings.filterwarnings("ignore", category=NotOpenSSLWarning)
    except Exception:
        # If urllib3 isn't available yet, skip silently.
        pass


def main():
    """Main entry point for MedBot CLI."""
    try:
        _suppress_cli_warnings()
        from src.cli.repl import MedBotREPL
        repl = MedBotREPL()
        repl.run()
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
