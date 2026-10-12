import io
import fitz
from PIL import Image, ImageDraw

from src.models.schemas import ExtractionResult
from src.ingestion.extraction_service import ExtractionService


def test_extract_text_from_pdf(tmp_path):
    pdf_path = tmp_path / "test_document.pdf"

    document = fitz.open()

    page = document.new_page()

    page.insert_text(
        (72, 72),
        "ClaimGuard Test Document\n"
        "Date of Accident: 2026-08-10\n"
        "Vehicle: ABC-1234"
    )

    document.save(str(pdf_path))
    document.close()

    service = ExtractionService()

    text = service.extract_text_from_pdf(str(pdf_path))

    assert "ClaimGuard Test Document" in text
    assert "Date of Accident: 2026-08-10" in text
    assert "Vehicle: ABC-1234" in text


def test_extraction_result_model():
    result = ExtractionResult(
        document_id="DOC-001",
        page_number=1,
        text="Vehicle accident reported on 10 September 2026.",
        source_type="ocr",
    )

    assert result.document_id == "DOC-001"
    assert result.page_number == 1
    assert result.text.startswith("Vehicle accident")
    assert result.source_type == "ocr"


def test_extract_pdf_pages():
    service = ExtractionService()

    results = service.extract_pdf_pages(
        "data/sample_claims/sample_claim.pdf"
    )

    assert isinstance(results, list)
    assert len(results) > 0

    first_result = results[0]

    assert first_result.document_id == "sample_claim"
    assert first_result.page_number == 1
    assert first_result.text
    assert first_result.source_type == "pdf_text"


def test_extract_scanned_pdf_fallback(tmp_path):
    pdf_path = tmp_path / "scanned_doc.pdf"

    # Create image containing text to simulate a scanned document page
    img = Image.new("RGB", (800, 200), "white")
    draw = ImageDraw.Draw(img)
    draw.text((30, 50), "Policy Number: POL-SCAN-777", fill="black")
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    # Insert image into a PDF without any digital text layer
    doc = fitz.open()
    page = doc.new_page(width=800, height=200)
    page.insert_image(page.rect, stream=buf.getvalue())
    doc.save(str(pdf_path))
    doc.close()

    service = ExtractionService()
    text = service.extract_text_from_pdf(str(pdf_path))
    assert isinstance(text, str)

    pages = service.extract_pdf_pages(str(pdf_path))
    assert isinstance(pages, list)
    if pages:
        assert pages[0].source_type in {"pdf_ocr", "pdf_text"}