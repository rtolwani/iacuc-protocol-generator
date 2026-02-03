#!/usr/bin/env python3
"""
Export Protocol Script.

Exports IACUC protocols to PDF or Markdown format.

Usage:
    python scripts/export_protocol.py --id PROTOCOL_ID --format pdf
    python scripts/export_protocol.py --id PROTOCOL_ID --format md
    python scripts/export_protocol.py --sample --format pdf
"""

import argparse
import sys
from datetime import date
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.protocol.schema import (
    Protocol,
    PersonnelInfo,
    AnimalInfo,
    ProcedureInfo,
    DrugInfo,
    HumaneEndpoint,
    LiteratureSearch,
    ProtocolStatus,
    USDACategory,
)
from src.protocol.export import export_to_pdf, export_to_markdown
from src.api.routes.protocols import ProtocolStorage


def create_sample_protocol() -> Protocol:
    """Create a sample complete protocol for testing exports."""
    return Protocol(
        title="Effects of Novel Compound XYZ-123 on Alzheimer's Disease Pathology in Transgenic Mouse Model",
        protocol_number="IACUC-2024-0123",
        principal_investigator=PersonnelInfo(
            name="Dr. Jane Smith",
            role="Principal Investigator",
            email="jsmith@university.edu",
            phone="555-123-4567",
            department="Department of Neuroscience",
            qualifications=["PhD in Neuroscience", "IACUC Training Certified", "Rodent Surgery Certified"],
            responsibilities=["Protocol oversight", "Data analysis", "Personnel training"],
        ),
        department="Department of Neuroscience",
        funding_sources=["NIH R01", "Alzheimer's Association"],
        funding_agency_numbers=["R01AG12345"],
        study_duration="24 months",
        lay_summary="""This research project aims to test whether a new drug called XYZ-123 can help 
slow down memory loss associated with Alzheimer's disease. We will use specially bred mice that 
develop brain changes similar to human Alzheimer's patients. These mice will receive the drug 
or a placebo, and we will test their memory using maze tests. We hope this research will help 
develop new treatments for people with Alzheimer's disease.""",
        personnel=[
            PersonnelInfo(
                name="Dr. Jane Smith",
                role="Principal Investigator",
                qualifications=["PhD", "IACUC Certified"],
            ),
            PersonnelInfo(
                name="Dr. John Doe",
                role="Co-Investigator",
                qualifications=["MD, PhD", "Rodent Surgery Certified"],
            ),
            PersonnelInfo(
                name="Sarah Johnson",
                role="Graduate Student",
                qualifications=["IACUC Training", "Behavioral Testing Certified"],
            ),
        ],
        animals=[
            AnimalInfo(
                species="Mouse",
                scientific_name="Mus musculus",
                strain="APP/PS1 transgenic",
                sex="both",
                age_range="3-6 months at study start",
                weight_range="25-35g",
                total_number=80,
                number_per_group=20,
                number_of_groups=4,
                source="Jackson Laboratory",
                vendor_name="The Jackson Laboratory",
                genetic_modification="APP/PS1 double transgenic",
                housing_requirements="Standard caging, 12h light/dark cycle",
            )
        ],
        usda_category=USDACategory.D,
        total_animals=80,
        animal_number_justification="""Power analysis using G*Power (α=0.05, power=0.80, effect size=0.5) 
indicates n=20 per group is required to detect significant differences. Four groups (vehicle control, 
low dose, medium dose, high dose) × 20 animals = 80 total mice. This represents the minimum number 
needed for statistical validity while allowing for potential attrition.""",
        scientific_objectives="""1. Determine the effect of XYZ-123 on amyloid plaque deposition
2. Evaluate cognitive function improvements using Morris Water Maze
3. Assess synaptic density and neuroinflammation markers""",
        scientific_rationale="""The APP/PS1 transgenic mouse model is well-established for Alzheimer's 
research, developing amyloid plaques and cognitive deficits similar to human patients. In vitro 
studies have shown XYZ-123 reduces amyloid aggregation by 40%. Animal models are essential to 
evaluate blood-brain barrier penetration and functional cognitive outcomes that cannot be assessed 
in cell culture systems.""",
        potential_benefits="""This research may lead to a new therapeutic approach for Alzheimer's 
disease, potentially benefiting millions of patients worldwide. The data generated will support 
an IND application for clinical trials.""",
        replacement_statement="""We have conducted extensive in vitro studies using primary neuronal 
cultures and iPSC-derived neurons to screen compound efficacy. However, assessment of cognitive 
function, blood-brain barrier penetration, and complex neuronal circuit effects require an intact 
nervous system that cannot be replicated in cell culture.""",
        reduction_statement="""The sample size was determined through rigorous power analysis to use 
the minimum number of animals needed for statistical significance. We will employ repeated measures 
within subjects where possible to reduce total animal numbers.""",
        refinement_statement="""All procedures include appropriate anesthesia and analgesia. Animals 
are housed in enriched environments with nesting material. Personnel are trained in low-stress 
handling techniques. Humane endpoints are clearly defined and monitored daily.""",
        literature_search=LiteratureSearch(
            databases_searched=["PubMed", "AWIC", "ALTEX"],
            search_date=date(2024, 1, 15),
            search_terms=["Alzheimer's", "alternatives", "in vitro", "cognitive assessment", "3Rs"],
            years_covered="2019-2024",
            results_summary="No suitable replacement alternatives identified for in vivo cognitive testing.",
        ),
        experimental_design="""Randomized, blinded, placebo-controlled study:
- Group 1: Vehicle control (n=20)
- Group 2: XYZ-123 low dose (10 mg/kg, n=20)
- Group 3: XYZ-123 medium dose (30 mg/kg, n=20)
- Group 4: XYZ-123 high dose (100 mg/kg, n=20)

Timeline: Daily oral gavage for 12 weeks, behavioral testing at weeks 4, 8, 12.""",
        statistical_methods="""Two-way repeated measures ANOVA with Tukey post-hoc tests for behavioral 
data. One-way ANOVA for histological endpoints. Significance level α=0.05. Analysis performed using 
GraphPad Prism.""",
        power_analysis="G*Power 3.1: Two-way ANOVA, effect size f=0.25, α=0.05, power=0.80, 4 groups → n=20/group",
        procedures=[
            ProcedureInfo(
                name="Oral Gavage",
                description="Daily administration of test compound or vehicle via oral gavage using curved feeding needle",
                frequency="Daily for 12 weeks",
                duration="<30 seconds per animal",
                anesthesia_required=False,
                analgesia_required=False,
                recovery_expected=True,
            ),
            ProcedureInfo(
                name="Morris Water Maze",
                description="Spatial learning and memory assessment in circular pool with hidden platform",
                frequency="5 trials per day for 5 consecutive days at weeks 4, 8, 12",
                duration="60 seconds maximum per trial",
                anesthesia_required=False,
                analgesia_required=False,
                recovery_expected=True,
            ),
        ],
        procedure_timeline="Week 1-12: Daily dosing. Week 4, 8, 12: Behavioral testing. Week 12: Terminal procedures.",
        anesthesia_protocols=[
            DrugInfo(
                drug_name="Isoflurane",
                dose="2-3% in oxygen",
                route="Inhalation",
                purpose="Anesthesia for terminal perfusion",
                frequency="Once at study end",
            ),
        ],
        analgesia_protocols=[
            DrugInfo(
                drug_name="Buprenorphine SR",
                dose="1.0 mg/kg",
                route="SC",
                purpose="Post-procedure analgesia (if any unexpected procedures needed)",
                frequency="As needed",
            ),
        ],
        monitoring_during_anesthesia="Respiratory rate, toe pinch reflex, body temperature",
        humane_endpoints=[
            HumaneEndpoint(
                criterion="Weight loss",
                measurement="Daily weighing",
                threshold=">20% loss from baseline",
                action="Euthanasia",
            ),
            HumaneEndpoint(
                criterion="Neurological signs",
                measurement="Daily observation",
                threshold="Seizures, paralysis, severe ataxia",
                action="Euthanasia",
            ),
            HumaneEndpoint(
                criterion="General condition",
                measurement="Daily health check",
                threshold="Inability to eat/drink, severe dehydration",
                action="Euthanasia",
            ),
        ],
        monitoring_schedule="Daily observation for general health, weekly detailed assessment, daily weighing during treatment period",
        responsible_person="Dr. Jane Smith and trained laboratory personnel",
        euthanasia_method="CO2 asphyxiation followed by cervical dislocation",
        euthanasia_justification="CO2 is AVMA-approved for rodents; cervical dislocation ensures death",
        secondary_method="Cervical dislocation",
        avma_compliant=True,
        hazardous_materials=[],
        biohazard_level=None,
        radiation_use=False,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Export IACUC protocol to PDF or Markdown",
    )
    
    parser.add_argument(
        "--id",
        type=str,
        help="Protocol ID to export",
    )
    
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Export a sample protocol instead of loading from storage",
    )
    
    parser.add_argument(
        "--format", "-f",
        type=str,
        choices=["pdf", "md", "markdown"],
        default="pdf",
        help="Export format (default: pdf)",
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output file path (default: protocol_<id>.<format>)",
    )
    
    parser.add_argument(
        "--institution",
        type=str,
        default="University Research Institution",
        help="Institution name for header",
    )
    
    args = parser.parse_args()
    
    if not args.id and not args.sample:
        parser.error("Either --id or --sample is required")
    
    # Load or create protocol
    if args.sample:
        protocol = create_sample_protocol()
        print("Using sample protocol")
    else:
        storage = ProtocolStorage()
        protocol = storage.load(args.id)
        if not protocol:
            print(f"Error: Protocol '{args.id}' not found", file=sys.stderr)
            sys.exit(1)
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        ext = "pdf" if args.format == "pdf" else "md"
        filename = f"protocol_{protocol.id[:8]}.{ext}"
        output_path = Path(filename)
    
    # Export
    if args.format == "pdf":
        pdf_bytes = export_to_pdf(
            protocol,
            output_path=output_path,
            institution_name=args.institution,
        )
        print(f"PDF exported to: {output_path} ({len(pdf_bytes)} bytes)")
    else:
        markdown = export_to_markdown(
            protocol,
            output_path=output_path,
            institution_name=args.institution,
        )
        print(f"Markdown exported to: {output_path} ({len(markdown)} characters)")


if __name__ == "__main__":
    main()
