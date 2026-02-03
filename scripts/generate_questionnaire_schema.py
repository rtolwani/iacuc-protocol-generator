#!/usr/bin/env python3
"""
Generate questionnaire JSON schemas.

Usage:
    python scripts/generate_questionnaire_schema.py --group basic_info
    python scripts/generate_questionnaire_schema.py --branch surgery
    python scripts/generate_questionnaire_schema.py --full
"""

import argparse
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.questionnaire.schema import ALL_QUESTION_GROUPS, get_group_by_id
from src.questionnaire.branching import QuestionnaireState, BRANCHES
from src.questionnaire.renderer import (
    render_single_group,
    render_full_questionnaire,
    render_question_group,
)


def main():
    parser = argparse.ArgumentParser(
        description="Generate questionnaire JSON schemas",
    )
    
    parser.add_argument(
        "--group", "-g",
        type=str,
        help="Render a specific question group by ID",
    )
    
    parser.add_argument(
        "--branch", "-b",
        type=str,
        help="Render a specific branch question group",
    )
    
    parser.add_argument(
        "--full", "-f",
        action="store_true",
        help="Render full questionnaire",
    )
    
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available groups and branches",
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output file (default: stdout)",
    )
    
    args = parser.parse_args()
    
    if args.list:
        print("Available Question Groups:")
        for group in ALL_QUESTION_GROUPS:
            branch_info = f" [branch: {group.branch_id}]" if group.branch_id else ""
            print(f"  - {group.id}: {group.title}{branch_info}")
        
        print("\nAvailable Branches:")
        for branch in BRANCHES:
            print(f"  - {branch.id}: {branch.name}")
        
        return
    
    result = None
    
    if args.group:
        result = render_single_group(args.group)
        if not result:
            print(f"Error: Group '{args.group}' not found", file=sys.stderr)
            sys.exit(1)
    
    elif args.branch:
        # Find the branch's question group
        branch = next((b for b in BRANCHES if b.id == args.branch), None)
        if not branch:
            print(f"Error: Branch '{args.branch}' not found", file=sys.stderr)
            sys.exit(1)
        
        result = render_single_group(branch.question_group_id)
        if not result:
            print(f"Error: Branch group '{branch.question_group_id}' not found", file=sys.stderr)
            sys.exit(1)
    
    elif args.full:
        result = render_full_questionnaire()
    
    else:
        parser.print_help()
        return
    
    # Output
    output_json = json.dumps(result, indent=2)
    
    if args.output:
        Path(args.output).write_text(output_json)
        print(f"Schema written to {args.output}", file=sys.stderr)
    else:
        print(output_json)


if __name__ == "__main__":
    main()
