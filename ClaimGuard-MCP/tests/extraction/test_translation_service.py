from unittest.mock import MagicMock
from src.extraction.translation_service import TranslationService


def test_normalize_indic_digits():
    # Devanagari numerals
    assert TranslationService.normalize_indic_digits("२०२६-०९-०५") == "2026-09-05"
    assert TranslationService.normalize_indic_digits("₹५०,०००") == "₹50,000"
    assert TranslationService.normalize_indic_digits("टीएस ०९ एबी १२३४") == "टीएस 09 एबी 1234"

    # Telugu numerals
    assert TranslationService.normalize_indic_digits("౨౦౨౬-౦౯-౦౫") == "2026-09-05"
    assert TranslationService.normalize_indic_digits("₹౫౦,౦౦౦") == "₹50,000"

    # Tamil numerals
    assert TranslationService.normalize_indic_digits("₹௫௦,௦௦௦") == "₹50,000"

    # Mixed / standard ASCII remains intact
    assert TranslationService.normalize_indic_digits("POL-2026-001") == "POL-2026-001"


def test_is_non_latin():
    assert TranslationService.is_non_latin("राहुल शर्मा") is True
    assert TranslationService.is_non_latin("சுரேஷ் குமார்") is True
    assert TranslationService.is_non_latin("వెంకట రావు") is True
    assert TranslationService.is_non_latin("Rahul Sharma") is False
    assert TranslationService.is_non_latin("POL-2026-001") is False
    assert TranslationService.is_non_latin("") is False


def test_transliterate_text_offline():
    service = TranslationService()

    # Common Hindi name
    result = service.transliterate_text_offline("राहुल शर्मा")
    assert "Rahul" in result
    assert "Sharma" in result

    # Name with Indic numerals
    result_digits = service.transliterate_text_offline("अमित कुमार २०२६")
    assert "Amit" in result_digits
    assert "Kumar" in result_digits
    assert "2026" in result_digits

    # Common insurance terms
    result_terms = service.transliterate_text_offline("कार दुर्घटना मरम्मत")
    assert "car" in result_terms.lower()
    assert "accident" in result_terms.lower()
    assert "repair" in result_terms.lower()


def test_translate_fields_offline():
    # Offline scenario (no LLM)
    mock_llm = MagicMock()
    mock_llm.is_available.return_value = False
    service = TranslationService(llm_extraction_service=mock_llm)

    raw_fields = {
        "claimant_name": "राहुल शर्मा",
        "incident_date": "२०२६-०९-०५",
        "estimated_cost": "₹८५,०००",
        "policy_number": "POL-2026-001",
    }

    translated = service.translate_fields(raw_fields)

    assert "Rahul" in translated["claimant_name"]
    assert "Sharma" in translated["claimant_name"]
    assert translated["incident_date"] == "2026-09-05"
    assert translated["estimated_cost"] == "₹85,000"
    assert translated["policy_number"] == "POL-2026-001"


def test_translate_fields_with_llm():
    # LLM available scenario
    mock_llm = MagicMock()
    mock_llm.is_available.return_value = True
    mock_llm.provider = "gemini"
    mock_llm._call_gemini.return_value = """{
        "claimant_name": "Rahul Sharma",
        "incident_description": "Car and truck collision on highway",
        "vehicle_registration": "MH 12 AB 1234"
    }"""
    mock_llm._parse_json_response.return_value = {
        "claimant_name": "Rahul Sharma",
        "incident_description": "Car and truck collision on highway",
        "vehicle_registration": "MH 12 AB 1234",
    }

    service = TranslationService(llm_extraction_service=mock_llm)

    raw_fields = {
        "claimant_name": "राहुल शर्मा",
        "incident_description": "कार और ट्रक की टक्कर",
        "vehicle_registration": "एमएच १२ एबी १२३४",
        "incident_date": "२०२६-०९-०५",
    }

    translated = service.translate_fields(raw_fields)

    assert translated["claimant_name"] == "Rahul Sharma"
    assert translated["incident_description"] == "Car and truck collision on highway"
    assert translated["vehicle_registration"] == "MH 12 AB 1234"
    assert translated["incident_date"] == "2026-09-05"
