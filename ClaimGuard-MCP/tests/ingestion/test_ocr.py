from PIL import Image, ImageDraw

from src.ingestion.extraction_service import ExtractionService


def test_extract_text_from_image(tmp_path):
    image_path = tmp_path / "test_document.png"

    image = Image.new("RGB", (1000, 300), "white")
    draw = ImageDraw.Draw(image)

    draw.text(
        (50, 50),
        "Date of Accident: 2026-08-10",
        fill="black",
    )

    draw.text(
        (50, 120),
        "Vehicle: ABC-1234",
        fill="black",
    )

    image.save(image_path)

    service = ExtractionService()

    text = service.extract_text_from_image(str(image_path))

    assert "2026-08-10" in text
    assert "ABC-1234" in text


def test_clean_ocr_text_with_various_types():
    # String input
    assert ExtractionService._clean_ocr_text("  hello world  ") == "hello world"

    # Dict input (the exact scenario where pytesseract / mocks return a dict)
    assert ExtractionService._clean_ocr_text({"text": "  scanned text  "}) == "scanned text"
    assert ExtractionService._clean_ocr_text({}) == ""

    # Bytes input
    assert ExtractionService._clean_ocr_text(b"  bytes text  ") == "bytes text"

    # None input
    assert ExtractionService._clean_ocr_text(None) == ""


def test_extraction_service_languages_configuration():
    # Default uses configured multi-language string
    service = ExtractionService()
    assert "hin" in service.languages
    assert "eng" in service.languages
    assert "tam" in service.languages
    assert "tel" in service.languages

    # Custom language string override
    custom_service = ExtractionService(languages="eng+fra")
    assert custom_service.languages == "eng+fra"


def test_run_tesseract_fallback_on_missing_language_pack(monkeypatch):
    import pytesseract
    service = ExtractionService(languages="hin+eng+tam+tel")

    call_history = []

    def fake_image_to_string(img, lang="eng", **kwargs):
        call_history.append(lang)
        if lang == "hin+eng+tam+tel":
            raise RuntimeError("Error opening data file /tessdata/hin.traineddata")
        return "Fallback English Scanned Text"

    monkeypatch.setattr(pytesseract, "image_to_string", fake_image_to_string)

    dummy_img = Image.new("RGB", (100, 100), "white")
    result = service._run_tesseract(dummy_img)

    assert result == "Fallback English Scanned Text"
    assert "hin+eng+tam+tel" in call_history
    assert "eng" in call_history