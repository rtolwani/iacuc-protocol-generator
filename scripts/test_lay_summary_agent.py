#!/usr/bin/env python3
"""
Test script for Lay Summary Writer Agent.

Usage:
    python scripts/test_lay_summary_agent.py --input "Your technical text here"
    python scripts/test_lay_summary_agent.py --example behavioral
    python scripts/test_lay_summary_agent.py --example surgical
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.lay_summary_writer import (
    generate_lay_summary,
    EXAMPLE_TECHNICAL_TEXTS,
)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test the Lay Summary Writer agent"
    )
    parser.add_argument(
        "--input",
        type=str,
        help="Technical text to simplify",
    )
    parser.add_argument(
        "--example",
        type=str,
        choices=list(EXAMPLE_TECHNICAL_TEXTS.keys()),
        help="Use a built-in example text",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show agent reasoning",
    )

    args = parser.parse_args()

    if not args.input and not args.example:
        parser.error("Must specify either --input or --example")

    # Get the text to process
    if args.example:
        text = EXAMPLE_TECHNICAL_TEXTS[args.example]
        print(f"Using example: {args.example}")
    else:
        text = args.input

    print("=" * 60)
    print("Lay Summary Writer Agent Test")
    print("=" * 60)
    print()
    print("Input text:")
    print("-" * 40)
    print(text.strip())
    print("-" * 40)
    print()
    print("Generating lay summary...")
    print()

    # Generate summary
    result = generate_lay_summary(text, verbose=args.verbose)

    print("=" * 60)
    print("RESULT")
    print("=" * 60)
    print()
    print("Lay Summary:")
    print("-" * 40)
    print(result["summary"])
    print("-" * 40)
    print()
    print("Readability Metrics:")
    print(f"  Flesch-Kincaid Grade: {result['readability']['grade']}")
    print(f"  Flesch Reading Ease: {result['readability']['ease']}")
    print(f"  Word Count: {result['readability']['word_count']}")
    print(f"  Sentence Count: {result['readability']['sentence_count']}")
    print()

    if result["passes"]:
        print("✅ PASS - Summary meets grade 14 target (college level)!")
    else:
        print("⚠️  Summary is above grade 14 target")

    return 0 if result["passes"] else 1


if __name__ == "__main__":
    sys.exit(main())
