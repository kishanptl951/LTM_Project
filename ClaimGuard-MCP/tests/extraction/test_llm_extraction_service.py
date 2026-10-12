import json
from unittest.mock import MagicMock, patch

import pytest

from src.extraction.llm_extraction_service import (
    DEFAULT_EXTRACTION_SCHEMA,
    LLMExtractionService,
)
from src.extraction.structured_extraction_service import (
    StructuredExtractionService,
)
from src.ingestion.document_classifier_service import DocumentType


def test_llm_extraction_service_openai_config():
    service = LLMExtractionService(
        provider="openai",
        api_key="sk-test-key-12345",
        model="gpt-4o-mini",
    )
    assert service.provider == "openai"
    assert service.api_key == "sk-test-key-12345"
    assert service.model == "gpt-4o-mini"
    assert service.is_available() is True


def test_llm_extraction_service_gemini_config():
    service = LLMExtractionService(
        provider="gemini",
        api_key="AIzaSyTestGeminiKey",
        model="gemini-1.5-flash",
    )
    assert service.provider == "gemini"
    assert service.api_key == "AIzaSyTestGeminiKey"
    assert service.model == "gemini-1.5-flash"
    assert service.is_available() is True


def test_llm_extraction_service_unavailable_without_key():
    service = LLMExtractionService(
        provider="openai",
        api_key="",
    )
    assert service.is_available() is False
    # Calling extract_fields with no key returns empty dict gracefully
    result = service.extract_fields("Policy Number: POL-001")
    assert result == {}


def test_llm_extraction_service_with_mock_client():
    def mock_llm_caller(text: str, schema: dict) -> dict:
        assert "POL-MOCK-999" in text
        return {
            "policy_number": "POL-MOCK-999",
            "vehicle_registration": "KA01AB9999",
            "incident_date": "2026-07-15",
            "claimant_name": "Priya Nair",
        }

    service = LLMExtractionService(client=mock_llm_caller)
    assert service.is_available() is True

    result = service.extract_fields(
        text="The insured Priya Nair had an accident in vehicle KA01AB9999 under POL-MOCK-999.",
        missing_fields=["policy_number", "vehicle_registration"],
    )

    assert result["policy_number"] == "POL-MOCK-999"
    assert result["vehicle_registration"] == "KA01AB9999"


def test_llm_extraction_service_parses_markdown_json_blocks():
    service = LLMExtractionService(api_key="dummy-key")
    schema = DEFAULT_EXTRACTION_SCHEMA

    raw_response = """```json
    {
        "policy_number": "POL-CLEAN-777",
        "vehicle_registration": "MH12XY4321",
        "incident_date": "2026-04-12",
        "null_field": null,
        "empty_field": "None"
    }
    ```"""

    cleaned = service._parse_json_payload(raw_response, schema)
    assert cleaned["policy_number"] == "POL-CLEAN-777"
    assert cleaned["vehicle_registration"] == "MH12XY4321"
    assert cleaned["incident_date"] == "2026-04-12"
    assert "null_field" not in cleaned
    assert "empty_field" not in cleaned


@patch("requests.post")
def test_openai_api_call(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "policy_number": "POL-OPENAI-101",
                        "vehicle_registration": "DL01ZZ1234",
                    })
                }
            }
        ]
    }
    mock_post.return_value = mock_response

    service = LLMExtractionService(
        provider="openai",
        api_key="sk-test-123",
        model="gpt-4o-mini",
    )

    extracted = service.extract_fields(
        text="Sample claim notes for DL01ZZ1234 covered by POL-OPENAI-101",
        missing_fields=["policy_number", "vehicle_registration"],
    )

    assert extracted["policy_number"] == "POL-OPENAI-101"
    assert extracted["vehicle_registration"] == "DL01ZZ1234"
    assert mock_post.called


@patch("requests.post")
def test_gemini_api_call(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps({
                                "policy_number": "POL-GEMINI-202",
                                "incident_date": "2026-06-20",
                            })
                        }
                    ]
                }
            }
        ]
    }
    mock_post.return_value = mock_response

    service = LLMExtractionService(
        provider="gemini",
        api_key="AIzaSyTestKey",
        model="gemini-1.5-flash",
    )

    extracted = service.extract_fields(
        text="Loss recorded on 2026-06-20 under coverage POL-GEMINI-202",
        missing_fields=["policy_number", "incident_date"],
    )

    assert extracted["policy_number"] == "POL-GEMINI-202"
    assert extracted["incident_date"] == "2026-06-20"
    assert mock_post.called


def test_2_tier_extraction_skips_llm_when_regex_succeeds(tmp_path):
    """
    Tier 1 Regex extracts all critical fields.
    Tier 2 LLM should NEVER be called.
    """
    llm_mock = MagicMock()
    llm_service = LLMExtractionService(client=llm_mock)

    doc_path = tmp_path / "claim.txt"
    doc_path.write_text(
        "Claim ID: CLM-001\n"
        "Policy Number: POL-2026-001\n"
        "Incident Date: 2026-08-10\n"
        "Vehicle Registration: TS09AB1234\n",
        encoding="utf-8",
    )

    service = StructuredExtractionService(
        llm_extraction_service=llm_service,
    )

    # Mock text extraction & classifier
    service.extraction_service.extract_text_from_pdf = MagicMock(
        return_value=doc_path.read_text(encoding="utf-8")
    )
    service.classifier_service.classify = MagicMock(
        return_value=DocumentType.CLAIM_FORM
    )

    dummy_pdf = tmp_path / "claim.pdf"
    dummy_pdf.write_text("dummy", encoding="utf-8")

    result = service.process_document(
        file_path=str(dummy_pdf),
        claim_id="CLM-001",
        document_id="DOC-001",
    )

    assert result.extracted_data["policy_number"] == "POL-2026-001"
    assert result.extracted_data["incident_date"] == "2026-08-10"
    assert result.extracted_data["vehicle_registration"] == "TS09AB1234"
    # LLM was never called because Tier 1 found everything
    assert not llm_mock.called


def test_2_tier_extraction_llm_fallback_merges_missing_fields(tmp_path):
    """
    Tier 1 Regex misses non-standard phrasing like 'Ref Policy #:' or 'Date of Loss:'.
    Tier 2 LLM is triggered and successfully extracts and merges missing critical fields.
    """
    # Non-standard document text that regex will fail on for vehicle registration
    non_standard_text = (
        "Claim Reference: CLM-IRREGULAR-99\n"
        "Coverage Plan Reference Code: POL-NONSTD-888\n"
        "Loss Occurred on: 15/09/2026\n"
        "Automobile Plate: TS09XYZ9999\n"
    )

    def mock_llm_extractor(text: str, schema: dict) -> dict:
        return {
            "policy_number": "POL-NONSTD-888",
            "incident_date": "15/09/2026",
            "vehicle_registration": "TS09XYZ9999",
        }

    llm_service = LLMExtractionService(client=mock_llm_extractor)
    service = StructuredExtractionService(
        llm_extraction_service=llm_service,
    )

    dummy_pdf = tmp_path / "claim.pdf"
    dummy_pdf.write_text("dummy", encoding="utf-8")

    service.extraction_service.extract_text_from_pdf = MagicMock(
        return_value=non_standard_text
    )
    service.classifier_service.classify = MagicMock(
        return_value=DocumentType.CLAIM_FORM
    )

    result = service.process_document(
        file_path=str(dummy_pdf),
        claim_id="CLM-IRREGULAR-99",
        document_id="DOC-IRREGULAR-99",
    )

    # Critical fields extracted via Tier-2 LLM fallback
    assert result.extracted_data.get("policy_number") == "POL-NONSTD-888"
    assert result.extracted_data.get("vehicle_registration") == "TS09XYZ9999"


def test_2_tier_field_extraction_method_on_service():
    """
    Direct invocation of extract_fields_with_llm_fallback on FieldExtractionService.
    """
    from src.extraction.field_extraction_service import FieldExtractionService

    service = FieldExtractionService()
    text = (
        "Notice of Claim.\n"
        "Policy Identifier: POL-DIRECT-555\n"
        "Plate Number: DL09AA1111\n"
    )

    def mock_llm(text: str, schema: dict) -> dict:
        return {
            "policy_number": "POL-DIRECT-555",
            "vehicle_registration": "DL09AA1111",
            "incident_date": "2026-03-10",
        }

    llm_service = LLMExtractionService(client=mock_llm)

    evidence_list = service.extract_fields_with_llm_fallback(
        text=text,
        claim_id="CLM-DIR",
        document_id="DOC-DIR",
        llm_service=llm_service,
    )

    evidence_dict = {e.field_name: e.field_value for e in evidence_list}
    assert "policy_number" in evidence_dict
    assert "vehicle_registration" in evidence_dict
    assert evidence_dict.get("incident_date") == "2026-03-10"
