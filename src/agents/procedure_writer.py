"""
Procedure Writer Agent.

An agent that generates detailed procedure descriptions, drug administration
tables, monitoring schedules, and AVMA-compliant euthanasia methods.
"""

from typing import Optional

from crewai import Agent, Task, Crew
from pydantic import BaseModel, Field

from src.agents.llm import get_llm
from src.tools.formulary_tool import FormularyLookupTool, DrugFormulary
from src.tools.rag_tools import RegulatorySearchTool, EuthanasiaMethodTool


class DrugAdministrationEntry(BaseModel):
    """Entry in a drug administration table."""
    
    drug_name: str = Field(description="Name of drug")
    dose: str = Field(description="Dose with units")
    route: str = Field(description="Administration route")
    frequency: str = Field(description="Dosing frequency")
    timing: str = Field(description="When administered (e.g., pre-op, post-op)")
    purpose: str = Field(description="Purpose of administration")


class MonitoringScheduleEntry(BaseModel):
    """Entry in a monitoring schedule."""
    
    time_point: str = Field(description="When to monitor")
    parameters: list[str] = Field(description="What to monitor")
    criteria: str = Field(description="Acceptable/concerning findings")
    action_if_abnormal: str = Field(description="What to do if abnormal")


class ProcedureStep(BaseModel):
    """A step in a procedure description."""
    
    step_number: int = Field(description="Step number")
    description: str = Field(description="Step description")
    duration: Optional[str] = Field(default=None, description="Expected duration")
    notes: Optional[str] = Field(default=None, description="Additional notes")


class EuthanasiaMethod(BaseModel):
    """AVMA-compliant euthanasia method."""
    
    primary_method: str = Field(description="Primary euthanasia method")
    secondary_method: str = Field(description="Method to confirm death")
    species: str = Field(description="Species this applies to")
    classification: str = Field(description="AVMA classification (acceptable, conditionally acceptable)")
    notes: str = Field(default="", description="Additional considerations")


# AVMA Euthanasia Guidelines by species
AVMA_EUTHANASIA_METHODS = {
    "mouse": {
        "acceptable": [
            EuthanasiaMethod(
                primary_method="CO2 inhalation (gradual fill, 30-70% chamber volume/min)",
                secondary_method="Cervical dislocation or bilateral thoracotomy",
                species="mouse",
                classification="Acceptable",
                notes="Use compressed gas, not dry ice. Unconsciousness in 2-3 minutes.",
            ),
            EuthanasiaMethod(
                primary_method="Pentobarbital sodium (150-200 mg/kg IP)",
                secondary_method="Bilateral thoracotomy or decapitation",
                species="mouse",
                classification="Acceptable",
                notes="Preferred for tissue collection. DEA Schedule II.",
            ),
        ],
        "conditionally_acceptable": [
            EuthanasiaMethod(
                primary_method="Cervical dislocation (trained personnel only)",
                secondary_method="Ensure cessation of heartbeat",
                species="mouse",
                classification="Conditionally Acceptable",
                notes="Only for mice <200g. Requires training and proficiency.",
            ),
            EuthanasiaMethod(
                primary_method="Isoflurane overdose (5% until respiratory arrest)",
                secondary_method="Cervical dislocation or thoracotomy",
                species="mouse",
                classification="Conditionally Acceptable",
                notes="Requires scavenging system. Good for imaging studies.",
            ),
        ],
    },
    "rat": {
        "acceptable": [
            EuthanasiaMethod(
                primary_method="CO2 inhalation (gradual fill, 30-70% chamber volume/min)",
                secondary_method="Bilateral thoracotomy or decapitation",
                species="rat",
                classification="Acceptable",
                notes="Use compressed gas. May require longer exposure than mice.",
            ),
            EuthanasiaMethod(
                primary_method="Pentobarbital sodium (150-200 mg/kg IP)",
                secondary_method="Bilateral thoracotomy",
                species="rat",
                classification="Acceptable",
                notes="Preferred for tissue collection. DEA Schedule II.",
            ),
        ],
        "conditionally_acceptable": [
            EuthanasiaMethod(
                primary_method="Isoflurane overdose (5% until respiratory arrest)",
                secondary_method="Thoracotomy or exsanguination",
                species="rat",
                classification="Conditionally Acceptable",
                notes="Requires proper scavenging.",
            ),
        ],
    },
    "rabbit": {
        "acceptable": [
            EuthanasiaMethod(
                primary_method="Pentobarbital sodium (100-150 mg/kg IV)",
                secondary_method="Bilateral thoracotomy",
                species="rabbit",
                classification="Acceptable",
                notes="IV route strongly preferred. DEA Schedule II.",
            ),
        ],
        "conditionally_acceptable": [
            EuthanasiaMethod(
                primary_method="CO2 inhalation (with sedation)",
                secondary_method="Bilateral thoracotomy or exsanguination",
                species="rabbit",
                classification="Conditionally Acceptable",
                notes="Pre-sedate due to breath-holding. Less preferred.",
            ),
        ],
    },
}


def generate_drug_table(
    species: str,
    procedure_type: str,
) -> list[DrugAdministrationEntry]:
    """
    Generate a drug administration table for a procedure type.
    
    Args:
        species: Species being used
        procedure_type: Type of procedure (surgery, behavioral, etc.)
        
    Returns:
        List of drug administration entries.
    """
    formulary = DrugFormulary()
    entries = []
    
    if "surgery" in procedure_type.lower():
        # Get species-specific dosing
        ketamine = formulary.lookup_drug("ketamine", species)
        xylazine = formulary.lookup_drug("xylazine", species)
        buprenorphine = formulary.lookup_drug("buprenorphine", species)
        carprofen = formulary.lookup_drug("carprofen", species)
        
        if ketamine.species_specific:
            entries.append(DrugAdministrationEntry(
                drug_name="Ketamine",
                dose=ketamine.drug_info.dose_range,
                route=ketamine.drug_info.route,
                frequency="Once",
                timing="Pre-operative induction",
                purpose="Anesthesia induction",
            ))
        
        if xylazine.species_specific:
            entries.append(DrugAdministrationEntry(
                drug_name="Xylazine",
                dose=xylazine.drug_info.dose_range,
                route=xylazine.drug_info.route,
                frequency="Once",
                timing="Pre-operative with ketamine",
                purpose="Sedation/muscle relaxation",
            ))
        
        if buprenorphine.species_specific:
            entries.append(DrugAdministrationEntry(
                drug_name="Buprenorphine",
                dose=buprenorphine.drug_info.dose_range,
                route=buprenorphine.drug_info.route,
                frequency="Every 8-12 hours",
                timing="Pre-operative and post-operative",
                purpose="Analgesia",
            ))
        
        if carprofen.species_specific:
            entries.append(DrugAdministrationEntry(
                drug_name="Carprofen",
                dose=carprofen.drug_info.dose_range,
                route=carprofen.drug_info.route,
                frequency="Once daily",
                timing="Pre-operative and for 48-72 hours post-op",
                purpose="Anti-inflammatory/analgesia",
            ))
    
    return entries


def generate_monitoring_schedule(
    procedure_type: str,
) -> list[MonitoringScheduleEntry]:
    """
    Generate a monitoring schedule for a procedure type.
    
    Args:
        procedure_type: Type of procedure
        
    Returns:
        List of monitoring schedule entries.
    """
    entries = []
    
    if "surgery" in procedure_type.lower():
        entries = [
            MonitoringScheduleEntry(
                time_point="During anesthesia (every 5 min)",
                parameters=["Respiratory rate", "Heart rate", "Toe pinch reflex", "Body temperature"],
                criteria="RR 40-60/min, HR 300-600/min (mice), Temp >35°C",
                action_if_abnormal="Adjust anesthesia depth, provide supplemental heat",
            ),
            MonitoringScheduleEntry(
                time_point="Recovery (every 15 min until ambulatory)",
                parameters=["Righting reflex", "Respiratory pattern", "Body temperature"],
                criteria="Full recovery within 1 hour",
                action_if_abnormal="Provide supportive care, contact veterinarian if prolonged",
            ),
            MonitoringScheduleEntry(
                time_point="Post-operative Day 1-3 (twice daily)",
                parameters=["Incision site", "Body weight", "Food/water intake", "Activity level", "Pain score"],
                criteria="No signs of infection, <10% weight loss, normal activity",
                action_if_abnormal="Additional analgesia, veterinary consultation",
            ),
            MonitoringScheduleEntry(
                time_point="Post-operative Day 4-7 (daily)",
                parameters=["Incision healing", "Body weight", "General condition"],
                criteria="Healing wound, weight stable or increasing",
                action_if_abnormal="Veterinary consultation",
            ),
        ]
    
    elif "tumor" in procedure_type.lower():
        entries = [
            MonitoringScheduleEntry(
                time_point="Pre-implantation baseline",
                parameters=["Body weight", "Body condition score"],
                criteria="Healthy baseline established",
                action_if_abnormal="Exclude from study",
            ),
            MonitoringScheduleEntry(
                time_point="Twice weekly post-implantation",
                parameters=["Tumor dimensions", "Body weight", "Body condition score"],
                criteria="Tumor <2cm, weight loss <15%",
                action_if_abnormal="Increase monitoring, consider euthanasia",
            ),
            MonitoringScheduleEntry(
                time_point="Daily when tumors palpable",
                parameters=["Tumor size", "Ulceration", "Mobility", "Feeding behavior"],
                criteria="No ulceration, normal mobility and feeding",
                action_if_abnormal="Immediate euthanasia if humane endpoints met",
            ),
        ]
    
    else:
        # General monitoring
        entries = [
            MonitoringScheduleEntry(
                time_point="Daily during study",
                parameters=["General health", "Body weight (weekly)", "Food/water consumption"],
                criteria="Normal appearance and behavior",
                action_if_abnormal="Veterinary consultation",
            ),
        ]
    
    return entries


def generate_procedure_steps(
    procedure_type: str,
    species: str,
) -> list[ProcedureStep]:
    """
    Generate step-by-step procedure description.
    
    Args:
        procedure_type: Type of procedure
        species: Species being used
        
    Returns:
        List of procedure steps.
    """
    steps = []
    
    if "surgery" in procedure_type.lower():
        steps = [
            ProcedureStep(
                step_number=1,
                description="Weigh animal and record baseline weight",
                duration="1 minute",
            ),
            ProcedureStep(
                step_number=2,
                description="Administer pre-operative analgesia (buprenorphine and/or carprofen)",
                duration="1 minute",
                notes="Allow 30-60 minutes for onset before surgery",
            ),
            ProcedureStep(
                step_number=3,
                description="Induce anesthesia with ketamine/xylazine or isoflurane",
                duration="5-10 minutes",
            ),
            ProcedureStep(
                step_number=4,
                description="Confirm adequate anesthesia depth (loss of toe pinch reflex)",
                duration="2 minutes",
            ),
            ProcedureStep(
                step_number=5,
                description="Apply ophthalmic ointment to prevent corneal drying",
                duration="30 seconds",
            ),
            ProcedureStep(
                step_number=6,
                description="Shave and prepare surgical site with alternating betadine and alcohol scrubs",
                duration="2-3 minutes",
            ),
            ProcedureStep(
                step_number=7,
                description="Position animal on warming pad and drape surgical field",
                duration="1 minute",
            ),
            ProcedureStep(
                step_number=8,
                description="Perform surgical procedure using aseptic technique",
                duration="Variable",
                notes="Describe specific surgical steps here",
            ),
            ProcedureStep(
                step_number=9,
                description="Close incision with appropriate suture material or wound clips",
                duration="5-10 minutes",
            ),
            ProcedureStep(
                step_number=10,
                description="Administer atipamezole if using alpha-2 agonist (optional)",
                duration="1 minute",
            ),
            ProcedureStep(
                step_number=11,
                description="Place animal in recovery cage on warming pad, monitor until ambulatory",
                duration="30-60 minutes",
            ),
            ProcedureStep(
                step_number=12,
                description="Return to housing when fully recovered; provide softened food and hydration gel",
                duration="N/A",
            ),
        ]
    
    return steps


def get_euthanasia_methods(species: str) -> list[EuthanasiaMethod]:
    """
    Get AVMA-approved euthanasia methods for a species.
    
    Args:
        species: Species name
        
    Returns:
        List of acceptable euthanasia methods.
    """
    species_lower = species.lower()
    
    if species_lower in AVMA_EUTHANASIA_METHODS:
        methods = AVMA_EUTHANASIA_METHODS[species_lower]
        return methods.get("acceptable", []) + methods.get("conditionally_acceptable", [])
    
    # Default methods for unspecified species
    return [
        EuthanasiaMethod(
            primary_method="Pentobarbital sodium (overdose)",
            secondary_method="Method to confirm death (thoracotomy, exsanguination)",
            species=species,
            classification="Acceptable",
            notes="Consult AVMA Guidelines for species-specific dosing",
        ),
    ]


def create_procedure_writer_agent() -> Agent:
    """
    Create a Procedure Writer agent.
    
    This agent:
    - Generates step-by-step procedures
    - Creates drug administration tables
    - Develops monitoring schedules
    - Specifies AVMA-compliant euthanasia methods
    
    Returns:
        Configured CrewAI Agent instance.
    """
    llm = get_llm()
    formulary_tool = FormularyLookupTool()
    rag_tool = RegulatorySearchTool()
    euthanasia_tool = EuthanasiaMethodTool()
    
    return Agent(
        role="Procedure Writer",
        goal=(
            "Generate comprehensive, detailed procedure descriptions for IACUC "
            "protocols. Create clear step-by-step procedures, drug administration "
            "tables with species-specific dosing, monitoring schedules, and "
            "AVMA-compliant euthanasia methods."
        ),
        backstory=(
            "You are an experienced research technician and protocol writer with "
            "extensive hands-on experience in laboratory animal procedures. You've "
            "performed thousands of surgeries and procedures across multiple species "
            "and have trained countless researchers. You understand the importance "
            "of clear, detailed protocols that can be followed by researchers with "
            "varying experience levels. You're meticulous about drug dosing, "
            "monitoring requirements, and ensuring protocols meet regulatory "
            "standards."
        ),
        llm=llm,
        tools=[formulary_tool, rag_tool, euthanasia_tool],
        verbose=False,
        allow_delegation=False,
    )


def create_procedure_writing_task(
    agent: Agent,
    species: str,
    procedure_description: str,
    study_duration: Optional[str] = None,
) -> Task:
    """
    Create a procedure writing task.
    
    Args:
        agent: The Procedure Writer agent
        species: Species being used
        procedure_description: Brief description of procedures
        study_duration: Optional study duration
        
    Returns:
        Configured CrewAI Task instance.
    """
    duration_str = f"\nSTUDY DURATION: {study_duration}" if study_duration else ""
    
    return Task(
        description=f"""
Generate detailed procedure documentation for this IACUC protocol:

SPECIES: {species}
PROCEDURES: {procedure_description}{duration_str}

Your documentation must include:

1. STEP-BY-STEP PROCEDURES:
   - Numbered steps with clear descriptions
   - Estimated duration for each step
   - Critical technique notes where needed

2. DRUG ADMINISTRATION TABLE:
   - Use the formulary_lookup tool for species-specific dosing
   - Include all anesthetics, analgesics, and other drugs
   - Specify dose, route, frequency, and timing

3. MONITORING SCHEDULE:
   - Pre-procedure baseline assessments
   - Intra-procedure monitoring points
   - Post-procedure follow-up schedule
   - Specific parameters to monitor at each time point

4. EUTHANASIA METHODS:
   - Search regulatory guidance for AVMA-approved methods
   - Specify primary method with details
   - Specify secondary confirmation method
   - Note any species-specific considerations

Provide complete, detailed documentation that could be followed by a trained technician.
""",
        expected_output=(
            "Comprehensive procedure documentation including step-by-step procedures, "
            "drug administration table, monitoring schedule, and euthanasia methods."
        ),
        agent=agent,
    )


def write_procedure_documentation(
    species: str,
    procedure_description: str,
    study_duration: Optional[str] = None,
    verbose: bool = False,
) -> dict:
    """
    Generate procedure documentation.
    
    Main entry point for procedure writing.
    
    Args:
        species: Species being used
        procedure_description: Brief description of procedures
        study_duration: Optional study duration
        verbose: Whether to show agent reasoning
        
    Returns:
        Dictionary with procedure documentation.
    """
    # Create agent and task
    agent = create_procedure_writer_agent()
    if verbose:
        agent.verbose = True
    
    task = create_procedure_writing_task(
        agent=agent,
        species=species,
        procedure_description=procedure_description,
        study_duration=study_duration,
    )
    
    crew = Crew(
        agents=[agent],
        tasks=[task],
        verbose=verbose,
    )
    
    # Run the writing
    agent_result = crew.kickoff()
    
    # Get quick assessments
    drug_table = generate_drug_table(species, procedure_description)
    monitoring = generate_monitoring_schedule(procedure_description)
    steps = generate_procedure_steps(procedure_description, species)
    euthanasia = get_euthanasia_methods(species)
    
    return {
        "species": species,
        "procedure_description": procedure_description,
        "procedure_steps": [s.model_dump() for s in steps],
        "drug_table": [d.model_dump() for d in drug_table],
        "monitoring_schedule": [m.model_dump() for m in monitoring],
        "euthanasia_methods": [e.model_dump() for e in euthanasia],
        "detailed_documentation": str(agent_result),
    }


# Quick generation without LLM
def quick_procedure_generation(
    species: str,
    procedure_description: str,
) -> dict:
    """
    Quick procedure generation without LLM calls.
    
    Args:
        species: Species being used
        procedure_description: Brief description of procedures
        
    Returns:
        Dictionary with quick procedure documentation.
    """
    return {
        "species": species,
        "procedure_description": procedure_description,
        "procedure_steps": [s.model_dump() for s in generate_procedure_steps(procedure_description, species)],
        "drug_table": [d.model_dump() for d in generate_drug_table(species, procedure_description)],
        "monitoring_schedule": [m.model_dump() for m in generate_monitoring_schedule(procedure_description)],
        "euthanasia_methods": [e.model_dump() for e in get_euthanasia_methods(species)],
    }


# Export key items
__all__ = [
    "create_procedure_writer_agent",
    "create_procedure_writing_task",
    "write_procedure_documentation",
    "quick_procedure_generation",
    "generate_drug_table",
    "generate_monitoring_schedule",
    "generate_procedure_steps",
    "get_euthanasia_methods",
    "DrugAdministrationEntry",
    "MonitoringScheduleEntry",
    "ProcedureStep",
    "EuthanasiaMethod",
    "AVMA_EUTHANASIA_METHODS",
]
