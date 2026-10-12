# ClaimGuard-MCP

**Multimodal Insurance Claim Consistency & Fraud Arbiter**

ClaimGuard-MCP is an end-to-end insurance claim validation system that extracts structured data from claim documents (PDFs and images), performs cross-document consistency checks, evaluates policy compliance, validates expense claims, and uses computer vision (Qwen2-VL) to analyze vehicle damage photographs.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Orchestration                        │
│              ClaimPackageService                         │
├─────────┬───────────┬────────────┬──────────────────────┤
│ Ingestion│ Extraction │  Vision    │    Evaluation        │
│  ├─ PDF  │  ├─ Fields │  ├─ Qwen2  │  ├─ Policy          │
│  ├─ OCR  │  ├─ Mapper │  └─ VL API │  ├─ Invariants      │
│  └─ Class│  └─ Struct │            │  ├─ Expenses         │
│          │            │            │  ├─ Damage           │
│          │            │            │  └─ Documents        │
├──────────┴────────────┴────────────┴─────────────────────┤
│                    Services (DB Layer)                    │
│   ClaimService · DocumentService · EvidenceService       │
│   PolicyService · InvariantService                       │
├──────────────────────────────────────────────────────────┤
│                   DuckDB Database                        │
└──────────────────────────────────────────────────────────┘
```

---

## Features

- **Document Ingestion** — PDF text extraction via PyMuPDF, OCR via Tesseract
- **Document Classification** — Automatic detection of claim forms, policies, police reports, repair estimates, medical bills
- **Field Extraction** — Regex-based structured field extraction with evidence persistence
- **Cross-Document Consistency** — Vehicle registration, policy number, claimant name, and incident date validation across documents
- **Policy Evaluation** — Policy period, coverage limit, and deductible checks
- **Expense Validation** — Repair cost vs. coverage, parts + labor reconciliation
- **Damage Analysis** — Qwen2-VL vision model for vehicle damage area and severity assessment
- **Damage Consistency** — Cross-reference between claim description and photo evidence
- **MCP Servers** — Model Context Protocol servers for AI agent integration
- **Reports** — Text and PDF report generation
- **Streamlit UI** — Web interface for interactive claim analysis

---

## Prerequisites

- **Python 3.11+**
- **Tesseract OCR** — Install from [tesseract-ocr](https://github.com/tesseract-ocr/tesseract)
- **Vision API** (optional) — Remote Qwen2-VL inference server for damage photo analysis

---

## Installation

```bash
# Clone the repository
git clone https://github.com/kishanptl951/ClaimGuard_MCP_Multimodal-Insurance-Claim-Consistency-Fraud-Arbiter.git
cd ClaimGuard-MCP

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/macOS)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Configuration

Copy the environment template and fill in your values:

```bash
cp .env.example .env
```

| Variable | Description | Required |
|---|---|---|
| `VISION_API_URL` | URL of the Qwen2-VL inference server | Only for damage photo analysis |

---

## Usage

### CLI

```bash
python -m src.app --package data/sample_claims/realistic_package --claim-id CLM-001
```

### Streamlit UI

```bash
streamlit run src/ui/app.py
```

### MCP Servers

```bash
# Claim assessment server
python -m src.servers.claim_server

# Document extraction server
python -m src.servers.extraction_server

# Policy evaluation server
python -m src.servers.policy_server

# Invariant checking server
python -m src.servers.invariant_server
```

---

## Running Tests

```bash
python -m pytest tests/ -v
```

---

## Project Structure

```
ClaimGuard-MCP/
├── src/
│   ├── app.py                    # CLI entry point
│   ├── config.py                 # Settings (pydantic-settings)
│   ├── db/                       # Database schema and session
│   ├── evaluation/               # Policy, invariant, expense, damage checks
│   ├── extraction/               # Field extraction, document mapping
│   ├── ingestion/                # PDF/image ingestion, classification
│   ├── models/                   # Pydantic schemas
│   ├── orchestration/            # End-to-end claim processing
│   ├── reporting/                # Text and PDF report generation
│   ├── servers/                  # MCP server definitions
│   ├── services/                 # Database CRUD services
│   ├── ui/                       # Streamlit web interface
│   ├── utils/                    # Logging and utilities
│   └── vision/                   # Qwen2-VL API client
├── tests/                        # Pytest test suite
├── data/
│   ├── sample_claims/            # Test claim packages
│   └── policies/                 # Policy documents
├── reports/                      # Generated reports
├── scripts/                      # Utility scripts
├── requirements.txt
└── .env.example
```

---

## Evaluation Checks

| Check | Description | Severity on Fail |
|---|---|---|
| `POLICY_PERIOD` | Incident date within policy dates | FAIL |
| `POLICY_NUMBER_MATCH` | Claim ↔ Policy number consistency | FAIL |
| `VEHICLE_REGISTRATION_MATCH` | Claim ↔ Policy vehicle consistency | FAIL |
| `VEHICLE_REGISTRATION_CONSISTENCY` | Claim Form ↔ Policy vehicle | FAIL |
| `POLICY_NUMBER_CONSISTENCY` | Claim Form ↔ Policy number | FAIL |
| `CLAIMANT_NAME_CONSISTENCY` | Claimant ↔ Policy holder name | FAIL |
| `INCIDENT_DATE_CONSISTENCY` | Claim Form ↔ Police Report date | FAIL |
| `REPAIR_COST_WITHIN_COVERAGE` | Repair cost ≤ coverage limit | REVIEW |
| `REPAIR_COST_COMPONENTS_MATCH_TOTAL` | Parts + labor = total cost | REVIEW |
| `DAMAGE_AREA_CONSISTENCY` | Photo damage ↔ claim description | REVIEW |

---

## License

This project is for educational and demonstration purposes.
