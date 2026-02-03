# IACUC Protocol Generator - Architecture Blueprint

This document contains the complete technical specification for the system, preserved from the initial design discussions.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Multi-Agent Architecture](#multi-agent-architecture)
3. [RAG Knowledge Base](#rag-knowledge-base)
4. [Adaptive Questionnaire System](#adaptive-questionnaire-system)
5. [Human-in-the-Loop Checkpoints](#human-in-the-loop-checkpoints)
6. [Protocol Output Schema](#protocol-output-schema)
7. [Validation Rules](#validation-rules)
8. [Technology Stack](#technology-stack)
9. [Project Structure](#project-structure)

---

## System Overview

### Purpose

A multi-agent AI system that generates submission-ready IACUC protocols through:
- Adaptive questioning based on research type
- RAG-powered regulatory compliance
- Simulated veterinary pre-review
- Iterative refinement loops
- Human-in-the-loop checkpoints

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SYSTEM ARCHITECTURE                                   │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌──────────────────────┐
                    │     Frontend UI      │
                    │  (React/Next.js)     │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │     FastAPI          │
                    │   Backend Server     │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
    ┌─────────────────┐ ┌────────────┐ ┌──────────────┐
    │  CrewAI Agents  │ │  ChromaDB  │ │  PostgreSQL  │
    │  (8 agents)     │ │  (RAG)     │ │  (State)     │
    └─────────────────┘ └────────────┘ └──────────────┘
              │
              ▼
    ┌─────────────────┐
    │  Claude 3.5     │
    │  Sonnet API     │
    └─────────────────┘
```

---

## Multi-Agent Architecture

### Agent Roster (8 Specialized Agents)

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    INTAKE       │     │   REGULATORY    │     │   ALTERNATIVES  │
│   SPECIALIST    │────▶│     SCOUT       │────▶│    RESEARCHER   │
│                 │     │                 │     │                 │
│ Extracts goals, │     │ Maps to AWA,    │     │ Database search │
│ species, methods│     │ PHS, Guide reqs │     │ for 3Rs         │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
        ┌───────────────────────────────────────────────┘
        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   STATISTICAL   │     │   VETERINARY    │     │    PROCEDURE    │
│   CONSULTANT    │────▶│    REVIEWER     │────▶│     WRITER      │
│                 │     │                 │     │                 │
│ Power analysis, │     │ Clinical review,│     │ Detailed SOPs,  │
│ justifies N     │     │ welfare flags   │     │ timelines       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
        ┌───────────────────────────────────────────────┘
        ▼
┌─────────────────┐     ┌─────────────────┐
│   LAY SUMMARY   │     │    PROTOCOL     │
│    WRITER       │────▶│   ASSEMBLER     │────▶ [FINAL OUTPUT]
│                 │     │                 │
│ 7th grade level,│     │ Consistency     │
│ no jargon       │     │ checks, format  │
└─────────────────┘     └─────────────────┘
```

### Detailed Agent Specifications

#### Agent 1: Intake Specialist

```yaml
role: "Research Intake Specialist"
goal: "Extract complete research parameters through adaptive questioning"
responsibilities:
  - Parse initial research description
  - Identify missing required information
  - Generate targeted follow-up questions
  - Classify research type and trigger appropriate branches
  - Extract: species, strain, numbers, procedures, timeline, personnel

outputs:
  - Structured research profile (JSON)
  - List of clarification questions (if needed)
  - Research classification tags

tools:
  - adaptive_questionnaire_generator
  - research_classifier
```

#### Agent 2: Regulatory Scout

```yaml
role: "Regulatory Compliance Scout"
goal: "Map research activities to all applicable federal and institutional requirements"
responsibilities:
  - Determine USDA Pain Category (B, C, D, or E)
  - Identify if species is USDA-covered vs PHS-only
  - Flag special permit requirements (wildlife, DEA controlled substances)
  - Retrieve applicable sections from The Guide, AWA, PHS Policy
  - Check for AAALAC-specific requirements

outputs:
  - Pain category determination with justification
  - Regulatory requirements checklist
  - Applicable citations from source documents
  - Special permits/approvals needed

tools:
  - rag_regulatory_search
  - pain_category_classifier
  - species_regulation_mapper
```

#### Agent 3: Alternatives Researcher (3Rs Specialist)

```yaml
role: "Alternatives and 3Rs Compliance Analyst"
goal: "Ensure robust Replacement, Reduction, and Refinement documentation"
responsibilities:
  - Generate literature search strategy for alternatives
  - Document database search (keywords, dates, databases)
  - Evaluate replacement possibilities (in vitro, in silico, lower species)
  - Justify why alternatives are not feasible
  - Identify refinement opportunities

outputs:
  - Alternatives search documentation (USDA-compliant narrative)
  - Replacement analysis with citations
  - Refinement recommendations
  - Search metadata (databases, dates, keywords, results count)

tools:
  - rag_alternatives_search
  - literature_search_formatter
```

#### Agent 4: Statistical Consultant

```yaml
role: "Biostatistics and Animal Numbers Consultant"
goal: "Provide rigorous statistical justification for animal numbers"
responsibilities:
  - Determine appropriate statistical test for study design
  - Calculate or validate sample size (power analysis)
  - Account for anticipated attrition/mortality
  - Break down numbers by experimental group
  - Justify any numbers not derived from power analysis

outputs:
  - Power analysis documentation (or justification if not applicable)
  - Animal numbers table by group/timepoint
  - Statistical test specification
  - Attrition allowance justification

tools:
  - power_analysis_calculator
  - study_design_analyzer
```

#### Agent 5: Veterinary Reviewer (Pre-Review Simulator)

```yaml
role: "Laboratory Animal Veterinarian Pre-Review Simulator"
goal: "Identify and flag welfare concerns before formal veterinary review"
responsibilities:
  - Validate anesthesia/analgesia protocols against formulary
  - Review surgical procedures for aseptic technique compliance
  - Evaluate humane endpoints for specificity and measurability
  - Check monitoring frequency and parameters
  - Assess post-procedural care adequacy
  - Flag any Category E justification issues

outputs:
  - Welfare concern flags with severity ratings
  - Drug dosage validation results
  - Humane endpoint assessment
  - Recommended modifications
  - Pre-review summary (pass/needs revision/critical issues)

tools:
  - rag_drug_formulary_lookup
  - rag_surgical_standards_search
  - humane_endpoint_evaluator
  - welfare_concern_flagger
```

#### Agent 6: Procedure Writer

```yaml
role: "Experimental Procedure Technical Writer"
goal: "Generate detailed, reproducible procedure descriptions"
responsibilities:
  - Write step-by-step experimental procedures
  - Include timing, dosages, routes of administration
  - Describe monitoring parameters and frequency
  - Detail criteria for intervention or euthanasia
  - Ensure procedures match stated objectives

outputs:
  - Detailed procedure narratives
  - Monitoring schedule tables
  - Drug administration tables (drug, dose, route, frequency)
  - Euthanasia method description with AVMA compliance

tools:
  - rag_procedure_templates
  - rag_avma_euthanasia_guidelines
  - timeline_generator
```

#### Agent 7: Lay Summary Writer

```yaml
role: "Lay Summary and Public Communication Specialist"
goal: "Translate technical content to 7th-grade reading level"
responsibilities:
  - Extract core research purpose and significance
  - Remove all technical jargon
  - Explain animal use rationale in plain language
  - Describe what animals will experience simply
  - Ensure accessibility for non-scientist IACUC members

outputs:
  - Lay summary (250-500 words, Flesch-Kincaid grade 7 or below)
  - Reading level score
  - Jargon-free benefit statement

tools:
  - readability_scorer
  - jargon_detector
  - simplification_engine
```

#### Agent 8: Protocol Assembler

```yaml
role: "Protocol Document Assembler and Quality Controller"
goal: "Compile sections into consistent, submission-ready document"
responsibilities:
  - Assemble all sections in institutional format
  - Cross-check for internal consistency (numbers, dates, personnel)
  - Verify all required fields are populated
  - Flag any contradictions between sections
  - Generate final formatted output

outputs:
  - Complete protocol document
  - Consistency check report
  - Missing field alerts
  - Submission readiness score

tools:
  - consistency_checker
  - format_validator
  - section_assembler
```

---

## RAG Knowledge Base

### Document Collections

```
knowledge_base/
├── regulatory_core/           # Federal regulations
│   ├── the_guide_8th_edition.pdf
│   ├── phs_policy.pdf
│   ├── awa_regulations_9cfr.pdf
│   ├── usda_policy_manual.pdf
│   └── us_government_principles.pdf
│
├── clinical_standards/        # Clinical guidelines
│   ├── avma_euthanasia_guidelines.pdf
│   ├── species_specific/
│   │   ├── rodent_anesthesia_guidelines.pdf
│   │   ├── rabbit_care_guidelines.pdf
│   │   ├── swine_procedures.pdf
│   │   └── nhp_guidelines.pdf
│   └── surgical_standards/
│       ├── aseptic_technique_guide.pdf
│       ├── post_operative_care.pdf
│       └── survival_surgery_standards.pdf
│
├── institutional/             # YOUR INSTITUTION'S DOCUMENTS
│   ├── sops/
│   │   ├── sop_rodent_surgery.pdf
│   │   ├── sop_blood_collection.pdf
│   │   ├── sop_euthanasia.pdf
│   │   └── [all other SOPs...]
│   ├── drug_formulary.pdf
│   ├── iacuc_policies/
│   │   ├── policy_humane_endpoints.pdf
│   │   ├── policy_multiple_survival_surgery.pdf
│   │   └── policy_food_water_restriction.pdf
│   └── approved_protocol_examples/
│       ├── example_behavioral_study.pdf
│       ├── example_tumor_model.pdf
│       └── example_surgical_model.pdf
│
└── alternatives_resources/    # 3Rs resources
    ├── three_rs_guidelines.pdf
    ├── alternatives_databases_list.pdf
    └── replacement_technologies_review.pdf
```

### Chunking Strategy

| Document Type | Chunk Size | Chunk Overlap | Metadata Fields |
|---------------|------------|---------------|-----------------|
| Regulatory (Guide, AWA) | 1000 tokens | 200 tokens | section_number, topic, species_relevance, pain_category_relevance |
| Drug Formulary | By drug entry | N/A | drug_name, species, route, indication |
| SOPs | By procedure step | 100 tokens | procedure_type, species, risk_level |
| AVMA Euthanasia | By species/method | 150 tokens | species, method, conditions |
| Example Protocols | By section | 200 tokens | section_type, species, procedure_type |

### Retrieval Strategy

```python
class RegulatoryRetriever:
    def retrieve(self, query, context):
        """
        Context-aware retrieval that filters by:
        - Species being used
        - Procedure types involved
        - Pain category
        - Institutional vs federal requirements
        """

        filters = {
            "species": context.species,
            "procedure_type": context.procedures,
            "pain_category": context.pain_category,
        }

        # Multi-collection search with relevance ranking
        results = []

        # Always search regulatory core
        results += self.search_collection("regulatory_core", query, filters, top_k=5)

        # Search clinical standards if procedures involved
        if context.has_procedures:
            results += self.search_collection("clinical_standards", query, filters, top_k=5)

        # Always include institutional requirements
        results += self.search_collection("institutional", query, filters, top_k=5)

        return self.rerank(results, query)
```

---

## Adaptive Questionnaire System

### Branching Logic Tree

```
START: Basic Research Information
│
├── What is your research objective? [free text]
├── What species will you use? [selection + text]
│   │
│   ├─► USDA-Covered Species (dog, cat, rabbit, NHP, pig, etc.)
│   │   └── Triggers: USDA reporting requirements, Pain Category determination
│   │
│   ├─► Rodents (mice, rats)
│   │   └── Triggers: PHS-only requirements, strain-specific questions
│   │
│   ├─► Aquatic Species (zebrafish, frogs)
│   │   └── Triggers: Aquatic housing requirements, staging questions
│   │
│   └─► Wildlife/Field Studies
│       └── Triggers: Permit questions, capture method questions
│
├── What procedures will you perform? [multi-select]
│   │
│   ├─► Survival Surgery
│   │   ├── How many survival surgeries per animal?
│   │   ├── Major or minor surgery?
│   │   ├── Aseptic technique confirmation
│   │   ├── Post-operative monitoring plan
│   │   └── Analgesia protocol
│   │
│   ├─► Non-Survival Surgery
│   │   ├── Anesthesia protocol
│   │   └── Euthanasia method
│   │
│   ├─► Injections/Drug Administration
│   │   ├── What substances? [triggers DEA check if controlled]
│   │   ├── Route of administration?
│   │   ├── Volume per injection?
│   │   ├── Frequency?
│   │   └── Known side effects?
│   │
│   ├─► Behavioral Testing
│   │   ├── Does testing involve stress/aversive stimuli?
│   │   ├── Food/water restriction involved?
│   │   └── Restraint methods?
│   │
│   ├─► Tissue Collection
│   │   ├── Terminal or survival collection?
│   │   ├── Volume limits (blood collection)?
│   │   └── Frequency?
│   │
│   ├─► Tumor/Disease Models
│   │   ├── Tumor type and induction method?
│   │   ├── Expected tumor burden?
│   │   ├── Humane endpoint criteria? [CRITICAL]
│   │   └── Monitoring frequency?
│   │
│   ├─► Breeding Colony
│   │   ├── Strain/genotype information
│   │   ├── Breeding scheme
│   │   ├── Weaning age and criteria
│   │   └── Genotyping method
│   │
│   └─► Imaging
│       ├── Modality (MRI, CT, PET, optical)?
│       ├── Anesthesia required?
│       ├── Contrast agents?
│       └── Frequency of imaging?
│
├── Will animals experience pain or distress? [determination flow]
│   │
│   ├─► No pain/distress anticipated
│   │   └── Assign Category C
│   │
│   ├─► Pain/distress relieved by anesthesia/analgesia
│   │   ├── Document relief methods
│   │   └── Assign Category D
│   │
│   └─► Pain/distress NOT relieved [CRITICAL PATH]
│       ├── Why can't pain be relieved? [scientific justification required]
│       ├── What are the specific humane endpoints?
│       ├── What is monitoring frequency?
│       ├── Veterinary consultation confirmed?
│       └── Assign Category E
│
└── Personnel and Training
    ├── Who is the Principal Investigator?
    ├── Who will perform procedures?
    └── Training verification [CITI, species-specific, procedure-specific]
```

### Question Schema Structure

```python
QuestionSchema = {
    "id": "surgery_type",
    "text": "What type of surgery will be performed?",
    "type": "single_select",  # single_select, multi_select, text, number, date
    "options": [
        {"value": "major_survival", "label": "Major Survival Surgery"},
        {"value": "minor_survival", "label": "Minor Survival Surgery"},
        {"value": "non_survival", "label": "Non-Survival (Terminal) Surgery"}
    ],
    "required": True,
    "help_text": "Major surgery penetrates a body cavity or has potential for permanent impairment",

    # Conditional branching
    "triggers": {
        "major_survival": ["multiple_surgery_justification", "aseptic_technique", "post_op_care"],
        "minor_survival": ["aseptic_technique", "post_op_care"],
        "non_survival": ["anesthesia_protocol", "euthanasia_method"]
    },

    # Regulatory mapping
    "regulatory_relevance": {
        "major_survival": {
            "guide_section": "4.D.1",
            "phs_section": "IV.C.1.g",
            "pain_category_impact": "minimum_D"
        }
    },

    # Validation rules
    "validation": {
        "major_survival": {
            "requires_fields": ["surgeon_training", "aseptic_confirmation", "post_op_monitoring"],
            "warnings": ["Multiple major survival surgeries require scientific justification"]
        }
    }
}
```

---

## Human-in-the-Loop Checkpoints

### Checkpoint Architecture

```
CHECKPOINT 1: Post-Intake Review
├── When: After Intake Specialist completes data gathering
├── Reviewer: Principal Investigator
├── Purpose: Confirm AI correctly understood research intent
├── Actions: Approve / Edit / Add Missing Information
└── Blocks: Regulatory analysis until approved

CHECKPOINT 2: Pain Category Determination
├── When: After Regulatory Scout assigns pain category
├── Reviewer: PI + Veterinarian (if Category D/E)
├── Purpose: Verify pain category assignment
├── Actions: Approve / Override with justification
└── Flags: Category E requires veterinary sign-off

CHECKPOINT 3: Alternatives Search Validation
├── When: After Alternatives Researcher completes 3Rs analysis
├── Reviewer: PI
├── Purpose: Verify search was comprehensive, alternatives properly dismissed
├── Actions: Approve / Request additional searches / Edit justification
└── Blocks: Cannot proceed with incomplete alternatives documentation

CHECKPOINT 4: Veterinary Pre-Review
├── When: After Veterinary Reviewer agent flags concerns
├── Reviewer: Laboratory Animal Veterinarian (actual human)
├── Purpose: Expert validation of clinical aspects
├── Review Items:
│   ├── Anesthesia/analgesia adequacy
│   ├── Surgical procedure appropriateness
│   ├── Humane endpoint specificity
│   ├── Monitoring plan adequacy
│   └── Drug dosages and routes
├── Actions: Approve / Require Changes / Request Consultation
└── Critical: Must pass before final assembly

CHECKPOINT 5: Final Protocol Review
├── When: After Protocol Assembler generates complete document
├── Reviewer: PI + designated lab personnel
├── Purpose: Final accuracy and completeness check
├── Review Items:
│   ├── All sections present and consistent
│   ├── Personnel listed correctly
│   ├── Numbers match across sections
│   └── Timeline is feasible
├── Actions: Approve for Submission / Return for Edits
└── Output: Submission-ready protocol
```

### Checkpoint State Schema

```python
CheckpointState = {
    "protocol_id": "uuid",
    "current_checkpoint": "veterinary_review",
    "checkpoint_history": [
        {
            "checkpoint": "intake_review",
            "status": "approved",
            "reviewer": "PI: Dr. Smith",
            "timestamp": "2024-01-15T10:30:00Z",
            "comments": "Looks good, proceed",
            "edits_made": []
        }
    ],
    "current_checkpoint_data": {
        "checkpoint": "veterinary_review",
        "status": "pending_review",
        "assigned_reviewer": "Dr. Johnson (Attending Vet)",
        "flagged_items": [
            {
                "id": "flag_001",
                "severity": "warning",
                "category": "analgesia",
                "message": "Consider adding buprenorphine SR for extended analgesia",
                "agent_source": "veterinary_reviewer",
                "relevant_section": "post_operative_care"
            }
        ],
        "sections_for_review": ["anesthesia", "analgesia", "surgical_procedure", "humane_endpoints"]
    },
    "protocol_data": { ... },
    "created_at": "2024-01-15T09:00:00Z",
    "last_modified": "2024-01-15T14:30:00Z"
}
```

---

## Protocol Output Schema

### Complete Protocol Structure

```python
ProtocolSchema = {
    # SECTION 1: ADMINISTRATIVE INFORMATION
    "administrative": {
        "protocol_title": str,  # Max 200 chars
        "principal_investigator": {
            "name": str,
            "department": str,
            "email": str,
            "phone": str
        },
        "co_investigators": List[Personnel],
        "funding_source": str,
        "grant_number": Optional[str],
        "submission_type": Enum["new", "amendment", "renewal"],
        "proposed_start_date": date,
        "proposed_end_date": date,
    },

    # SECTION 2: LAY SUMMARY
    "lay_summary": {
        "content": str,  # 250-500 words, grade 7 reading level
        "reading_level_score": float,
        "word_count": int
    },

    # SECTION 3: SCIENTIFIC JUSTIFICATION
    "scientific_justification": {
        "research_objectives": str,
        "background_and_significance": str,
        "specific_aims": List[str],
        "expected_outcomes": str,
        "relevance_to_human_health": str
    },

    # SECTION 4: ANIMALS REQUESTED
    "animals": {
        "species_groups": [
            {
                "common_name": str,
                "scientific_name": str,
                "strain": str,
                "source": str,
                "sex": Enum["male", "female", "both"],
                "age_range": str,
                "weight_range": str,
                "total_number": int,
                "usda_covered": bool,
                "pain_category": Enum["B", "C", "D", "E"],
                "group_breakdown": [
                    {
                        "group_name": str,
                        "purpose": str,
                        "number": int,
                        "procedures": List[str]
                    }
                ]
            }
        ],
        "total_animals_requested": int,
        "statistical_justification": {
            "method": str,
            "parameters": {
                "effect_size": float,
                "alpha": float,
                "power": float,
                "test_type": str
            },
            "narrative": str,
            "attrition_allowance": {
                "percentage": float,
                "justification": str
            }
        }
    },

    # SECTION 5: ALTERNATIVES (3Rs)
    "alternatives": {
        "replacement": {
            "considered_alternatives": List[str],
            "why_not_feasible": str,
            "literature_search": {
                "databases_searched": List[str],
                "search_date": date,
                "keywords_used": List[str],
                "years_covered": str,
                "results_summary": str
            }
        },
        "reduction": {
            "justification": str,
            "statistical_method": str,
            "pilot_study_reference": Optional[str]
        },
        "refinement": {
            "measures_taken": List[str],
            "anesthesia_analgesia_plan": str,
            "humane_endpoints": str,
            "training_qualifications": str
        }
    },

    # SECTION 6: EXPERIMENTAL PROCEDURES
    "procedures": {
        "experimental_design_overview": str,
        "detailed_procedures": [
            {
                "procedure_name": str,
                "procedure_description": str,
                "duration": str,
                "frequency": str,
                "anesthesia_required": bool,
                "anesthesia_details": Optional[AnesthesiaProtocol],
                "expected_effects": str,
                "potential_complications": str,
                "intervention_criteria": str
            }
        ],
        "study_timeline": {
            "total_duration": str,
            "timeline_narrative": str,
            "milestones": List[Milestone]
        }
    },

    # SECTION 7: ANESTHESIA, ANALGESIA, AND SEDATION
    "anesthesia_analgesia": {
        "anesthesia_protocols": [
            {
                "agent": str,
                "dose": str,
                "route": str,
                "frequency": str,
                "duration": str,
                "monitoring_during": str,
                "species_applicable": List[str]
            }
        ],
        "analgesia_protocols": [
            {
                "agent": str,
                "dose": str,
                "route": str,
                "frequency": str,
                "duration": str,
                "timing": str,
                "species_applicable": List[str]
            }
        ],
        "sedation_protocols": Optional[List],
        "formulary_compliance": bool,
        "veterinary_approved": bool
    },

    # SECTION 8: SURGICAL PROCEDURES
    "surgery": {
        "surgery_type": Enum["major_survival", "minor_survival", "non_survival"],
        "surgical_procedures": [
            {
                "procedure_name": str,
                "detailed_description": str,
                "surgeon": str,
                "surgeon_training": str,
                "aseptic_technique_confirmation": bool,
                "surgical_facility": str,
                "pre_operative_care": str,
                "post_operative_care": str,
                "suture_materials": str,
                "expected_recovery_time": str
            }
        ],
        "multiple_survival_surgery": {
            "applicable": bool,
            "scientific_justification": Optional[str]
        }
    },

    # SECTION 9: HUMANE ENDPOINTS
    "humane_endpoints": {
        "endpoint_criteria": [
            {
                "criterion": str,
                "measurement_method": str,
                "threshold": str,
                "action_taken": str
            }
        ],
        "monitoring_schedule": {
            "frequency": str,
            "parameters_monitored": List[str],
            "responsible_personnel": List[str],
            "documentation_method": str
        },
        "unexpected_morbidity_plan": str,
        "veterinary_notification_criteria": str
    },

    # SECTION 10: EUTHANASIA
    "euthanasia": {
        "primary_method": {
            "method": str,
            "avma_compliant": bool,
            "details": str,
            "confirmation_method": str
        },
        "secondary_method": Optional[EuthanasiaMethod],
        "personnel_trained": List[str],
        "carcass_disposal": str
    },

    # SECTION 11: HOUSING AND HUSBANDRY
    "housing": {
        "housing_location": str,
        "room_number": str,
        "cage_type": str,
        "animals_per_cage": int,
        "bedding_type": str,
        "environmental_enrichment": List[str],
        "light_cycle": str,
        "temperature_range": str,
        "humidity_range": str,
        "special_housing_requirements": Optional[str],
        "housing_exceptions_requested": Optional[str]
    },

    # SECTION 12: PERSONNEL AND TRAINING
    "personnel": {
        "team_members": [
            {
                "name": str,
                "role": str,
                "procedures_performed": List[str],
                "training_completed": [
                    {
                        "course_name": str,
                        "completion_date": date,
                        "expiration_date": Optional[date]
                    }
                ],
                "training_verified": bool
            }
        ]
    },

    # SECTION 13: HAZARDOUS MATERIALS
    "hazards": {
        "biological_hazards": Optional[HazardDetails],
        "chemical_hazards": Optional[HazardDetails],
        "radiological_hazards": Optional[HazardDetails],
        "ibc_approval_number": Optional[str],
        "radiation_safety_approval": Optional[str],
        "ppe_requirements": List[str]
    },

    # METADATA AND VALIDATION
    "metadata": {
        "generated_at": datetime,
        "generator_version": str,
        "agents_used": List[str],
        "checkpoints_completed": List[CheckpointRecord],
        "consistency_score": float,
        "completeness_score": float,
        "warnings": List[str],
        "regulatory_citations": List[Citation]
    }
}
```

---

## Validation Rules

```python
ValidationRules = {
    "animal_numbers_consistent": {
        "rule": "Sum of all group breakdowns == total_animals_requested",
        "severity": "error",
        "sections": ["animals.species_groups", "animals.total_animals_requested"]
    },

    "pain_category_matches_procedures": {
        "rule": "If survival surgery AND no analgesia THEN pain_category cannot be C",
        "severity": "error",
        "sections": ["animals.pain_category", "procedures", "anesthesia_analgesia"]
    },

    "personnel_training_complete": {
        "rule": "All personnel performing procedures must have valid training records",
        "severity": "error",
        "sections": ["personnel.team_members", "procedures.detailed_procedures"]
    },

    "humane_endpoints_for_category_d_e": {
        "rule": "If pain_category in [D, E] THEN humane_endpoints must be specific and measurable",
        "severity": "error",
        "sections": ["animals.pain_category", "humane_endpoints"]
    },

    "euthanasia_avma_compliant": {
        "rule": "Primary euthanasia method must be AVMA-approved for species",
        "severity": "error",
        "sections": ["euthanasia", "animals.species_groups"]
    },

    "surgery_requires_anesthesia": {
        "rule": "All surgical procedures must have associated anesthesia protocol",
        "severity": "error",
        "sections": ["surgery", "anesthesia_analgesia"]
    },

    "formulary_compliance": {
        "rule": "All drug doses must be within institutional formulary ranges",
        "severity": "warning",
        "sections": ["anesthesia_analgesia"]
    },

    "lay_summary_reading_level": {
        "rule": "Lay summary Flesch-Kincaid grade <= 7",
        "severity": "warning",
        "sections": ["lay_summary"]
    },

    "alternatives_search_current": {
        "rule": "Literature search must be within 6 months of submission",
        "severity": "warning",
        "sections": ["alternatives.replacement.literature_search"]
    },

    "protocol_duration_limit": {
        "rule": "Protocol duration cannot exceed 3 years",
        "severity": "error",
        "sections": ["administrative.proposed_start_date", "administrative.proposed_end_date"]
    }
}
```

---

## Technology Stack

```
BACKEND (Python)
├── Framework: FastAPI
├── Agent Orchestration: CrewAI
├── LLM: Claude 3.5 Sonnet (Anthropic API)
├── Vector Database: ChromaDB
├── Embeddings: OpenAI text-embedding-3-small
├── Document Processing:
│   ├── pypdf / pdfplumber
│   ├── unstructured
│   └── tiktoken
├── Database: PostgreSQL / SQLite
├── Task Queue: Celery + Redis (optional)
├── Validation: Pydantic v2
└── Testing: pytest

FRONTEND
├── Framework: React / Next.js
├── UI Components: shadcn/ui
├── State Management: Zustand / React Query
├── Forms: React Hook Form + Zod
├── Styling: Tailwind CSS
└── Real-time: SSE or WebSocket

INFRASTRUCTURE
├── Containerization: Docker
├── Environment: python-dotenv
└── API Documentation: FastAPI/OpenAPI
```

---

## Project Structure

```
iacuc-protocol-generator/
│
├── README.md
├── pyproject.toml
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── .gitignore
│
├── docs/
│   ├── ARCHITECTURE_BLUEPRINT.md
│   ├── IMPLEMENTATION_STEPS.md
│   ├── AGENT_SPECIFICATIONS.md
│   └── TESTING_GUIDE.md
│
├── knowledge_base/              # RAG documents (gitignored)
│   ├── regulatory_core/
│   ├── clinical_standards/
│   ├── institutional/
│   └── alternatives/
│
├── src/
│   ├── __init__.py
│   ├── main.py                  # FastAPI entry point
│   ├── config.py                # Configuration
│   │
│   ├── api/                     # API layer
│   │   ├── routes/
│   │   │   ├── protocols.py
│   │   │   ├── questionnaire.py
│   │   │   ├── review.py
│   │   │   └── documents.py
│   │   ├── dependencies.py
│   │   └── middleware.py
│   │
│   ├── agents/                  # CrewAI agents
│   │   ├── crew.py
│   │   ├── intake_specialist.py
│   │   ├── regulatory_scout.py
│   │   ├── alternatives_researcher.py
│   │   ├── statistical_consultant.py
│   │   ├── veterinary_reviewer.py
│   │   ├── procedure_writer.py
│   │   ├── lay_summary_writer.py
│   │   └── protocol_assembler.py
│   │
│   ├── tools/                   # Agent tools
│   │   ├── rag_tools.py
│   │   ├── formulary_tools.py
│   │   ├── readability_tools.py
│   │   ├── validation_tools.py
│   │   └── power_analysis_tools.py
│   │
│   ├── rag/                     # RAG infrastructure
│   │   ├── ingestion.py
│   │   ├── chunking.py
│   │   ├── embeddings.py
│   │   ├── retrieval.py
│   │   └── vector_store.py
│   │
│   ├── questionnaire/           # Adaptive questionnaire
│   │   ├── schema.py
│   │   ├── branching.py
│   │   ├── questions/
│   │   └── renderer.py
│   │
│   ├── review/                  # Human-in-the-loop
│   │   ├── checkpoints.py
│   │   ├── state_manager.py
│   │   └── notifications.py
│   │
│   ├── protocol/                # Protocol models
│   │   ├── schema.py
│   │   ├── validation.py
│   │   ├── assembly.py
│   │   └── export.py
│   │
│   ├── database/                # Database layer
│   │   ├── models.py
│   │   ├── repositories.py
│   │   └── migrations/
│   │
│   └── utils/                   # Utilities
│       ├── logging.py
│       ├── exceptions.py
│       └── text_processing.py
│
├── frontend/                    # React/Next.js (future)
│
├── tests/
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── scripts/
│   ├── ingest_documents.py
│   ├── setup_database.py
│   ├── verify_api_keys.py
│   └── generate_sample_protocol.py
│
└── notebooks/                   # Development notebooks
    ├── 01_rag_exploration.ipynb
    └── 02_agent_testing.ipynb
```

---

## Regulatory Background Reference

### Key Regulations

| Regulation | Governing Body | Primary Source | Scope |
|------------|----------------|----------------|-------|
| Animal Welfare Act | USDA (APHIS) | 9 C.F.R. Chapter 1 | Warm-blooded vertebrates (excluding certain rodents/birds) |
| PHS Policy | NIH (OLAW) | Health Research Extension Act | All live vertebrate animals |
| The Guide | NRC (ILAR) | Guide for Care and Use | Universal performance-based standards |
| AVMA Guidelines | AVMA | Euthanasia Panel Report | Standards for humane termination |

### Pain Categories (USDA)

- **Category B**: Animals held but not used in research
- **Category C**: No pain/distress, or pain relieved by drugs
- **Category D**: Pain/distress relieved by appropriate drugs
- **Category E**: Pain/distress NOT relieved (requires scientific justification)

### The Three Rs

1. **Replacement**: Consider non-animal alternatives
2. **Reduction**: Use minimum animals for valid results
3. **Refinement**: Minimize pain, distress, and improve welfare

---

*This blueprint was created to guide the development of a sophisticated, production-quality IACUC protocol generation system.*
