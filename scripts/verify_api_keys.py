#!/usr/bin/env python3
"""
Verify that API keys are properly configured and working.

Run this script after setting up your .env file to ensure
all required API keys are valid.

Usage:
    python scripts/verify_api_keys.py
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import get_settings


def verify_anthropic_key(api_key: str) -> bool:
    """Verify Anthropic API key by making a minimal API call."""
    try:
        from anthropic import Anthropic

        client = Anthropic(api_key=api_key)

        # Make a minimal API call to verify the key works
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}],
        )

        return True
    except Exception as e:
        print(f"  Error: {e}")
        return False


def verify_openai_key(api_key: str) -> bool:
    """Verify OpenAI API key by making a minimal API call."""
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)

        # Make a minimal API call to verify the key works
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input="test",
        )

        return True
    except Exception as e:
        print(f"  Error: {e}")
        return False


def main():
    """Main verification routine."""
    print("=" * 60)
    print("IACUC Protocol Generator - API Key Verification")
    print("=" * 60)
    print()

    settings = get_settings()
    all_valid = True

    # Check Anthropic API Key (Required)
    print("Checking Anthropic API Key (Required)...")
    if not settings.anthropic_api_key:
        print("  ❌ MISSING - Set ANTHROPIC_API_KEY in your .env file")
        print("     Get your key at: https://console.anthropic.com/")
        all_valid = False
    elif settings.anthropic_api_key == "your_anthropic_api_key_here":
        print("  ❌ NOT CONFIGURED - Replace the placeholder in your .env file")
        all_valid = False
    else:
        print("  Found key, verifying...")
        if verify_anthropic_key(settings.anthropic_api_key):
            print("  ✅ Anthropic API key is valid!")
        else:
            print("  ❌ Anthropic API key verification failed")
            all_valid = False

    print()

    # Check OpenAI API Key (Optional)
    print("Checking OpenAI API Key (Optional - for embeddings)...")
    if not settings.openai_api_key:
        print("  ⚠️  NOT SET - Will use alternative embedding methods")
        print("     (This is optional, but OpenAI embeddings are recommended)")
    elif settings.openai_api_key == "your_openai_api_key_here":
        print("  ⚠️  NOT CONFIGURED - Placeholder value detected")
        print("     (This is optional, but OpenAI embeddings are recommended)")
    else:
        print("  Found key, verifying...")
        if verify_openai_key(settings.openai_api_key):
            print("  ✅ OpenAI API key is valid!")
        else:
            print("  ⚠️  OpenAI API key verification failed")
            print("     (Will fall back to alternative embedding methods)")

    print()
    print("=" * 60)

    if all_valid:
        print("✅ All required API keys are configured and valid!")
        print("   You can proceed with the next setup steps.")
        return 0
    else:
        print("❌ Some required API keys are missing or invalid.")
        print("   Please check your .env file and try again.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
