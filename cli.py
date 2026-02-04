#!/usr/bin/env python3
"""
MedBot CLI - Interactive conversational interface for MedBot.

Usage:
    python cli.py
"""

import sys

from src.cli.repl import MedBotREPL


def main():
    """Main entry point for MedBot CLI."""
    try:
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
