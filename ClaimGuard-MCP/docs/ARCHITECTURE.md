# ClaimGuard-MCP Architecture & Execution Flow

ClaimGuard-MCP is an end-to-end multimodal insurance claim consistency and fraud arbiter that validates claim packages containing structured documents (claim forms, police reports, repair estimates, policies) and visual evidence (damage photos).

```
+--------------------------------------------------------------------+
|                         Input Sources                              |
|  CLI (`src/app.py`) | Web UI (`src/ui/app.py`) | MCP Servers       |
+---------------------------------+----------------------------------+
                                  |
                                  v
+--------------------------------------------------------------------+
|                    ClaimPackageService                             |
|          (src/orchestration/claim_package_service.py)              |
+---------------------------------+----------------------------------+
         |                                           |
         v (PDF / Text)                              v (Images: JPG, PNG)
+----------------------------------+      +--------------------------+
|  StructuredExtractionService     |      | VisionExtractionService  |
|  - Ingestion (PyMuPDF / OCR)     |      | - Remote Vision Client   |
|  - ClassificationService         |      |   (Qwen2-VL API)         |
|  - DocumentMapperService         |      | - DamagePhotoDocument    |
+----------------------------------+      +--------------------------+
         |                                           |
         +--------------------+----------------------+
                              |
                              v
+--------------------------------------------------------------------+
|                   ClaimEvaluationPipeline                          |
|         (src/evaluation/claim_evaluation_pipeline.py)              |
|                                                                    |
|  1. PolicyEvaluationService:                                       |
|     - Coverage date validation (active during incident)            |
|     - Vehicle registration match (policy vs claim)                 |
|     - Policy holder name match                                     |
|                                                                    |
|  2. InvariantEvaluationService:                                    |
|     - Incident date consistency (claim vs police report)           |
|     - Vehicle registration across all documents                    |
|     - Policy number across all documents                           |
|     - Claimant identity consistency                                |
|                                                                    |
|  3. ExpenseEvaluationService & ExpenseConsistencyService:          |
|     - Parts + Labor = Total repair declared (with float tolerance) |
|     - Repair estimate <= Coverage limit                            |
|     - Deductible calculation & payable computation                 |
|                                                                    |
|  4. DamageConsistencyService:                                      |
|     - Visual damage area matches repair estimate descriptions      |
|     - Damage severity consistency                                  |
|                                                                    |
|  5. DocumentRequirementService:                                    |
|     - Required document completeness (e.g. photos for motor claims)|
+---------------------------------+----------------------------------+
                                  |
                                  v
+--------------------------------------------------------------------+
|                    ClaimAssessmentService                          |
|  - Evaluates results (PASS vs REVIEW)                              |
|  - Compiles actionable review reasons                              |
|  - Counts corroborating evidence artifacts                         |
+---------------------------------+----------------------------------+
                                  |
         +------------------------+-------------------------+
         v                                                  v
+----------------------------------+      +--------------------------+
|          Report Generation       |      |    Storage / Database    |
|  - Text Report (ReportService)   |      |  - DuckDB Database       |
|  - PDF Report (PDFReportService) |      |  - Claim & Document Logs |
|  - Streamlit UI Dashboard        |      |  - Evidence Records      |
+----------------------------------+      +--------------------------+
```

## Module Directory Structure

| Module | Description |
|---|---|
| `src/ingestion/` | PDF extraction via PyMuPDF and OCR via Tesseract |
| `src/classification/` | Keyword-based classification into document types |
| `src/extraction/` | Regex & pattern-based field extraction into Pydantic models |
| `src/evaluation/` | Rule engines for policies, invariants, expenses, and visual damage |
| `src/vision/` | REST client connecting to Qwen2-VL vision models |
| `src/orchestration/` | End-to-end package coordination |
| `src/reporting/` | Text and professional PDF reports via ReportLab |
| `src/servers/` | MCP (Model Context Protocol) tool servers for AI agents |
| `src/ui/` | Streamlit interactive web dashboard |
| `src/db/` | DuckDB schema, context manager session handler, and services |
