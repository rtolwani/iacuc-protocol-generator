#!/usr/bin/env python3
"""
Test script for Formulary Lookup Tool.

Usage:
    python scripts/test_formulary_lookup.py --drug "ketamine" --species "mouse"
    python scripts/test_formulary_lookup.py --drug "buprenorphine" --species "rat"
    python scripts/test_formulary_lookup.py --list-drugs --species "mouse"
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.tools.formulary_tool import DrugFormulary, FormularyLookupTool


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test the Formulary Lookup tool"
    )
    parser.add_argument(
        "--drug",
        type=str,
        help="Drug name to look up",
    )
    parser.add_argument(
        "--species",
        type=str,
        help="Species for species-specific dosing",
    )
    parser.add_argument(
        "--validate-dose",
        type=str,
        help="Validate a proposed dose (e.g., '100 mg/kg')",
    )
    parser.add_argument(
        "--list-drugs",
        action="store_true",
        help="List all drugs available for a species",
    )
    parser.add_argument(
        "--protocol",
        type=str,
        help="Look up a combination protocol by name",
    )

    args = parser.parse_args()

    formulary = DrugFormulary()
    tool = FormularyLookupTool()

    print("=" * 60)
    print("FORMULARY LOOKUP TEST")
    print("=" * 60)
    print()

    if args.list_drugs and args.species:
        print(f"Drugs with dosing info for {args.species}:")
        print("-" * 40)
        drugs = formulary.list_drugs_for_species(args.species)
        for drug in drugs:
            print(f"  • {drug}")
        print(f"\nTotal: {len(drugs)} drugs")
        return 0

    if args.protocol:
        print(f"Looking up protocol: {args.protocol}")
        print("-" * 40)
        protocol = formulary.get_combination_protocol(args.protocol)
        if protocol:
            print(f"Name: {protocol['name']}")
            print(f"Indication: {protocol['indication']}")
            print(f"Duration: {protocol['duration']}")
            print("\nComponents:")
            for comp in protocol["components"]:
                print(f"  • {comp['drug']}: {comp['dose']} {comp['route']}")
            if "reversal" in protocol:
                print(f"\nReversal: {protocol['reversal']}")
            if "notes" in protocol:
                print(f"Notes: {protocol['notes']}")
        else:
            print("Protocol not found")
        return 0

    if args.drug:
        if args.validate_dose and args.species:
            print(f"Validating dose for {args.drug}:")
            print(f"  Species: {args.species}")
            print(f"  Proposed dose: {args.validate_dose}")
            print("-" * 40)
            
            result = formulary.validate_dose(args.drug, args.species, args.validate_dose)
            print(f"Status: {result['status']}")
            print(f"Valid: {result['valid']}")
            print(f"Message: {result['message']}")
            if "approved_range" in result:
                print(f"Approved Range: {result['approved_range']}")
        else:
            # Simple lookup using the tool
            query = args.drug
            if args.species:
                query = f"{args.drug} for {args.species}"
            
            print(f"Query: {query}")
            print("-" * 40)
            print()
            result = tool._run(query)
            print(result)
    else:
        print("Formulary Info:")
        print(f"  Path: {formulary.formulary_path}")
        print(f"  Total drugs: {len(formulary.data.get('drugs', []))}")
        print(f"  Combination protocols: {len(formulary.data.get('combination_protocols', []))}")
        print(f"  Emergency drugs: {len(formulary.data.get('emergency_drugs', []))}")
        print()
        print("Usage examples:")
        print("  --drug ketamine --species mouse")
        print("  --drug buprenorphine --species rat --validate-dose '0.05 mg/kg'")
        print("  --list-drugs --species mouse")
        print("  --protocol ketamine/xylazine")

    return 0


if __name__ == "__main__":
    sys.exit(main())
