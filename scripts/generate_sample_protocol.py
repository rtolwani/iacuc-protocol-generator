#!/usr/bin/env python3
"""
Generate a sample IACUC protocol.

This script demonstrates the full protocol generation workflow.

Usage:
    python scripts/generate_sample_protocol.py --type behavioral --output output.json
    python scripts/generate_sample_protocol.py --type surgical --verbose
    python scripts/generate_sample_protocol.py --type tumor --quick
"""

import argparse
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.crew import (
    ProtocolInput,
    generate_protocol,
    quick_crew_check,
)


# Sample protocol inputs
SAMPLE_PROTOCOLS = {
    "behavioral": ProtocolInput(
        title="Effects of Environmental Enrichment on Anxiety-Related Behavior",
        pi_name="Dr. Jane Smith",
        species="mouse",
        strain="C57BL/6J",
        total_animals=60,
        research_description=(
            "This study investigates how environmental enrichment affects "
            "anxiety-related behaviors in mice. Animals will be housed in "
            "standard or enriched environments for 4 weeks, then tested in "
            "the elevated plus maze and open field test. Understanding these "
            "mechanisms could lead to new treatments for anxiety disorders."
        ),
        procedures=(
            "Behavioral testing including elevated plus maze (10 min/session) "
            "and open field test (30 min/session). Animals will be habituated "
            "to handling for 1 week before testing. All testing occurs during "
            "the light phase. Euthanasia by CO2 inhalation followed by cervical "
            "dislocation for brain tissue collection."
        ),
        study_duration="6 weeks",
        primary_endpoint="Time spent in open arms of elevated plus maze",
    ),
    
    "surgical": ProtocolInput(
        title="Cranial Window Implantation for In Vivo Two-Photon Imaging",
        pi_name="Dr. John Doe",
        species="mouse",
        strain="Thy1-GFP-M",
        total_animals=30,
        research_description=(
            "This study uses in vivo two-photon microscopy to image neuronal "
            "activity through a chronic cranial window. The window allows "
            "repeated imaging sessions over several weeks to track structural "
            "plasticity of dendritic spines during learning."
        ),
        procedures=(
            "Survival surgery for cranial window implantation under isoflurane "
            "anesthesia (1-2% in oxygen). A 3mm diameter craniotomy will be "
            "performed over the primary motor cortex. Post-operative analgesia "
            "with buprenorphine (0.1 mg/kg SC) and carprofen (5 mg/kg SC). "
            "Weekly imaging sessions under brief isoflurane anesthesia (30 min). "
            "Euthanasia by pentobarbital overdose (150 mg/kg IP) at study end."
        ),
        study_duration="8 weeks",
        primary_endpoint="Dendritic spine density changes over time",
    ),
    
    "tumor": ProtocolInput(
        title="Efficacy of Novel Anti-Cancer Compound XYZ-123",
        pi_name="Dr. Sarah Johnson",
        species="mouse",
        strain="BALB/c nude (nu/nu)",
        total_animals=80,
        research_description=(
            "Testing the efficacy of a novel anti-cancer compound (XYZ-123) "
            "in a subcutaneous human tumor xenograft model. This compound "
            "has shown promising results in vitro and this study will "
            "determine its in vivo efficacy and optimal dosing."
        ),
        procedures=(
            "Subcutaneous implantation of 1×10^6 HCT-116 tumor cells in the "
            "right flank under isoflurane anesthesia. Once tumors reach 100mm³, "
            "animals will be randomized to treatment groups. Daily compound "
            "administration by oral gavage for 21 days. Tumor measurements "
            "with calipers twice weekly. Animals will be euthanized by CO2 "
            "when tumors reach 1500mm³ or show signs of ulceration. Final "
            "euthanasia for all remaining animals at day 28."
        ),
        study_duration="6 weeks",
        primary_endpoint="Tumor volume at day 21",
    ),
}


def main():
    parser = argparse.ArgumentParser(
        description="Generate a sample IACUC protocol",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Quick validation (no LLM calls)
    python scripts/generate_sample_protocol.py --type behavioral --quick
    
    # Generate full protocol (requires API keys)
    python scripts/generate_sample_protocol.py --type surgical --output protocol.json
    
    # Verbose output to see agent reasoning
    python scripts/generate_sample_protocol.py --type tumor --verbose
""",
    )
    
    parser.add_argument(
        "--type",
        choices=["behavioral", "surgical", "tumor"],
        default="behavioral",
        help="Type of sample protocol to generate",
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output file path (JSON format)",
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show verbose output from agents",
    )
    
    parser.add_argument(
        "--quick", "-q",
        action="store_true",
        help="Quick validation only (no LLM calls)",
    )
    
    args = parser.parse_args()
    
    # Get sample input
    protocol_input = SAMPLE_PROTOCOLS[args.type]
    
    print(f"\n{'='*60}")
    print(f"IACUC Protocol Generator")
    print(f"{'='*60}")
    print(f"\nProtocol Type: {args.type}")
    print(f"Title: {protocol_input.title}")
    print(f"PI: {protocol_input.pi_name}")
    print(f"Species: {protocol_input.species} ({protocol_input.strain})")
    print(f"Total Animals: {protocol_input.total_animals}")
    
    if args.quick:
        print(f"\n{'='*60}")
        print("QUICK VALIDATION (no LLM calls)")
        print(f"{'='*60}\n")
        
        result = quick_crew_check(protocol_input)
        
        print(f"Input Valid: {result['is_valid']}")
        
        if result['validation_errors']:
            print("\nValidation Errors:")
            for error in result['validation_errors']:
                print(f"  ✗ {error}")
        
        print("\nTask Sequence:")
        for task in result['task_sequence']:
            print(f"  {task}")
        
        print("\nAgents:")
        for agent in result['agents']:
            print(f"  • {agent}")
        
        return
    
    print(f"\n{'='*60}")
    print("GENERATING PROTOCOL (this may take several minutes)")
    print(f"{'='*60}\n")
    
    # Generate protocol
    result = generate_protocol(protocol_input, verbose=args.verbose)
    
    if result.success:
        print("\n✓ Protocol generated successfully!")
        
        # Show summary
        print(f"\nAgent Outputs:")
        for agent_name, output in result.agent_outputs.items():
            preview = output[:100] + "..." if len(output) > 100 else output
            print(f"  • {agent_name}: {preview}")
        
        # Save to file if requested
        if args.output:
            output_path = Path(args.output)
            
            output_data = {
                "success": result.success,
                "protocol_input": protocol_input.model_dump(),
                "protocol_sections": result.protocol_sections,
                "agent_outputs": result.agent_outputs,
                "errors": result.errors,
            }
            
            with open(output_path, "w") as f:
                json.dump(output_data, f, indent=2)
            
            print(f"\n✓ Protocol saved to: {output_path}")
    else:
        print("\n✗ Protocol generation failed!")
        print("\nErrors:")
        for error in result.errors:
            print(f"  ✗ {error}")
        
        sys.exit(1)


if __name__ == "__main__":
    main()
