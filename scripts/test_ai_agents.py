#!/usr/bin/env python3
"""
Test script to manually run AI agents on a protocol.

This script demonstrates how the CrewAI agents process a protocol.

Usage:
    python scripts/test_ai_agents.py <protocol_id>
    
Example:
    python scripts/test_ai_agents.py 6d3fdb53-5e7b-4fe7-a370-382334b40ef3
"""

import sys
import json
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.api.routes.protocols import ProtocolStorage


def test_regulatory_compliance(protocol: dict) -> dict:
    """Test regulatory compliance checking."""
    print("\n" + "=" * 60)
    print("🔍 REGULATORY ANALYST AGENT")
    print("=" * 60)
    
    issues = []
    recommendations = []
    
    # Check USDA category
    usda_category = protocol.get("usda_category", "")
    if not usda_category:
        issues.append("USDA pain category not specified")
    else:
        print(f"✓ USDA Category: {usda_category}")
    
    # Check 3Rs statements
    for rs in ["replacement_statement", "reduction_statement", "refinement_statement"]:
        value = protocol.get(rs, "")
        if not value or value.lower() in ["none", "n/a", "tbd"]:
            issues.append(f"Missing or incomplete {rs.replace('_', ' ')}")
        else:
            print(f"✓ {rs.replace('_', ' ').title()}: Present")
    
    # Check euthanasia method
    euthanasia = protocol.get("euthanasia_method", "")
    if euthanasia:
        avma_approved = ["co2", "cervical dislocation", "decapitation", "pentobarbital", 
                        "isoflurane", "ketamine", "carbon dioxide"]
        if any(method in euthanasia.lower() for method in avma_approved):
            print(f"✓ Euthanasia method ({euthanasia}): AVMA-approved")
        else:
            recommendations.append(f"Verify '{euthanasia}' is AVMA-approved for the species")
    else:
        issues.append("Euthanasia method not specified")
    
    # Check humane endpoints
    endpoints = protocol.get("humane_endpoints", [])
    if endpoints:
        print(f"✓ Humane endpoints: {len(endpoints)} defined")
    else:
        issues.append("No humane endpoints defined")
    
    print("\n📋 Issues Found:", len(issues))
    for issue in issues:
        print(f"   ⚠️  {issue}")
    
    print("\n💡 Recommendations:", len(recommendations))
    for rec in recommendations:
        print(f"   → {rec}")
    
    return {"issues": issues, "recommendations": recommendations}


def test_veterinary_review(protocol: dict) -> dict:
    """Test veterinary review of procedures."""
    print("\n" + "=" * 60)
    print("🩺 VETERINARY REVIEWER AGENT")
    print("=" * 60)
    
    findings = []
    
    # Check animals
    animals = protocol.get("animals", [])
    if animals:
        print(f"✓ Animals: {len(animals)} groups defined")
        total = sum(a.get("total_number", 0) for a in animals)
        print(f"  Total animals: {total}")
        for animal in animals:
            species = animal.get("species", "Unknown")
            strain = animal.get("strain", "")
            n = animal.get("total_number", 0)
            print(f"  - {species} {f'({strain})' if strain else ''}: n={n}")
    else:
        findings.append("No animals defined in protocol")
    
    # Check anesthesia/analgesia
    anesthesia = protocol.get("anesthesia_protocol", "")
    analgesia = protocol.get("analgesia_protocol", "")
    
    if anesthesia:
        print(f"✓ Anesthesia protocol: Present")
    else:
        findings.append("No anesthesia protocol specified")
    
    if analgesia:
        print(f"✓ Analgesia protocol: Present")
    else:
        findings.append("No analgesia protocol specified (may be required for painful procedures)")
    
    # Check monitoring
    monitoring = protocol.get("monitoring_schedule", "")
    if monitoring:
        print(f"✓ Monitoring schedule: {monitoring}")
    else:
        findings.append("No monitoring schedule defined")
    
    print("\n🔬 Veterinary Findings:", len(findings))
    for finding in findings:
        print(f"   📝 {finding}")
    
    return {"findings": findings}


def test_statistical_review(protocol: dict) -> dict:
    """Test statistical methods review."""
    print("\n" + "=" * 60)
    print("📊 STATISTICAL REVIEWER AGENT")
    print("=" * 60)
    
    issues = []
    
    # Check sample size justification
    animals = protocol.get("animals", [])
    total = sum(a.get("total_number", 0) for a in animals)
    
    print(f"Total sample size: {total}")
    
    # Check statistical methods
    stats = protocol.get("statistical_methods", "")
    if stats:
        print(f"✓ Statistical methods: {stats}")
        
        # Check for power analysis keywords
        power_keywords = ["power", "sample size", "effect size", "alpha", "beta"]
        if any(kw in stats.lower() for kw in power_keywords):
            print("  ✓ Power analysis mentioned")
        else:
            issues.append("Consider adding power analysis justification")
    else:
        issues.append("No statistical methods specified")
    
    # Check experimental design
    design = protocol.get("experimental_design", "")
    if design:
        print(f"✓ Experimental design: {design}")
    else:
        issues.append("No experimental design specified")
    
    # Simple power check
    if total > 0 and total < 6:
        issues.append(f"Sample size of {total} may be too small for statistical significance")
    elif total > 100:
        issues.append(f"Large sample size ({total}) - ensure justified to minimize animal use")
    else:
        print(f"✓ Sample size ({total}) within typical range")
    
    print("\n📈 Statistical Issues:", len(issues))
    for issue in issues:
        print(f"   ⚠️  {issue}")
    
    return {"issues": issues, "total_animals": total}


def test_lay_summary(protocol: dict) -> dict:
    """Test lay summary generation (Grade 14 level)."""
    print("\n" + "=" * 60)
    print("📝 LAY SUMMARY WRITER AGENT (Grade 14 Level)")
    print("=" * 60)
    
    summary = protocol.get("lay_summary", "")
    
    if summary:
        print(f"\nOriginal lay summary ({len(summary)} chars):")
        print(f"  \"{summary[:200]}{'...' if len(summary) > 200 else ''}\"")
        
        # In a real implementation, this would use the LLM to rewrite
        print("\n💡 The AI agent would analyze and potentially simplify this text")
        print("   to ensure it's understandable at a college reading level.")
        print("   Target: Clear, jargon-free explanation accessible to educated public.")
    else:
        print("⚠️  No lay summary provided")
    
    return {"summary_length": len(summary)}


def test_protocol_assembly(protocol: dict, all_results: dict) -> dict:
    """Test final protocol assembly."""
    print("\n" + "=" * 60)
    print("📋 PROTOCOL ASSEMBLER AGENT")
    print("=" * 60)
    
    # Calculate completeness
    required_fields = [
        "title", "principal_investigator", "department", "lay_summary",
        "scientific_objectives", "experimental_design",
        "euthanasia_method"
    ]
    
    filled = sum(1 for f in required_fields if protocol.get(f))
    completeness = filled / len(required_fields) * 100
    
    print(f"\n📊 Protocol Completeness: {completeness:.1f}%")
    print(f"   Filled: {filled}/{len(required_fields)} required fields")
    
    # Aggregate issues from all agents
    total_issues = (
        len(all_results.get("regulatory", {}).get("issues", [])) +
        len(all_results.get("veterinary", {}).get("findings", [])) +
        len(all_results.get("statistical", {}).get("issues", []))
    )
    
    print(f"\n🔍 Total Issues Found: {total_issues}")
    
    if total_issues == 0:
        print("\n✅ RECOMMENDATION: Protocol ready for committee review")
    elif total_issues <= 3:
        print("\n⚠️  RECOMMENDATION: Minor revisions needed before review")
    else:
        print("\n❌ RECOMMENDATION: Significant revisions required")
    
    return {"completeness": completeness, "total_issues": total_issues}


async def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_ai_agents.py <protocol_id>")
        print("\nAvailable protocols:")
        
        # List available protocols
        storage = ProtocolStorage()
        protocols = storage.list_all()
        for p in protocols[:10]:  # Show first 10
            print(f"  - {p.id}: {p.title} ({p.status.value})")
        
        if len(protocols) > 10:
            print(f"  ... and {len(protocols) - 10} more")
        
        sys.exit(1)
    
    protocol_id = sys.argv[1]
    
    print("=" * 60)
    print("🤖 IACUC PROTOCOL AI REVIEW SYSTEM")
    print("=" * 60)
    print(f"\nProtocol ID: {protocol_id}")
    
    # Load protocol
    storage = ProtocolStorage()
    try:
        protocol = storage.load(protocol_id)
    except Exception as e:
        print(f"❌ Error loading protocol: {e}")
        sys.exit(1)
    
    protocol_dict = protocol.model_dump()
    
    print(f"Title: {protocol.title}")
    print(f"PI: {protocol.principal_investigator.name}")
    print(f"Status: {protocol.status.value}")
    
    # Run all agents
    results = {}
    
    results["regulatory"] = test_regulatory_compliance(protocol_dict)
    results["veterinary"] = test_veterinary_review(protocol_dict)
    results["statistical"] = test_statistical_review(protocol_dict)
    results["lay_summary"] = test_lay_summary(protocol_dict)
    results["assembly"] = test_protocol_assembly(protocol_dict, results)
    
    print("\n" + "=" * 60)
    print("📋 SUMMARY")
    print("=" * 60)
    print(f"\nProtocol: {protocol.title}")
    print(f"Completeness: {results['assembly']['completeness']:.1f}%")
    print(f"Total Issues: {results['assembly']['total_issues']}")
    
    print("\n✅ AI Review Complete!")
    print("\nNote: This is a simulation. In production, the CrewAI agents")
    print("would use LLMs to provide more detailed analysis and recommendations.")


if __name__ == "__main__":
    asyncio.run(main())
