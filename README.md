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
│ College level,  │     │ Consistency     │
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
| **Lay Summary Writer** | Translate to plain language | College reading level summary |
| **Protocol Assembler** | Compile and validate | Submission-ready document, consistency report |

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+**
- **Node.js 18+** (for frontend)
- **Anthropic API Key** (for Claude)
- **OpenAI API Key** (for embeddings)

### Quick Start

```bash
# Clone repository
git clone https://github.com/rtolwani/iacuc-protocol-generator.git
cd iacuc-protocol-generator

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -e ".[dev]"

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys:
# - ANTHROPIC_API_KEY=your_key_here
# - OPENAI_API_KEY=your_key_here

# Run tests to verify installation
pytest tests/unit/ -v

# Start the backend API
uvicorn src.api.app:app --reload

# In a new terminal, start the frontend
cd frontend
npm install
npm run dev
```

### API Access

- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000

## 📁 Project Structure

```
iacuc-protocol-generator/
├── src/
│   ├── agents/          # CrewAI agent definitions (8 agents)
│   ├── tools/           # Agent tools (RAG, validation, formulary)
│   ├── rag/             # Document ingestion and retrieval
│   ├── questionnaire/   # Adaptive questioning system
│   ├── review/          # Human-in-the-loop checkpoints
│   ├── protocol/        # Protocol data models & export
│   └── api/             # FastAPI routes
├── frontend/            # Next.js frontend
│   ├── app/             # Next.js app router pages
│   └── components/      # React components
├── knowledge_base/      # RAG documents (gitignored)
├── tests/               # Test suite (743+ tests)
│   ├── unit/            # Unit tests
│   └── integration/     # API integration tests
├── scripts/             # Utility scripts
└── docs/                # Documentation
```

## 📚 Knowledge Base Setup

Add your regulatory documents to the knowledge base:

```bash
# Create the knowledge base directory structure
mkdir -p knowledge_base/regulatory_core
mkdir -p knowledge_base/clinical_standards
mkdir -p knowledge_base/institutional

# Add your PDFs (examples):
# - knowledge_base/regulatory_core/Guide_for_the_care_and_use_of_laboratory_animals.pdf
# - knowledge_base/regulatory_core/PHSPolicyLabAnimals.pdf
# - knowledge_base/regulatory_core/Guidelines-on-Euthanasia-2020.pdf

# Ingest documents into the vector database
python scripts/ingest_documents.py
```

## 🔄 Human-in-the-Loop Checkpoints

The system pauses for human review at critical decision points:

1. **Intake Review** - Confirm AI understood research correctly
2. **Regulatory Review** - Verify pain category classification
3. **Statistical Review** - Validate power analysis
4. **Veterinary Review** - Clinical aspects review
5. **Final Review** - PI approval before submission

## 🧪 Testing

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run integration tests
pytest tests/integration/ -v

# Run with coverage report
pytest --cov=src --cov-report=html
```

## 📦 Key Features

### Questionnaire System
- Adaptive branching based on research type
- Species-specific questions
- USDA pain category determination
- JSON Schema generation for frontend

### Protocol Generation
- All 13 IACUC-required sections
- PDF and Markdown export
- Completeness scoring
- Missing section detection

### Drug Formulary
- Species-specific dosing validation
- Route of administration checking
- USDA category compatibility

### Review Dashboard
- Pending review queue
- Approve/reject/revise workflow
- Reviewer comments and feedback

## ⚠️ Important Notes

- This tool generates **drafts** that require human review
- Always have protocols reviewed by qualified personnel before submission
- Institutional documents (SOPs, formulary) are required for full functionality
- Drug dosages must be verified against your institutional formulary

## 📖 Documentation

- [Implementation Steps](docs/IMPLEMENTATION_STEPS.md) - Step-by-step build guide
- [Architecture Blueprint](docs/ARCHITECTURE_BLUEPRINT.md) - Full technical specification
- [Agent Specifications](docs/AGENT_SPECIFICATIONS.md) - Detailed agent definitions

## 🛠️ Technology Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.11+, FastAPI |
| Agent Framework | CrewAI |
| LLM | Claude 3.5 Sonnet (Anthropic) |
| Embeddings | OpenAI text-embedding-ada-002 |
| Vector Database | ChromaDB |
| Frontend | Next.js 16, React, shadcn/ui |
| CSS | Tailwind CSS |
| Testing | pytest, pytest-cov |

## 📄 License

MIT License

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

*This project demonstrates sophisticated multi-agent orchestration for regulatory compliance in biomedical research.*
