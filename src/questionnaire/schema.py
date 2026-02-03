"""
Questionnaire Schema Definitions.

Defines question types, structures, and all questions for IACUC protocols.
"""

from enum import Enum
from typing import Optional, Any

from pydantic import BaseModel, Field


class QuestionType(str, Enum):
    """Types of questions supported by the questionnaire."""
    
    TEXT = "text"  # Free text input
    TEXTAREA = "textarea"  # Multi-line text input
    NUMBER = "number"  # Numeric input
    SINGLE_SELECT = "single_select"  # Radio buttons / dropdown
    MULTI_SELECT = "multi_select"  # Checkboxes
    DATE = "date"  # Date picker
    YES_NO = "yes_no"  # Boolean yes/no
    FILE = "file"  # File upload


class Option(BaseModel):
    """An option for select-type questions."""
    
    value: str = Field(description="Option value/ID")
    label: str = Field(description="Display label")
    help_text: Optional[str] = Field(default=None, description="Tooltip/help text")
    triggers_branch: Optional[str] = Field(default=None, description="Branch ID to trigger")


class ValidationRule(BaseModel):
    """Validation rule for a question."""
    
    rule_type: str = Field(description="Type: required, min, max, pattern, etc.")
    value: Any = Field(description="Rule value")
    message: str = Field(description="Error message if validation fails")


class Question(BaseModel):
    """A single question in the questionnaire."""
    
    id: str = Field(description="Unique question identifier")
    question_type: QuestionType = Field(description="Type of question")
    label: str = Field(description="Question text")
    help_text: Optional[str] = Field(default=None, description="Help/guidance text")
    regulatory_reference: Optional[str] = Field(default=None, description="Regulatory citation")
    required: bool = Field(default=True, description="Whether answer is required")
    options: list[Option] = Field(default_factory=list, description="Options for select types")
    validation: list[ValidationRule] = Field(default_factory=list, description="Validation rules")
    default_value: Optional[Any] = Field(default=None, description="Default value")
    placeholder: Optional[str] = Field(default=None, description="Placeholder text")
    depends_on: Optional[str] = Field(default=None, description="Question ID this depends on")
    show_when: Optional[dict] = Field(default=None, description="Condition to show question")
    order: int = Field(default=0, description="Display order")


class QuestionGroup(BaseModel):
    """A group of related questions."""
    
    id: str = Field(description="Unique group identifier")
    title: str = Field(description="Group title")
    description: Optional[str] = Field(default=None, description="Group description")
    questions: list[Question] = Field(default_factory=list, description="Questions in group")
    order: int = Field(default=0, description="Display order")
    branch_id: Optional[str] = Field(default=None, description="Branch this group belongs to")


# ============================================================================
# BASIC INFO QUESTIONS
# ============================================================================

BASIC_INFO_QUESTIONS = QuestionGroup(
    id="basic_info",
    title="Basic Protocol Information",
    description="General information about your research project",
    order=1,
    questions=[
        Question(
            id="protocol_title",
            question_type=QuestionType.TEXT,
            label="Protocol Title",
            help_text="A descriptive title for your research project",
            required=True,
            placeholder="e.g., Effects of Novel Compound on Disease Model",
            validation=[
                ValidationRule(
                    rule_type="min_length",
                    value=10,
                    message="Title must be at least 10 characters",
                ),
                ValidationRule(
                    rule_type="max_length",
                    value=200,
                    message="Title must not exceed 200 characters",
                ),
            ],
            order=1,
        ),
        Question(
            id="pi_name",
            question_type=QuestionType.TEXT,
            label="Principal Investigator Name",
            help_text="Full name of the PI responsible for this protocol",
            required=True,
            placeholder="e.g., Dr. Jane Smith",
            order=2,
        ),
        Question(
            id="pi_email",
            question_type=QuestionType.TEXT,
            label="PI Email Address",
            required=True,
            placeholder="e.g., jsmith@university.edu",
            validation=[
                ValidationRule(
                    rule_type="pattern",
                    value=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                    message="Please enter a valid email address",
                ),
            ],
            order=3,
        ),
        Question(
            id="department",
            question_type=QuestionType.TEXT,
            label="Department/Division",
            required=True,
            placeholder="e.g., Department of Neuroscience",
            order=4,
        ),
        Question(
            id="funding_source",
            question_type=QuestionType.MULTI_SELECT,
            label="Funding Source(s)",
            help_text="Select all that apply",
            required=True,
            options=[
                Option(value="nih", label="NIH"),
                Option(value="nsf", label="NSF"),
                Option(value="dod", label="DoD"),
                Option(value="industry", label="Industry/Pharma"),
                Option(value="foundation", label="Foundation/Non-profit"),
                Option(value="internal", label="Internal/Institutional"),
                Option(value="other", label="Other"),
            ],
            order=5,
        ),
        Question(
            id="study_duration",
            question_type=QuestionType.TEXT,
            label="Estimated Study Duration",
            help_text="How long do you expect the study to last?",
            required=True,
            placeholder="e.g., 12 months",
            order=6,
        ),
        Question(
            id="research_description",
            question_type=QuestionType.TEXTAREA,
            label="Research Objective Summary",
            help_text="Briefly describe the purpose and objectives of your research",
            regulatory_reference="PHS Policy IV.D.1.a",
            required=True,
            placeholder="Describe the scientific questions you are addressing...",
            validation=[
                ValidationRule(
                    rule_type="min_length",
                    value=100,
                    message="Please provide at least 100 characters",
                ),
            ],
            order=7,
        ),
    ],
)


# ============================================================================
# SPECIES QUESTIONS
# ============================================================================

SPECIES_QUESTIONS = QuestionGroup(
    id="species",
    title="Species and Animal Information",
    description="Information about the animals to be used",
    order=2,
    questions=[
        Question(
            id="species",
            question_type=QuestionType.SINGLE_SELECT,
            label="Species",
            help_text="Select the primary species to be used",
            regulatory_reference="AWA §2132(g); PHS Policy IV.A.1",
            required=True,
            options=[
                Option(value="mouse", label="Mouse", triggers_branch="mouse_branch"),
                Option(value="rat", label="Rat", triggers_branch="rat_branch"),
                Option(value="rabbit", label="Rabbit", triggers_branch="usda_covered_branch"),
                Option(value="guinea_pig", label="Guinea Pig", triggers_branch="usda_covered_branch"),
                Option(value="hamster", label="Hamster", triggers_branch="usda_covered_branch"),
                Option(value="dog", label="Dog", triggers_branch="usda_covered_branch"),
                Option(value="cat", label="Cat", triggers_branch="usda_covered_branch"),
                Option(value="pig", label="Pig/Swine", triggers_branch="usda_covered_branch"),
                Option(value="sheep", label="Sheep", triggers_branch="usda_covered_branch"),
                Option(value="primate", label="Non-Human Primate", triggers_branch="primate_branch"),
                Option(value="zebrafish", label="Zebrafish", triggers_branch="fish_branch"),
                Option(value="other_fish", label="Other Fish", triggers_branch="fish_branch"),
                Option(value="other", label="Other (specify)"),
            ],
            order=1,
        ),
        Question(
            id="strain",
            question_type=QuestionType.TEXT,
            label="Strain/Stock",
            help_text="Specify the strain, stock, or breed",
            required=True,
            placeholder="e.g., C57BL/6J, Sprague Dawley",
            order=2,
        ),
        Question(
            id="genetic_modification",
            question_type=QuestionType.YES_NO,
            label="Are the animals genetically modified?",
            help_text="Includes transgenic, knockout, knockin, etc.",
            required=True,
            order=3,
        ),
        Question(
            id="genetic_modification_details",
            question_type=QuestionType.TEXTAREA,
            label="Genetic Modification Details",
            help_text="Describe the genetic modification",
            required=False,
            depends_on="genetic_modification",
            show_when={"genetic_modification": True},
            order=4,
        ),
        Question(
            id="sex",
            question_type=QuestionType.SINGLE_SELECT,
            label="Sex of Animals",
            required=True,
            options=[
                Option(value="male", label="Male only"),
                Option(value="female", label="Female only"),
                Option(value="both", label="Both sexes"),
            ],
            order=5,
        ),
        Question(
            id="age_weight",
            question_type=QuestionType.TEXT,
            label="Age/Weight Range",
            help_text="Specify age range or weight range at study start",
            required=True,
            placeholder="e.g., 8-12 weeks old, 20-25g",
            order=6,
        ),
        Question(
            id="animal_source",
            question_type=QuestionType.SINGLE_SELECT,
            label="Animal Source",
            required=True,
            options=[
                Option(value="commercial", label="Commercial vendor"),
                Option(value="institutional_breeding", label="Institutional breeding colony"),
                Option(value="collaborator", label="Transfer from collaborator"),
                Option(value="wild_caught", label="Wild-caught", triggers_branch="wildlife_branch"),
                Option(value="other", label="Other (specify)"),
            ],
            order=7,
        ),
        Question(
            id="vendor_name",
            question_type=QuestionType.TEXT,
            label="Vendor/Source Name",
            required=False,
            depends_on="animal_source",
            show_when={"animal_source": "commercial"},
            placeholder="e.g., Jackson Laboratory, Charles River",
            order=8,
        ),
        Question(
            id="total_animals",
            question_type=QuestionType.NUMBER,
            label="Total Number of Animals Requested",
            help_text="Total animals needed for all experiments over protocol period",
            regulatory_reference="PHS Policy IV.D.1.a - requires justification",
            required=True,
            validation=[
                ValidationRule(
                    rule_type="min",
                    value=1,
                    message="At least 1 animal is required",
                ),
            ],
            order=9,
        ),
        Question(
            id="number_justification",
            question_type=QuestionType.TEXTAREA,
            label="Justification for Animal Numbers",
            help_text="Explain how you determined the number of animals needed",
            regulatory_reference="Guide Chapter 2; PHS Policy IV.C.1.a",
            required=True,
            placeholder="Include power analysis or other statistical justification...",
            order=10,
        ),
    ],
)


# ============================================================================
# PROCEDURE QUESTIONS
# ============================================================================

PROCEDURE_QUESTIONS = QuestionGroup(
    id="procedures",
    title="Experimental Procedures",
    description="Details about procedures to be performed",
    order=3,
    questions=[
        Question(
            id="procedure_types",
            question_type=QuestionType.MULTI_SELECT,
            label="Types of Procedures",
            help_text="Select all procedures that will be performed",
            required=True,
            options=[
                Option(
                    value="survival_surgery",
                    label="Survival Surgery",
                    triggers_branch="surgery_branch",
                    help_text="Surgery where animal recovers from anesthesia",
                ),
                Option(
                    value="non_survival_surgery",
                    label="Non-Survival (Terminal) Surgery",
                    triggers_branch="terminal_surgery_branch",
                ),
                Option(
                    value="injections",
                    label="Injections (IP, IV, SC, IM)",
                    triggers_branch="injection_branch",
                ),
                Option(
                    value="blood_collection",
                    label="Blood Collection",
                    triggers_branch="blood_branch",
                ),
                Option(
                    value="behavioral_testing",
                    label="Behavioral Testing",
                    triggers_branch="behavior_branch",
                ),
                Option(
                    value="imaging",
                    label="In Vivo Imaging (MRI, PET, etc.)",
                    triggers_branch="imaging_branch",
                ),
                Option(
                    value="tumor_implantation",
                    label="Tumor Implantation/Cancer Studies",
                    triggers_branch="tumor_branch",
                ),
                Option(
                    value="food_water_restriction",
                    label="Food/Water Restriction",
                    triggers_branch="restriction_branch",
                ),
                Option(
                    value="breeding",
                    label="Breeding/Colony Maintenance",
                    triggers_branch="breeding_branch",
                ),
                Option(
                    value="tissue_collection",
                    label="Tissue Collection (post-mortem)",
                ),
                Option(
                    value="other",
                    label="Other (describe in procedures)",
                ),
            ],
            order=1,
        ),
        Question(
            id="procedure_description",
            question_type=QuestionType.TEXTAREA,
            label="Detailed Procedure Description",
            help_text="Describe all procedures in detail, including timing and frequency",
            regulatory_reference="PHS Policy IV.D.1.b",
            required=True,
            placeholder="Provide step-by-step description of all procedures...",
            validation=[
                ValidationRule(
                    rule_type="min_length",
                    value=200,
                    message="Please provide at least 200 characters",
                ),
            ],
            order=2,
        ),
        Question(
            id="pain_category",
            question_type=QuestionType.SINGLE_SELECT,
            label="USDA Pain Category",
            help_text="Select the highest pain category that applies",
            regulatory_reference="AWA §2143(a)(3)(C); 9 CFR 2.36",
            required=True,
            options=[
                Option(
                    value="B",
                    label="Category B - Breeding, conditioning, holding",
                    help_text="Animals used for breeding or held but not used in research",
                ),
                Option(
                    value="C",
                    label="Category C - No pain or minimal pain",
                    help_text="Procedures causing no or momentary pain/distress",
                ),
                Option(
                    value="D",
                    label="Category D - Pain relieved by anesthesia/analgesia",
                    help_text="Procedures with pain/distress appropriately relieved",
                    triggers_branch="pain_management_branch",
                ),
                Option(
                    value="E",
                    label="Category E - Pain NOT relieved",
                    help_text="Procedures with pain/distress not relieved (requires scientific justification)",
                    triggers_branch="category_e_branch",
                ),
            ],
            order=3,
        ),
        Question(
            id="anesthesia_used",
            question_type=QuestionType.YES_NO,
            label="Will anesthesia be used?",
            required=True,
            order=4,
        ),
        Question(
            id="anesthesia_method",
            question_type=QuestionType.SINGLE_SELECT,
            label="Primary Anesthesia Method",
            required=False,
            depends_on="anesthesia_used",
            show_when={"anesthesia_used": True},
            options=[
                Option(value="isoflurane", label="Isoflurane (inhalation)"),
                Option(value="ketamine_xylazine", label="Ketamine/Xylazine (injection)"),
                Option(value="pentobarbital", label="Pentobarbital"),
                Option(value="other_injectable", label="Other injectable"),
                Option(value="other_inhalant", label="Other inhalant"),
            ],
            order=5,
        ),
        Question(
            id="analgesia_used",
            question_type=QuestionType.YES_NO,
            label="Will analgesia (pain relief) be provided?",
            required=True,
            order=6,
        ),
        Question(
            id="analgesia_method",
            question_type=QuestionType.MULTI_SELECT,
            label="Analgesia Method(s)",
            required=False,
            depends_on="analgesia_used",
            show_when={"analgesia_used": True},
            options=[
                Option(value="buprenorphine", label="Buprenorphine"),
                Option(value="carprofen", label="Carprofen (Rimadyl)"),
                Option(value="meloxicam", label="Meloxicam"),
                Option(value="ketoprofen", label="Ketoprofen"),
                Option(value="local_anesthetic", label="Local anesthetic (lidocaine, bupivacaine)"),
                Option(value="other", label="Other"),
            ],
            order=7,
        ),
        Question(
            id="euthanasia_method",
            question_type=QuestionType.SINGLE_SELECT,
            label="Primary Euthanasia Method",
            help_text="Select the primary method for euthanasia",
            regulatory_reference="AVMA Guidelines for Euthanasia 2020",
            required=True,
            options=[
                Option(value="co2", label="CO2 inhalation"),
                Option(value="co2_cervical", label="CO2 followed by cervical dislocation"),
                Option(value="pentobarbital_overdose", label="Pentobarbital overdose"),
                Option(value="decapitation", label="Decapitation"),
                Option(value="cervical_dislocation", label="Cervical dislocation"),
                Option(value="exsanguination", label="Exsanguination under anesthesia"),
                Option(value="other", label="Other (describe)"),
            ],
            order=8,
        ),
        Question(
            id="humane_endpoints",
            question_type=QuestionType.TEXTAREA,
            label="Humane Endpoints",
            help_text="Describe criteria for early euthanasia to prevent suffering",
            regulatory_reference="Guide Chapter 2",
            required=True,
            placeholder="e.g., >20% weight loss, tumor >2cm, inability to eat/drink...",
            order=9,
        ),
    ],
)


# ============================================================================
# ADDITIONAL QUESTION GROUPS
# ============================================================================

SURGERY_QUESTIONS = QuestionGroup(
    id="surgery_branch",
    title="Surgical Procedures",
    description="Details about surgical procedures",
    order=4,
    branch_id="surgery_branch",
    questions=[
        Question(
            id="surgery_type",
            question_type=QuestionType.SINGLE_SELECT,
            label="Surgery Classification",
            required=True,
            options=[
                Option(value="minor", label="Minor surgery"),
                Option(value="major", label="Major surgery"),
            ],
            order=1,
        ),
        Question(
            id="multiple_surgeries",
            question_type=QuestionType.YES_NO,
            label="Will animals undergo multiple survival surgeries?",
            regulatory_reference="Guide Chapter 2; requires scientific justification",
            required=True,
            order=2,
        ),
        Question(
            id="multiple_surgery_justification",
            question_type=QuestionType.TEXTAREA,
            label="Justification for Multiple Surgeries",
            required=False,
            depends_on="multiple_surgeries",
            show_when={"multiple_surgeries": True},
            order=3,
        ),
        Question(
            id="sterile_technique",
            question_type=QuestionType.YES_NO,
            label="Will aseptic technique be used?",
            regulatory_reference="Guide Chapter 2 - required for survival surgery",
            required=True,
            order=4,
        ),
        Question(
            id="post_op_monitoring",
            question_type=QuestionType.TEXTAREA,
            label="Post-operative Monitoring Plan",
            help_text="Describe frequency and criteria for monitoring",
            required=True,
            placeholder="e.g., Monitor every 15 min until sternal, then daily for 7 days...",
            order=5,
        ),
    ],
)

TUMOR_QUESTIONS = QuestionGroup(
    id="tumor_branch",
    title="Tumor/Cancer Studies",
    description="Details about tumor implantation studies",
    order=5,
    branch_id="tumor_branch",
    questions=[
        Question(
            id="tumor_type",
            question_type=QuestionType.SINGLE_SELECT,
            label="Tumor Model Type",
            required=True,
            options=[
                Option(value="subcutaneous", label="Subcutaneous xenograft"),
                Option(value="orthotopic", label="Orthotopic implantation"),
                Option(value="metastatic", label="Metastatic model"),
                Option(value="spontaneous", label="Spontaneous/genetically induced"),
                Option(value="other", label="Other"),
            ],
            order=1,
        ),
        Question(
            id="tumor_size_limit",
            question_type=QuestionType.TEXT,
            label="Maximum Tumor Size Endpoint",
            help_text="Specify maximum allowable tumor size",
            required=True,
            placeholder="e.g., 1500 mm³ or 2 cm in any dimension",
            order=2,
        ),
        Question(
            id="tumor_monitoring",
            question_type=QuestionType.TEXT,
            label="Tumor Monitoring Frequency",
            required=True,
            placeholder="e.g., Twice weekly with calipers",
            order=3,
        ),
    ],
)

CATEGORY_E_QUESTIONS = QuestionGroup(
    id="category_e_branch",
    title="Category E Justification",
    description="Required justification for withholding pain relief",
    order=6,
    branch_id="category_e_branch",
    questions=[
        Question(
            id="category_e_justification",
            question_type=QuestionType.TEXTAREA,
            label="Scientific Justification for Category E",
            help_text="Explain why pain relief cannot be provided without compromising scientific objectives",
            regulatory_reference="AWA §2143(a)(3)(C)(ii); 9 CFR 2.31(e)(4)",
            required=True,
            validation=[
                ValidationRule(
                    rule_type="min_length",
                    value=200,
                    message="Please provide detailed justification (at least 200 characters)",
                ),
            ],
            order=1,
        ),
        Question(
            id="category_e_alternatives_considered",
            question_type=QuestionType.TEXTAREA,
            label="Alternatives Considered",
            help_text="What alternatives were considered and why they were rejected?",
            required=True,
            order=2,
        ),
        Question(
            id="category_e_monitoring",
            question_type=QuestionType.TEXTAREA,
            label="Enhanced Monitoring Plan",
            help_text="Describe how animals will be closely monitored during Category E procedures",
            required=True,
            order=3,
        ),
    ],
)


# All question groups
ALL_QUESTION_GROUPS = [
    BASIC_INFO_QUESTIONS,
    SPECIES_QUESTIONS,
    PROCEDURE_QUESTIONS,
    SURGERY_QUESTIONS,
    TUMOR_QUESTIONS,
    CATEGORY_E_QUESTIONS,
]


def get_question_by_id(question_id: str) -> Optional[Question]:
    """
    Get a question by its ID.
    
    Args:
        question_id: The question ID to find
        
    Returns:
        Question if found, None otherwise.
    """
    for group in ALL_QUESTION_GROUPS:
        for question in group.questions:
            if question.id == question_id:
                return question
    return None


def get_group_by_id(group_id: str) -> Optional[QuestionGroup]:
    """
    Get a question group by its ID.
    
    Args:
        group_id: The group ID to find
        
    Returns:
        QuestionGroup if found, None otherwise.
    """
    for group in ALL_QUESTION_GROUPS:
        if group.id == group_id:
            return group
    return None


# Export all
__all__ = [
    "QuestionType",
    "Option",
    "ValidationRule",
    "Question",
    "QuestionGroup",
    "BASIC_INFO_QUESTIONS",
    "SPECIES_QUESTIONS",
    "PROCEDURE_QUESTIONS",
    "SURGERY_QUESTIONS",
    "TUMOR_QUESTIONS",
    "CATEGORY_E_QUESTIONS",
    "ALL_QUESTION_GROUPS",
    "get_question_by_id",
    "get_group_by_id",
]
