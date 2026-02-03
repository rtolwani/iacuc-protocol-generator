# IACUC Protocol Generator

A multi-agent AI system that generates submission-ready IACUC (Institutional Animal Care and Use Committee) protocols through intelligent regulatory compliance, veterinary pre-review simulation, and adaptive questioning.

## 🎯 Project Vision

This system helps researchers create high-quality IACUC protocol drafts by:
- Guiding them through adaptive questionnaires based on their research type
- Automatically ensuring compliance with federal regulations (AWA, PHS Policy, The Guide)
- Simulating veterinary pre-review to catch issues early
- Generating lay summaries accessible to non-scientists
- Validating internal consistency across all protocol sections

## 🏗️ Architecture Overview

### Multi-Agent System (8 Specialized Agents)

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

### Agent Responsibilities

| Agent | Primary Function | Key Outputs |
|-------|------------------|-------------|
| **Intake Specialist** | Extract research parameters, identify gaps | Structured research profile, clarifying questions |
| **Regulatory Scout** | Map activities to federal requirements | Pain category, regulatory citations, permit requirements |
| **Alternatives Researcher** | Document 3Rs compliance | Literature search documentation, refinement measures |
| **Statistical Consultant** | Justify animal numbers | Power analysis, group breakdowns |
| **Veterinary Reviewer** | Simulate vet pre-review | Welfare flags, dosage validation, clinical recommendations |
| **Procedure Writer** | Generate detailed procedures | Step-by-step protocols, monitoring schedules |
| **Lay Summary Writer** | Translate to plain language | 7th-grade reading level summary |
| **Protocol Assembler** | Compile and validate | Submission-ready document, consistency report |

## 📚 RAG Knowledge Base Structure

```
knowledge_base/
├── regulatory_core/           # Federal regulations
│   ├── the_guide_8th_edition.pdf
│   ├── phs_policy.pdf
│   ├── awa_regulations_9cfr.pdf
│   └── usda_policy_manual.pdf
├── clinical_standards/        # Clinical guidelines
│   ├── avma_euthanasia_guidelines.pdf
│   └── species_guidelines/
├── institutional/             # YOUR institution's documents
│   ├── sops/
│   ├── drug_formulary.pdf
│   └── iacuc_policies/
└── alternatives/              # 3Rs resources
```

## 🔄 Human-in-the-Loop Checkpoints

The system pauses for human review at critical decision points:

1. **Post-Intake Review** - PI confirms AI understood research correctly
2. **Pain Category Determination** - Verify classification (requires vet for D/E)
3. **Alternatives Search Validation** - Confirm search was comprehensive
4. **Veterinary Pre-Review** - Actual veterinarian reviews clinical aspects
5. **Final Protocol Review** - PI approval before submission

## 🛠️ Technology Stack

- **Backend**: Python 3.11+, FastAPI
- **Agent Framework**: CrewAI
- **LLM**: Claude 3.5 Sonnet (Anthropic)
- **Vector Database**: ChromaDB
- **Frontend**: React/Next.js (planned)
- **Database**: PostgreSQL/SQLite

## 📁 Project Structure

```
iacuc-protocol-generator/
├── src/
│   ├── agents/          # CrewAI agent definitions
│   ├── tools/           # Agent tools (RAG, validation, etc.)
│   ├── rag/             # Document ingestion and retrieval
│   ├── questionnaire/   # Adaptive questioning system
│   ├── review/          # Human-in-the-loop checkpoints
│   ├── protocol/        # Protocol data models
│   └── api/             # FastAPI routes
├── knowledge_base/      # RAG documents (gitignored)
├── tests/               # Test suite
├── scripts/             # Utility scripts
└── docs/                # Documentation
```

## 🚀 Getting Started

See [SETUP.md](docs/SETUP.md) for detailed setup instructions.

### Quick Start

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/iacuc-protocol-generator.git
cd iacuc-protocol-generator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Run tests
pytest

# Start development server
uvicorn src.main:app --reload
```

## 📋 Implementation Phases

This project is being built incrementally. See [IMPLEMENTATION_STEPS.md](docs/IMPLEMENTATION_STEPS.md) for the detailed step-by-step guide.

### Current Status: Phase 1 - Foundation

- [x] Project structure created
- [ ] Development environment setup
- [ ] Basic RAG pipeline
- [ ] First agent (Lay Summary Writer)

## 🔑 Required API Keys

- **Anthropic API Key** - For Claude 3.5 Sonnet
- **OpenAI API Key** (optional) - For embeddings (can use alternatives)

## 📖 Documentation

- [Implementation Steps](docs/IMPLEMENTATION_STEPS.md) - Step-by-step build guide
- [Architecture Blueprint](docs/ARCHITECTURE_BLUEPRINT.md) - Full technical specification
- [Agent Specifications](docs/AGENT_SPECIFICATIONS.md) - Detailed agent definitions
- [Testing Guide](docs/TESTING_GUIDE.md) - How to run and write tests

## ⚠️ Important Notes

- This tool generates **drafts** that require human review
- Always have protocols reviewed by qualified personnel before submission
- Institutional documents (SOPs, formulary) are required for full functionality
- Drug dosages must be verified against your institutional formulary

## 📄 License

[TBD]

## 🤝 Contributing

[TBD]

---

*This project was designed to demonstrate sophisticated multi-agent orchestration for regulatory compliance in biomedical research.*
