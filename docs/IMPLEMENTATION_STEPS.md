# IACUC Protocol Generator - Implementation Steps

This document breaks down the entire project into small, actionable steps. Each step is designed to be completed in one work session with verification.

## How to Use This Guide

For each step:
1. **Read** the step description and requirements
2. **Build** the component with Claude's help
3. **Verify** using the provided verification method
4. **Commit & Push** to GitHub
5. **Move to next step** only when verification passes

---

## Phase 1: Foundation & Environment Setup

### Step 1.1: Set Up Development Environment
**Goal**: Get Python environment working with basic dependencies

**What you need before starting**:
- Python 3.11+ installed on your computer
- Git installed
- A GitHub account
- A code editor (VS Code recommended)

**Tasks**:
- [x] Clone the repository (if not already done)
- [x] Create Python virtual environment
- [x] Install initial dependencies
- [x] Verify Python and pip work correctly

**Verification**:
```bash
# Run these commands - all should succeed without errors
python --version  # Should show 3.11+
pip --version
python -c "import pydantic; print('Pydantic OK')"
```

**Commit message**: `chore: set up development environment`

---

### Step 1.2: Get API Keys
**Goal**: Obtain necessary API keys for LLM and embeddings

**What you need**:
- Credit card for API billing (small amounts for development)

**Tasks**:
- [x] Create Anthropic account at https://console.anthropic.com/
- [x] Generate Anthropic API key
- [x] (Optional) Create OpenAI account for embeddings
- [x] Add keys to `.env` file (NEVER commit this file!)

**Verification**:
```bash
# Run the verification script we'll create
python scripts/verify_api_keys.py
```

**Expected output**: "Anthropic API key is valid" (and OpenAI if configured)

**Commit message**: N/A (no code changes, just local .env file)

---

### Step 1.3: Create Basic FastAPI Application
**Goal**: Have a running web server that responds to requests

**Tasks**:
- [x] Create `src/main.py` with basic FastAPI app
- [x] Create health check endpoint
- [x] Test that server starts and responds

**Verification**:
```bash
# Start the server
uvicorn src.main:app --reload

# In another terminal (or browser), visit:
# http://localhost:8000/health
# Should return: {"status": "healthy"}

# Also check auto-generated docs at:
# http://localhost:8000/docs
```

**Commit message**: `feat: add basic FastAPI application with health check`

---

### Step 1.4: Set Up ChromaDB Vector Store
**Goal**: Have a working vector database for RAG

**Tasks**:
- [x] Create `src/rag/vector_store.py`
- [x] Initialize ChromaDB with persistent storage
- [x] Create basic add/query functions
- [x] Write test to verify it works

**Verification**:
```bash
pytest tests/unit/test_vector_store.py -v
```

**Expected**: All tests pass, ChromaDB stores and retrieves documents

**Commit message**: `feat: add ChromaDB vector store setup`

---

### Step 1.5: Create Document Ingestion Pipeline
**Goal**: Be able to load PDF documents into the vector store

**Tasks**:
- [x] Create `src/rag/ingestion.py`
- [x] Implement PDF text extraction
- [x] Implement text chunking with overlap
- [x] Add metadata extraction
- [x] Create ingestion script

**What you need before starting**:
- At least ONE PDF document for testing (can be any PDF initially)

**Verification**:
```bash
# Run ingestion on a test PDF
python scripts/ingest_documents.py --file tests/fixtures/sample.pdf

# Then run the test
pytest tests/unit/test_ingestion.py -v
```

**Commit message**: `feat: add document ingestion pipeline`

---

### Step 1.6: Add Core Regulatory Documents
**Goal**: Ingest the essential regulatory documents into knowledge base

**What you need before starting**:
- Download these documents (all freely available):
  - The Guide for the Care and Use of Laboratory Animals (8th Edition)
    - https://www.ncbi.nlm.nih.gov/books/NBK54050/
  - PHS Policy on Humane Care and Use of Laboratory Animals
    - https://olaw.nih.gov/policies-laws/phs-policy.htm
  - AVMA Guidelines for the Euthanasia of Animals
    - https://www.avma.org/resources-tools/avma-policies/avma-guidelines-euthanasia-animals

**Tasks**:
- [x] Download the documents
- [x] Place in `knowledge_base/regulatory_core/`
- [x] Run ingestion pipeline on each
- [x] Verify documents are searchable

**Verification**:
```bash
# Run the regulatory document ingestion
python scripts/ingest_documents.py --directory knowledge_base/regulatory_core/

# Test retrieval
python scripts/test_rag_retrieval.py --query "pain category D requirements"
```

**Expected**: Returns relevant excerpts from The Guide about pain categories

**Commit message**: `feat: ingest core regulatory documents`

---

### Step 1.7: Create Basic RAG Retrieval Tool
**Goal**: Have a working tool that agents can use to search documents

**Tasks**:
- [x] Create `src/tools/rag_tools.py`
- [x] Implement `RegulatorySearchTool` class
- [x] Add metadata filtering (by document type, species, etc.)
- [x] Write tests

**Verification**:
```bash
pytest tests/unit/test_rag_tools.py -v

# Also test interactively
python -c "
from src.tools.rag_tools import RegulatorySearchTool
tool = RegulatorySearchTool()
result = tool._run('What are the requirements for survival surgery?')
print(result[:500])
"
```

**Commit message**: `feat: add RAG retrieval tool for agents`

---

## Phase 2: First Agent - Lay Summary Writer

### Step 2.1: Set Up CrewAI with Claude
**Goal**: Have CrewAI working with Claude as the LLM

**Tasks**:
- [x] Create `src/agents/__init__.py`
- [x] Create `src/config.py` for LLM configuration
- [x] Test that CrewAI can call Claude successfully

**Verification**:
```bash
pytest tests/unit/test_crewai_setup.py -v
```

**Expected**: Simple agent task completes successfully using Claude

**Commit message**: `feat: configure CrewAI with Claude LLM`

---

### Step 2.2: Create Readability Scoring Tool
**Goal**: Have a tool that measures text reading level

**Tasks**:
- [x] Create `src/tools/readability_tools.py`
- [x] Implement Flesch-Kincaid grade level calculation
- [x] Add suggestions for simplification
- [x] Write tests with sample texts

**Verification**:
```bash
pytest tests/unit/test_readability_tools.py -v
```

**Test cases should include**:
- Simple text (grade 5-6) → PASS
- Technical jargon (grade 12+) → FAIL with suggestions

**Commit message**: `feat: add readability scoring tool`

---

### Step 2.3: Implement Lay Summary Writer Agent
**Goal**: Have an agent that can simplify technical text

**Tasks**:
- [x] Create `src/agents/lay_summary_writer.py`
- [x] Define agent role, goal, backstory
- [x] Connect readability tool to agent
- [x] Implement iterative refinement (rewrite until grade ≤ 7)

**Verification**:
```bash
pytest tests/unit/test_lay_summary_writer.py -v

# Also test interactively
python scripts/test_lay_summary_agent.py --input "Your technical text here"
```

**Expected**: Agent takes technical text and outputs grade 7 or below summary

**Commit message**: `feat: implement Lay Summary Writer agent`

---

### Step 2.4: Create End-to-End Test for Lay Summary
**Goal**: Verify the complete flow works with real examples

**Tasks**:
- [x] Create test fixtures with sample research descriptions
- [x] Write integration test that runs full agent workflow
- [x] Verify output quality meets requirements

**Verification**:
```bash
pytest tests/integration/test_lay_summary_e2e.py -v
```

**Expected**:
- All sample inputs produce valid lay summaries
- All summaries have Flesch-Kincaid grade ≤ 7.5
- No technical jargon remains

**Commit message**: `test: add end-to-end tests for Lay Summary Writer`

---

## Phase 3: Regulatory Scout Agent

### Step 3.1: Create Pain Category Classification Tool
**Goal**: Tool that determines USDA pain category based on procedures

**Tasks**:
- [x] Create `src/tools/pain_category_tool.py`
- [x] Implement classification logic based on USDA definitions
- [x] Handle edge cases (multiple procedures, relief measures)
- [x] Write comprehensive tests

**Verification**:
```bash
pytest tests/unit/test_pain_category_tool.py -v
```

**Test cases**:
- Behavioral observation only → Category C
- Surgery with analgesia → Category D
- Unrelieved pain with justification → Category E

**Commit message**: `feat: add pain category classification tool`

---

### Step 3.2: Implement Regulatory Scout Agent
**Goal**: Agent that identifies all applicable regulations

**Tasks**:
- [x] Create `src/agents/regulatory_scout.py`
- [x] Connect RAG tool and pain category tool
- [x] Implement species regulation mapping
- [x] Add permit requirement detection

**Verification**:
```bash
pytest tests/unit/test_regulatory_scout.py -v

# Interactive test
python scripts/test_regulatory_scout.py --species "rabbit" --procedures "survival_surgery"
```

**Expected**: Returns pain category, applicable regulations with citations, permit requirements

**Commit message**: `feat: implement Regulatory Scout agent`

---

### Step 3.3: Create Two-Agent Crew Test
**Goal**: Verify two agents can work together in sequence

**Tasks**:
- [x] Create simple crew with Regulatory Scout → Lay Summary Writer
- [x] Test handoff between agents
- [x] Verify context is preserved

**Verification**:
```bash
pytest tests/integration/test_two_agent_crew.py -v
```

**Commit message**: `test: add two-agent crew integration test`

---

## Phase 4: Alternatives Researcher Agent

### Step 4.1: Create Literature Search Documentation Tool
**Goal**: Tool that formats alternatives search documentation

**Tasks**:
- [x] Create `src/tools/literature_search_tool.py`
- [x] Implement USDA-compliant search documentation format
- [x] Include required fields (databases, dates, keywords, results)

**Verification**:
```bash
pytest tests/unit/test_literature_search_tool.py -v
```

**Commit message**: `feat: add literature search documentation tool`

---

### Step 4.2: Implement Alternatives Researcher Agent
**Goal**: Agent that generates 3Rs documentation

**Tasks**:
- [x] Create `src/agents/alternatives_researcher.py`
- [x] Implement Replacement, Reduction, Refinement sections
- [x] Connect RAG tool for alternatives resources
- [x] Generate compliant search narratives

**Verification**:
```bash
pytest tests/unit/test_alternatives_researcher.py -v
```

**Commit message**: `feat: implement Alternatives Researcher agent`

---

## Phase 5: Statistical Consultant Agent

### Step 5.1: Create Power Analysis Tool
**Goal**: Tool that performs/validates sample size calculations

**Tasks**:
- [x] Create `src/tools/power_analysis_tool.py`
- [x] Implement basic power analysis formulas
- [x] Support common statistical tests (t-test, ANOVA)
- [x] Add attrition calculation

**Verification**:
```bash
pytest tests/unit/test_power_analysis_tool.py -v
```

**Commit message**: `feat: add power analysis tool`

---

### Step 5.2: Implement Statistical Consultant Agent
**Goal**: Agent that justifies animal numbers

**Tasks**:
- [x] Create `src/agents/statistical_consultant.py`
- [x] Generate power analysis documentation
- [x] Create animal numbers breakdown tables
- [x] Handle non-power-analysis justifications

**Verification**:
```bash
pytest tests/unit/test_statistical_consultant.py -v
```

**Commit message**: `feat: implement Statistical Consultant agent`

---

## Phase 6: Clinical Agents (Veterinary Reviewer & Procedure Writer)

### Step 6.1: Add Institutional Drug Formulary
**Goal**: Ingest your institution's drug formulary for validation

**What you need before starting**:
- Your institution's approved drug formulary (PDF or create sample)
- If you don't have one, we'll create a sample formulary for testing

**Tasks**:
- [x] Create sample formulary if needed
- [x] Ingest formulary into vector store with drug-specific chunking
- [x] Create `src/tools/formulary_tool.py`

**Verification**:
```bash
python scripts/test_formulary_lookup.py --drug "ketamine" --species "mouse"
```

**Expected**: Returns approved dose ranges, routes, contraindications

**Commit message**: `feat: add drug formulary lookup tool`

---

### Step 6.2: Implement Veterinary Reviewer Agent
**Goal**: Agent that simulates veterinary pre-review

**Tasks**:
- [x] Create `src/agents/veterinary_reviewer.py`
- [x] Implement drug dosage validation against formulary
- [x] Add humane endpoint assessment
- [x] Create welfare concern flagging system
- [x] Implement severity ratings (critical, warning, info)

**Verification**:
```bash
pytest tests/unit/test_veterinary_reviewer.py -v
```

**Commit message**: `feat: implement Veterinary Reviewer agent`

---

### Step 6.3: Implement Procedure Writer Agent
**Goal**: Agent that generates detailed procedure descriptions

**Tasks**:
- [x] Create `src/agents/procedure_writer.py`
- [x] Generate step-by-step procedures
- [x] Create drug administration tables
- [x] Generate monitoring schedules
- [x] Include AVMA-compliant euthanasia methods

**Verification**:
```bash
pytest tests/unit/test_procedure_writer.py -v
```

**Commit message**: `feat: implement Procedure Writer agent`

---

## Phase 7: Intake Specialist & Protocol Assembler

### Step 7.1: Create Research Classifier Tool
**Goal**: Tool that classifies research type and triggers appropriate branches

**Tasks**:
- [x] Create `src/tools/research_classifier.py`
- [x] Classify by procedure types (surgery, behavioral, etc.)
- [x] Identify species categories
- [x] Flag special requirements (DEA, wildlife permits)

**Verification**:
```bash
pytest tests/unit/test_research_classifier.py -v
```

**Commit message**: `feat: add research classifier tool`

---

### Step 7.2: Implement Intake Specialist Agent
**Goal**: Agent that extracts research parameters and identifies gaps

**Tasks**:
- [x] Create `src/agents/intake_specialist.py`
- [x] Parse unstructured research descriptions
- [x] Generate clarifying questions for missing info
- [x] Output structured research profile

**Verification**:
```bash
pytest tests/unit/test_intake_specialist.py -v
```

**Commit message**: `feat: implement Intake Specialist agent`

---

### Step 7.3: Create Consistency Checker Tool
**Goal**: Tool that validates internal consistency of protocol

**Tasks**:
- [x] Create `src/tools/consistency_checker.py`
- [x] Check animal numbers match across sections
- [x] Verify personnel are consistently listed
- [x] Validate timeline alignment
- [x] Flag contradictions

**Verification**:
```bash
pytest tests/unit/test_consistency_checker.py -v
```

**Test cases**:
- Protocol with matching numbers → PASS
- Protocol with mismatched numbers → FAIL with specific error

**Commit message**: `feat: add protocol consistency checker tool`

---

### Step 7.4: Implement Protocol Assembler Agent
**Goal**: Agent that compiles final document and validates

**Tasks**:
- [x] Create `src/agents/protocol_assembler.py`
- [x] Assemble all sections in correct order
- [x] Run consistency checks
- [x] Generate completeness score
- [x] Flag missing required fields

**Verification**:
```bash
pytest tests/unit/test_protocol_assembler.py -v
```

**Commit message**: `feat: implement Protocol Assembler agent`

---

## Phase 8: Full Crew Integration

### Step 8.1: Create Complete 8-Agent Crew
**Goal**: All agents working together in sequence

**Tasks**:
- [x] Create `src/agents/crew.py`
- [x] Define task sequence with dependencies
- [x] Configure agent handoffs
- [x] Test complete workflow

**Verification**:
```bash
pytest tests/integration/test_full_crew.py -v --timeout=300
```

**Note**: This test may take several minutes due to multiple LLM calls

**Commit message**: `feat: implement complete 8-agent crew workflow`

---

### Step 8.2: Create Sample Protocol Generation Test
**Goal**: Generate a complete protocol from realistic input

**Tasks**:
- [x] Create realistic test inputs (behavioral study, surgical study, tumor model)
- [x] Run full generation workflow
- [x] Validate all output sections
- [x] Check regulatory compliance

**Verification**:
```bash
pytest tests/integration/test_protocol_generation.py -v

# Also generate a sample you can manually review
python scripts/generate_sample_protocol.py --type behavioral --output sample_output.json
```

**Expected**: Complete, valid protocol document in JSON format

**Commit message**: `test: add full protocol generation tests`

---

## Phase 9: Adaptive Questionnaire System

### Step 9.1: Define Question Schemas
**Goal**: Create structured question definitions for all branches

**Tasks**:
- [x] Create `src/questionnaire/schema.py`
- [x] Define question types (single_select, multi_select, text, etc.)
- [x] Create questions for basic info, species, procedures
- [x] Add help text and regulatory references

**Verification**:
```bash
pytest tests/unit/test_questionnaire_schema.py -v
```

**Commit message**: `feat: define questionnaire schemas`

---

### Step 9.2: Implement Branching Logic
**Goal**: Questions that adapt based on previous answers

**Tasks**:
- [x] Create `src/questionnaire/branching.py`
- [x] Implement trigger conditions
- [x] Handle nested branching
- [x] Test all major pathways

**Verification**:
```bash
pytest tests/unit/test_questionnaire_branching.py -v
```

**Test cases**:
- Select "survival surgery" → triggers surgical branch questions
- Select "mouse" → skips USDA-specific questions
- Select "Pain Category E" → triggers justification requirements

**Commit message**: `feat: implement questionnaire branching logic`

---

### Step 9.3: Create JSON Schema Renderer
**Goal**: Generate dynamic form schemas for the frontend

**Tasks**:
- [x] Create `src/questionnaire/renderer.py`
- [x] Output JSON Schema format for forms
- [x] Include validation rules
- [x] Test schema generation

**Verification**:
```bash
pytest tests/unit/test_questionnaire_renderer.py -v

# Generate sample schema
python scripts/generate_questionnaire_schema.py --branch surgical > sample_schema.json
```

**Commit message**: `feat: add questionnaire JSON schema renderer`

---

## Phase 10: Human-in-the-Loop System

### Step 10.1: Create Checkpoint State Manager
**Goal**: Persist workflow state at review points

**Tasks**:
- [x] Create `src/review/state_manager.py`
- [x] Implement state serialization/deserialization
- [x] Support pause and resume at any checkpoint
- [x] Store reviewer feedback

**Verification**:
```bash
pytest tests/unit/test_state_manager.py -v
```

**Commit message**: `feat: add checkpoint state manager`

---

### Step 10.2: Define Review Checkpoints
**Goal**: Configure the 5 human review points

**Tasks**:
- [x] Create `src/review/checkpoints.py`
- [x] Define checkpoint conditions
- [x] Implement approval/rejection/revision flows
- [x] Add feedback routing back to agents

**Verification**:
```bash
pytest tests/unit/test_checkpoints.py -v
```

**Commit message**: `feat: define human review checkpoints`

---

### Step 10.3: Create Review API Endpoints
**Goal**: API for reviewers to approve/reject/comment

**Tasks**:
- [x] Create `src/api/routes/review.py`
- [x] Implement GET checkpoint status
- [x] Implement POST approval/rejection
- [x] Handle revision requests

**Verification**:
```bash
pytest tests/integration/test_review_api.py -v

# Manual test
# Start server, then use API docs at http://localhost:8000/docs
```

**Commit message**: `feat: add review API endpoints`

---

## Phase 11: Protocol API & Export

### Step 11.1: Create Protocol Data Models
**Goal**: Pydantic models for complete protocol structure

**Tasks**:
- [ ] Create `src/protocol/schema.py`
- [ ] Define all 13 protocol sections
- [ ] Add validation rules
- [ ] Create nested models for complex fields

**Verification**:
```bash
pytest tests/unit/test_protocol_schema.py -v
```

**Commit message**: `feat: define protocol data models`

---

### Step 11.2: Create Protocol API Endpoints
**Goal**: CRUD operations for protocols

**Tasks**:
- [ ] Create `src/api/routes/protocols.py`
- [ ] Implement create, read, update, delete
- [ ] Add list with filtering
- [ ] Connect to database

**Verification**:
```bash
pytest tests/integration/test_protocol_api.py -v
```

**Commit message**: `feat: add protocol CRUD API endpoints`

---

### Step 11.3: Add Protocol Export
**Goal**: Export completed protocols to PDF/Word

**Tasks**:
- [ ] Create `src/protocol/export.py`
- [ ] Implement PDF generation
- [ ] Implement Word document generation
- [ ] Add institutional header/footer templates

**Verification**:
```bash
pytest tests/unit/test_protocol_export.py -v

# Generate sample exports
python scripts/export_protocol.py --id SAMPLE_ID --format pdf
python scripts/export_protocol.py --id SAMPLE_ID --format docx
```

**Commit message**: `feat: add protocol export to PDF and Word`

---

## Phase 12: Frontend (Basic)

### Step 12.1: Set Up Next.js Project
**Goal**: Basic React/Next.js frontend structure

**What you need before starting**:
- Node.js 18+ installed
- npm or yarn

**Tasks**:
- [ ] Initialize Next.js project in `frontend/`
- [ ] Install shadcn/ui components
- [ ] Configure Tailwind CSS
- [ ] Create basic layout

**Verification**:
```bash
cd frontend
npm run dev
# Visit http://localhost:3000 - should see basic page
```

**Commit message**: `feat: initialize Next.js frontend`

---

### Step 12.2: Create Protocol Wizard UI
**Goal**: Multi-step form for protocol creation

**Tasks**:
- [ ] Create questionnaire step components
- [ ] Implement form state management
- [ ] Connect to backend questionnaire API
- [ ] Add progress indicator

**Verification**:
- Manually test form flow in browser
- All questions render correctly
- Branching works as expected

**Commit message**: `feat: add protocol creation wizard`

---

### Step 12.3: Create Review Dashboard
**Goal**: Interface for reviewers to approve protocols

**Tasks**:
- [ ] Create review dashboard page
- [ ] Show flagged items with severity
- [ ] Implement approve/reject/comment actions
- [ ] Connect to review API

**Verification**:
- Manually test review flow
- Comments are saved
- Approval/rejection triggers correct backend flow

**Commit message**: `feat: add reviewer dashboard`

---

## Phase 13: Testing & Documentation

### Step 13.1: Comprehensive Test Coverage
**Goal**: Ensure high test coverage across all components

**Tasks**:
- [ ] Add missing unit tests
- [ ] Add edge case tests
- [ ] Run coverage report
- [ ] Fix any gaps

**Verification**:
```bash
pytest --cov=src --cov-report=html
# Open htmlcov/index.html in browser
# Target: >80% coverage
```

**Commit message**: `test: improve test coverage`

---

### Step 13.2: Write User Documentation
**Goal**: Documentation for end users

**Tasks**:
- [ ] Update README with final instructions
- [ ] Write user guide
- [ ] Document all configuration options
- [ ] Add troubleshooting guide

**Verification**:
- Have someone else follow the setup instructions
- They should be able to run the system

**Commit message**: `docs: add user documentation`

---

### Step 13.3: Create Demo Video/Screenshots
**Goal**: Visual demonstration of the system

**Tasks**:
- [ ] Record demo of complete workflow
- [ ] Capture screenshots of key screens
- [ ] Add to documentation

**Commit message**: `docs: add demo materials`

---

## Quick Reference: What You Need at Each Phase

| Phase | External Requirements |
|-------|----------------------|
| 1 | Python 3.11+, Anthropic API key |
| 2-5 | None (uses Phase 1 setup) |
| 6 | Institutional drug formulary (or sample) |
| 9-10 | None |
| 11 | None |
| 12 | Node.js 18+ |
| 13 | None |

## Estimated Effort

| Phase | Steps | Complexity |
|-------|-------|------------|
| Phase 1 | 7 steps | Medium (setup) |
| Phase 2 | 4 steps | Low-Medium |
| Phase 3 | 3 steps | Medium |
| Phase 4 | 2 steps | Low |
| Phase 5 | 2 steps | Low |
| Phase 6 | 3 steps | Medium |
| Phase 7 | 4 steps | Medium |
| Phase 8 | 2 steps | High |
| Phase 9 | 3 steps | Medium |
| Phase 10 | 3 steps | Medium |
| Phase 11 | 3 steps | Medium |
| Phase 12 | 3 steps | Medium-High |
| Phase 13 | 3 steps | Low |

**Total: 42 steps**

---

## Next Step

Start with **Step 1.1: Set Up Development Environment**

When you're ready, tell Claude: "Let's start Step 1.1" and we'll work through it together!
