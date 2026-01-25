#!/usr/bin/env python3
"""Interactive command parser tester.

Test command sequences from the terminal and see parsed results.

Usage:
    python scripts/test_parser_interactive.py
    python scripts/test_parser_interactive.py "jarvis, move forward, turn right"
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pi.command_parser.parser import CommandParser
from pi.command_parser.command_schema import CommandType, PRIORITY_STOP


def format_command(cmd, index):
    """Format a command for display."""
    cmd_type = cmd.command_type.value
    params = cmd.parameters
    priority = cmd.priority
    
    priority_str = "STOP" if priority == 100 else f"{priority}"
    
    params_str = ", ".join([f"{k}={v}" for k, v in params.items()])
    
    return f"  [{index}] {cmd_type}({params_str}) [priority: {priority_str}]"


def test_command(text):
    """Test a single command string."""
    parser = CommandParser()
    
    print(f"\n{'='*70}")
    print(f"Input: '{text}'")
    print(f"{'='*70}")
    
    result = parser.parse(text)
    
    if result:
        print(f"\n✓ Parsed {len(result)} command(s):\n")
        for i, cmd in enumerate(result, 1):
            print(format_command(cmd, i))
    else:
        print("\n✗ No commands parsed (parser returned None)")
    
    print(f"\n{'='*70}\n")


def interactive_mode():
    """Run in interactive mode."""
    parser = CommandParser()
    
    print("="*70)
    print("Voice Rover Command Parser - Interactive Mode")
    print("="*70)
    print("\nEnter commands to test. Type 'quit' or 'exit' to stop.\n")
    print("Examples:")
    print("  jarvis, move forward")
    print("  jarvis, move forward fast, turn right slowly")
    print("  stop")
    print("  jarvis, make a circle")
    print("-"*70)
    
    while True:
        try:
            text = input("\n> ").strip()
            
            if text.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break
            
            if not text:
                continue
            
            result = parser.parse(text)
            
            if result:
                print(f"\n✓ Parsed {len(result)} command(s):")
                for i, cmd in enumerate(result, 1):
                    print(format_command(cmd, i))
            else:
                print("\n✗ No commands parsed")
        
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\n✗ Error: {e}")


def main():
    """Main function."""
    if len(sys.argv) > 1:
        test_command(" ".join(sys.argv[1:]))
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
