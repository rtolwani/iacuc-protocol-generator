#!/usr/bin/env python3
"""
Test script for Regulatory Scout Agent.

Usage:
    python scripts/test_regulatory_scout.py --species "rabbit" --procedures "survival surgery"
    python scripts/test_regulatory_scout.py --quick --species "mouse" --procedures "behavioral observation"
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.regulatory_scout import (
    analyze_protocol_regulations,
    quick_regulatory_check,
)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test the Regulatory Scout agent"
    )
    parser.add_argument(
        "--species",
        type=str,
        required=True,
        help="Species being used (e.g., 'mouse', 'rabbit')",
    )
    parser.add_argument(
        "--procedures",
        type=str,
        required=True,
        help="Description of procedures",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick analysis without LLM calls",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show agent reasoning",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Regulatory Scout Analysis")
    print("=" * 60)
    print()
    print(f"Species: {args.species}")
    print(f"Procedures: {args.procedures}")
    print()

    if args.quick:
        print("Running quick analysis (no LLM)...")
        result = quick_regulatory_check(args.species, args.procedures)
        
        print()
        print("=" * 60)
        print("RESULTS")
        print("=" * 60)
        print()
        print(f"Species Category: {result['species_category']}")
        print(f"Pain Category: {result['pain_category']} - {result['pain_category_name']}")
        
        if result['requires_justification']:
            print("⚠️  Category E justification REQUIRED")
        
        print()
        print("Species Requirements:")
        for req in result['species_requirements']:
            print(f"  • {req}")
        
        if result['procedure_requirements']:
            print()
            print("Procedure Requirements:")
            for proc in result['procedure_requirements']:
                print(f"  {proc['type']}:")
                for reg in proc['regulations']:
                    print(f"    • {reg}")
        
        print()
        print("Recommendations:")
        for rec in result['recommendations']:
            print(f"  • {rec}")
        
    else:
        print("Running full analysis with Regulatory Scout agent...")
        print()
        
        result = analyze_protocol_regulations(
            species=args.species,
            procedures=args.procedures,
            verbose=args.verbose,
        )
        
        print()
        print("=" * 60)
        print("RESULTS")
        print("=" * 60)
        print()
        print(f"Species: {result['species']}")
        print(f"Species Category: {result['species_category']['category']}")
        print()
        print(f"Pain Category: {result['pain_category']['category']} - {result['pain_category']['name']}")
        print(f"Confidence: {result['pain_category']['confidence']}")
        
        if result['pain_category']['requires_justification']:
            print("⚠️  Category E justification REQUIRED")
        
        print()
        print("Detailed Analysis:")
        print("-" * 40)
        print(result['detailed_analysis'])

    return 0


if __name__ == "__main__":
    sys.exit(main())
