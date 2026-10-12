# ClaimGuard-MCP: Comprehensive Code Audit, Bugs, and Improvement Roadmap

---

## Executive Summary

This document provides an exhaustive, root-cause audit of the **ClaimGuard-MCP** codebase. It catalogues all identified bugs across four distinct severity levels (Critical, High, Medium, Low), explains the exact mechanism of each failure, and provides a concrete architectural roadmap of required improvements for production readiness.

---

## Table of Contents
1. [Bug Classification & Summary Matrix](#1-bug-classification--summary-matrix)
2. [Critical Bugs (Immediate Fix Required)](#2-critical-bugs)
3. [High-Priority Bugs (Data Quality & Extraction Failures)](#3-high-priority-bugs)
4. [Medium-Priority Bugs (Logic & Architectural Edge Cases)](#4-medium-priority-bugs)
5. [Low-Priority Issues & Technical Debt](#5-low-priority-issues)
6. [Required Project Improvements & Architectural Roadmap](#6-required-project-improvements)
7. [Implementation Action Plan](#7-implementation-action-plan)

---

## 1. Bug Classification & Summary Matrix

| ID | Component | Severity | Description | Impact |
| :--- | :--- | :--- | :--- | :--- |
| **BUG-01** | Orchestration / DB | **CRITICAL** | Claims, documents, policy evaluations, and invariant results are never saved to DuckDB during pipeline execution. | Database tables remain empty; audit history is lost. |
| **BUG-02** | Evaluation Pipeline | **CRITICAL** | `REPAIR_ESTIMATE` is omitted from `available_documents` set in `ClaimEvaluationPipeline`. | **[RESOLVED]** Added to `available_documents` tracking in pipeline. |
| **BUG-03** | Assessment Service | **CRITICAL** | `ClaimAssessmentService` collapses all `FAIL` verdicts into `REVIEW`. | **[RESOLVED]** 3-tier verdict logic (FAIL, REVIEW, PASS) implemented. |
| **BUG-04** | Document Mapper | **HIGH** | `_parse_date` uses strict `date.fromisoformat` (`YYYY-MM-DD` only). | Standard formats (`DD/MM/YYYY`, `DD-MM-YYYY`) evaluate to `None`, triggering false policy failures. |
| **BUG-05** | Classifier Service | **HIGH** | All image files (`.png`, `.jpg`, `.jpeg`) were unconditionally classified as `DAMAGE_PHOTO`. | **[RESOLVED]** Smart OCR-first classification checks images for insurance document keywords before routing to DAMAGE_PHOTO or structured extraction. |
| **BUG-06** | Ingestion / Extraction | **HIGH** | `extract_text_from_pdf` lacks OCR fallback for scanned/image-based PDFs. | **[RESOLVED]** High-res 300 DPI OCR fallback implemented (<50 chars threshold). |
| **BUG-07** | Database Schema | **MEDIUM** | Mismatch between `PolicyEvaluation` schema and `policy_evaluations` SQL table. | Fields `repair_cost`, `coverage_limit`, `deductible`, `estimated_payable` are dropped on insert. |
| **BUG-08** | Field Extraction | **MEDIUM** | Hardcoded `evidence_id = f"{document_id}-{field_name}"` creates primary key collisions. | Multi-page documents or recurring fields overwrite earlier evidence. |
| **BUG-09** | Field Extraction | **MEDIUM** | Rigid regex patterns fail on common synonymous document labels. | Real documents with `Claim #`, `Date of Loss`, `Insured Name` fail extraction. |
| **BUG-10** | Document Mapper | **MEDIUM** | `_parse_float` only cleans `₹` and `INR`, ignoring `$`, `USD`, `EUR`, `Rs.`, or spaces. | Any non-INR currency or formatted numbers fail to parse into floats. |
| **BUG-11** | Database Engine | **MEDIUM** | Single-writer file lock in DuckDB without connection pooling. | Concurrent writes from Streamlit UI, MCP servers, and background workers raise IO lock errors. |
| **BUG-12** | MCP Servers | **LOW** | Incomplete MCP server tool coverage for damage consistency and expense math. | External AI agents cannot call damage comparison or expense consistency independently. |
| **BUG-13** | Vision Client | **LOW** | Missing authentication headers and payload compression in `VisionAPIClient`. | Unsecured endpoints and large payload bandwidth overhead. |

---

## 2. Critical Bugs

### BUG-01: Disconnected Database Persistence in Orchestration Pipeline
* **Location:** [`src/orchestration/claim_package_service.py`](file:///c:/Users/T9934/Desktop/ClaimGuard-MCP/src/orchestration/claim_package_service.py#L61-L263)
* **The Problem:**
  When a claim package is processed through `ClaimPackageService.process_package()`, `StructuredExtractionService` saves individual evidence records to `extracted_evidence`. However:
  - `claim_service.create_claim(claim)` is **never called**.
  - `document_service.register_document(doc)` is **never called**.
  - `policy_service.save_evaluation(eval)` is **never called** for policy results.
  - `invariant_service.save_result(inv)` is **never called** for invariant results.
* **Impact:** 
  The DuckDB database only stores loose extracted fields. The core `claims`, `documents`, `policy_evaluations`, and `invariant_results` tables remain completely empty when running the UI or CLI package processing.
* **Fix Required:**
  Inject `ClaimService`, `DocumentService`, `PolicyService`, and `InvariantService` into `ClaimPackageService` and persist the entities during pipeline orchestration.

---

### BUG-02: `REPAIR_ESTIMATE` Omitted from `available_documents`
* **Location:** [`src/evaluation/claim_evaluation_pipeline.py`](file:///c:/Users/T9934/Desktop/ClaimGuard-MCP/src/evaluation/claim_evaluation_pipeline.py#L169-L185)
* **The Problem:**
  In Step 6 of `evaluate_claim()`, the set of available documents is initialized as:
  ```python
  available_documents = {"CLAIM_FORM", "POLICY"}
  if police_report is not None:
      available_documents.add("POLICE_REPORT")
  if damage_photo is not None:
      available_documents.add("DAMAGE_PHOTO")
  # REPAIR_ESTIMATE is missing here!
  ```
* **Impact:**
  Even when a valid `repair_estimate` is supplied and analyzed in Step 3, it is never added to `available_documents`. If `DocumentRequirementService` flags `REPAIR_ESTIMATE` as required, the system will falsely report `Required document is missing: REPAIR_ESTIMATE`.
* **Fix Required:**
  Add:
  ```python
  if repair_estimate is not None:
      available_documents.add("REPAIR_ESTIMATE")
  ```

---

### BUG-03: `ClaimAssessmentService` Collapses All Failures into `REVIEW`
* **Location:** [`src/evaluation/claim_assessment_service.py`](file:///c:/Users/T9934/Desktop/ClaimGuard-MCP/src/evaluation/claim_assessment_service.py#L115-L122)
* **The Problem:**
  The overall verdict logic treats failures and reviews identically:
  ```python
  if has_failures or has_review or has_missing_documents:
      overall_result = "REVIEW"
  else:
      overall_result = "PASS"
  ```
* **Impact:**
  The system is incapable of returning `"FAIL"` or `"REJECT"`. A blatantly fraudulent claim (e.g., mismatched registration plate or claim filed 2 years after policy expiry) receives the same `"REVIEW"` status as a claim that is merely missing a receipt. Automated STP (Straight-Through Processing) triage pipelines cannot distinguish fraud from minor incompleteness.
* **Fix Required:**
  Implement a three-tier or four-tier assessment state:
  ```python
  if has_failures:
      overall_result = "FAIL"
  elif has_review or has_missing_documents:
      overall_result = "REVIEW"
  else:
      overall_result = "PASS"
  ```

---

## 3. High-Priority Bugs

### BUG-04: Rigid ISO Date Parsing (`date.fromisoformat`)
* **Location:** [`src/extraction/document_mapper_service.py`](file:///c:/Users/T9934/Desktop/ClaimGuard-MCP/src/extraction/document_mapper_service.py#L17-L25)
* **The Problem:**
  `_parse_date()` calls `date.fromisoformat(value.strip())`, which strictly accepts `YYYY-MM-DD`. In real insurance documents (India, UK, Europe, Australia), dates are commonly formatted as `DD/MM/YYYY`, `DD-MM-YYYY`, `MM/DD/YYYY`, or `15-Oct-2024`.
* **Impact:**
  Valid dates fail parsing silently and return `None`. When `incident_date` or `policy_start_date` is `None`, the policy coverage check reports:
  *"Incident date is missing, so policy-period coverage cannot be determined"*, generating false-positive review alerts.
* **Fix Required:**
  Replace with a flexible multi-format parser:
  ```python
  from datetime import datetime

  SUPPORTED_FORMATS = [
      "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y",
      "%m/%d/%Y", "%d %b %Y", "%d %B %Y",
  ]
  for fmt in SUPPORTED_FORMATS:
      try:
          return datetime.strptime(value.strip(), fmt).date()
      except ValueError:
          continue
  ```

---

### BUG-05: Blind Image Classification as `DAMAGE_PHOTO` **[RESOLVED]**
* **Location:** [`src/ingestion/document_classifier_service.py`](file:///c:/Users/T9934/Desktop/ClaimGuard-MCP/src/ingestion/document_classifier_service.py), [`src/orchestration/claim_package_service.py`](file:///c:/Users/T9934/Desktop/ClaimGuard-MCP/src/orchestration/claim_package_service.py)
* **The Problem:**
  Previously, the classifier unconditionally assigned any image file (`.png`, `.jpg`, `.jpeg`) to `DAMAGE_PHOTO` when text was not provided, and `ClaimPackageService` bypassed text extraction for all image files.
* **Impact:**
  If a customer submitted photos or scans of their police report, repair estimate bill, or driving license as a JPEG/PNG, the system treated it as a vehicle exterior damage photo, losing text evidence.
* **Resolution:**
  1. `DocumentClassifierService` runs OCR on image files first via `ExtractionService.extract_text_from_image()`.
  2. If the OCR text contains insurance document keywords (`"police station"`, `"FIR"`, `"repair estimate"`, `"policy"`, `"claim form"`, `"hospital"`), it classifies it as the appropriate text document (`POLICE_REPORT`, `REPAIR_ESTIMATE`, `POLICY`, `CLAIM_FORM`, `MEDICAL_BILL`).
  3. If no insurance document keywords match or OCR returns empty text, it classifies it as `DAMAGE_PHOTO`.
  4. `ClaimPackageService` routes scanned image documents through `StructuredExtractionService` + `DocumentMapperService` while true vehicle damage photos route to `VisionExtractionService`.
  5. OCR caching is enabled in `ExtractionService` to avoid redundant OCR passes.

---

### BUG-06: No OCR Fallback for Scanned PDF Files
* **Location:** [`src/ingestion/extraction_service.py`](file:///c:/Users/T9934/Desktop/ClaimGuard-MCP/src/ingestion/extraction_service.py#L25-L38)
* **The Problem:**
  `extract_text_from_pdf` only extracts digital text layers using `page.get_text()`. If a PDF consists of scanned pages or photocopies, `page.get_text()` returns an empty string.
* **Impact:**
  Scanned PDFs yield 0 bytes of text. The classifier assigns `DocumentType.OTHER`, and 0 evidence fields are extracted.
* **Fix Required:**
  If `page.get_text().strip()` is empty, render the page using `page.get_pixmap()` and run `pytesseract.image_to_string()`.

---

## 4. Medium-Priority Bugs

### BUG-07: SQL Schema vs Pydantic Model Discrepancy in `policy_evaluations`
* **Location:** [`src/db/schema.py`](file:///c:/Users/T9934/Desktop/ClaimGuard-MCP/src/db/schema.py#L56-L64) vs [`src/models/schemas.py`](file:///c:/Users/T9934/Desktop/ClaimGuard-MCP/src/models/schemas.py#L43-L56)
* **The Problem:**
  `PolicyEvaluation` schema in Pydantic includes:
  `repair_cost`, `coverage_limit`, `deductible`, `estimated_payable`.
  However, the `policy_evaluations` table in `schema.py` and the insert statements in `PolicyService.save_evaluation()` only define 5 columns:
  `(evaluation_id, claim_id, rule_id, result, explanation)`.
* **Impact:** Financial calculation outcomes are dropped when persisting evaluation results.

---

### BUG-08: Evidence ID Collision in Multi-Page Documents
* **Location:** [`src/extraction/field_extraction_service.py`](file:///c:/Users/T9934/Desktop/ClaimGuard-MCP/src/extraction/field_extraction_service.py#L110)
* **The Problem:**
  `evidence_id` is computed as `f"{document_id}-{field_name}"`. In multi-page or repeating documents, any recurring field has identical `evidence_id`s. Because DuckDB executes `ON CONFLICT (evidence_id) DO UPDATE`, earlier page occurrences are overwritten.
* **Fix Required:**
  Include the page number or a UUID suffix: `f"{document_id}-p{page_number or 1}-{field_name}"`.

---

### BUG-09: Brittle Field Extraction Regexes
* **Location:** [`src/extraction/field_extraction_service.py`](file:///c:/Users/T9934/Desktop/ClaimGuard-MCP/src/extraction/field_extraction_service.py#L12-L60)
* **The Problem:**
  `FIELD_PATTERNS` relies on exact phrases:
  - `Claimant Name:\s*(.+)` misses `Insured:`, `Name of Insured:`, `Claimant:`
  - `Incident Date:\s*(.+)` misses `Date of Loss:`, `Accident Date:`, `Date of Incident:`
  - `Vehicle Registration:\s*(.+)` misses `Reg No:`, `Registration #:`, `Plate No:`
* **Fix Required:** Expand regex dictionaries with broader synonym anchors and token boundary assertions.

---

### BUG-10: Incomplete Currency & Float Parsing
* **Location:** [`src/extraction/document_mapper_service.py`](file:///c:/Users/T9934/Desktop/ClaimGuard-MCP/src/extraction/document_mapper_service.py#L27-L42)
* **The Problem:**
  `_parse_float()` only removes commas, `INR`, and `₹`. If a claim features `$`, `USD`, `EUR`, `Rs.`, or trailing `/-` (e.g., `Rs. 45,000/-`), float conversion fails and returns `None`.

---

### BUG-11: DuckDB Concurrency File Locking
* **Location:** [`src/db/session.py`](file:///c:/Users/T9934/Desktop/ClaimGuard-MCP/src/db/session.py#L21)
* **The Problem:**
  `duckdb.connect(str(database_path))` defaults to read-write mode. DuckDB locks the file exclusively for writes. If the Streamlit application and an MCP server or CLI command run simultaneously, DuckDB raises:
  `duckdb.IOException: Could not set lock on file`.
* **Fix Required:**
  Provide a `read_only=True` parameter option for read queries, and catch lock timeouts.

---

## 5. Low-Priority Issues & Technical Debt

### BUG-12: Incomplete MCP Server Tool Coverage
* **Location:** [`src/servers/invariant_server.py`](file:///c:/Users/T9934/Desktop/ClaimGuard-MCP/src/servers/invariant_server.py)
* **The Problem:**
  `invariant_server.py` exposes 5 specific check tools, but omits:
  - Damage area consistency (`DamageConsistencyService`)
  - Expense arithmetic consistency (`ExpenseConsistencyService`)
  Agents connecting over MCP cannot access the complete invariant toolsuite.

---

### BUG-13: Vision API Client Security & Payload Handling
* **Location:** [`src/vision/vision_api_client.py`](file:///c:/Users/T9934/Desktop/ClaimGuard-MCP/src/vision/vision_api_client.py#L68-L74)
* **The Problem:**
  No bearer authentication token header is passed, and uncompressed high-resolution images are converted to multi-megabyte base64 strings, potentially causing request timeout or payload size limit errors on standard reverse proxies.

---

## 6. Required Project Improvements & Architectural Roadmap

### Improvement 1: Full-Pipeline Automatic Database Logging
Update `ClaimPackageService.process_package()` to execute a complete transactional persistence loop:
1. Save `Claim` entity via `ClaimService.create_claim()`.
2. Save every ingested file via `DocumentService.register_document()`.
3. Save extracted fields via `EvidenceService.save_evidence()`.
4. Save policy check outcomes via `PolicyService.save_evaluation()`.
5. Save invariant checks via `InvariantService.save_result()`.

---

### Improvement 2: Multi-Tier Extraction (Regex + LLM Fallback) **[IMPLEMENTED]**
Regex extraction is fast and deterministic, but rigid. Implemented a **two-tier extraction strategy**:
- **Tier 1 (Fast Regex)**: Instant extraction for standard forms via `FieldExtractionService`.
- **Tier 2 (LLM Fallback)**: If critical fields (`policy_number`, `incident_date`, `vehicle_registration`) are missing/None, `StructuredExtractionService` triggers `LLMExtractionService` with strict JSON schema enforcement supporting both OpenAI (`gpt-4o-mini`) and Google Gemini (`gemini-1.5-flash`) APIs.

---

### Improvement 3: Robust OCR & Multi-Language Document Pipeline **[RESOLVED - Task 2.3]**
Enhance `ExtractionService`:
- Detect scanned PDFs via text density checks (`len(page.get_text()) < 50`).
- Convert PDF pages to images via `PyMuPDF` (`page.get_pixmap()`).
- Multi-language Tesseract OCR configured with `lang='hin+eng+tam+tel'` and graceful English fallback if regional language packs are missing.
- Centralized `TranslationService`:
  - Indic numeral normalization across Devanagari, Telugu, Tamil, Bengali, and Gujarati numerals (`०-९`, `౦-౯`, `௦-௯`).
  - Rule-based phonetic transliteration & vocabulary dictionary for common names, terms, and Indian cities.
  - LLM-powered (Gemini/OpenAI) translation pipeline for fluent, contextual field translation of non-English claims.
- Regional language keyword detection in `DocumentClassifierService` (Hindi, Tamil, Telugu, Marathi).

---

### Improvement 4: Multi-Format Date & Currency Engine
Introduce a centralized normalizer utility:
- Use `python-dateutil.parser` with fuzzy matching.
- Standardize all currency amounts into a common base unit, supporting exchange rates and tax tolerances (e.g., GST ±18% validation for labor/parts).

---

### Improvement 5: True Fraud Decision Hierarchy
Refactor the verdict aggregation in `ClaimAssessmentService`:
- **`APPROVED / PASS`**: All documents present, policy active, registration identical, expenses add up, damage photo matches.
- **`SUSPICIOUS / REVIEW`**: Missing non-critical documents, ambiguous damage description, partial text match.
- **`FRAUD_ALERT / REJECT`**: Policy expired at incident date, registration plate mismatch between police FIR and policy, forged repair totals.
- **Confidence Scoring**: Compute a composite fraud risk score (0.0 to 100.0%).

---

### Improvement 6: Unified FastMCP Server Architecture
Consolidate or update all servers in `src/servers/` to expose:
1. Complete claim package evaluation.
2. Individual tool invocations (policy check, invariant check, expense check, damage photo analysis).
3. Document extraction tools.
4. DuckDB query and audit-trail retrieval tools.

---

### Improvement 7: Production-Grade Async & Concurrency Management
- Wrap DuckDB write operations with retry backoff or migrate to PostgreSQL / Supabase for multi-user production deployments.
- Allow read-only DuckDB connections for the Streamlit UI database explorer and MCP query tools.
- Implement an asynchronous task queue (FastAPI BackgroundTasks or Celery) for large document batches.

---

## 7. Implementation Action Plan

```mermaid
flowchart TD
    subgraph Phase 1: Critical Bug Fixes
        B1[Fix BUG-01: Connect DB Persistence in Pipeline]
        B2[Fix BUG-02: Add REPAIR_ESTIMATE to Available Docs]
        B3[Fix BUG-03: Implement 3-Tier PASS/REVIEW/FAIL Verdict]
    end

    subgraph Phase 2: Ingestion & Extraction Robustness
        B4[Fix BUG-04 & BUG-10: Multi-format Date & Currency Parsers]
        B5[Fix BUG-05 & BUG-06: Scanned PDF OCR Fallback & Intelligent Classifier]
        B6[Fix BUG-08 & BUG-09: Unique Evidence IDs & Broad Synonyms]
    end

    subgraph Phase 3: Architectural & MCP Enhancements
        B7[Fix BUG-07: Sync SQL Schema with Pydantic Models]
        B8[Fix BUG-11: Read-Only DuckDB Concurrency]
        B9[Fix BUG-12: Full MCP Server Tool Coverage]
    end

    Phase 1 --> Phase 2
    Phase 2 --> Phase 3
```

---
*Report generated for ClaimGuard-MCP codebase review.*
