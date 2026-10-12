import logging
import shutil
from pathlib import Path

import pymupdf
import pytesseract
from PIL import Image

from src.config import settings
from src.models.schemas import ExtractionResult

logger = logging.getLogger(__name__)

# Detect standard Windows installation path for Tesseract if not already on PATH
if not shutil.which("tesseract"):
    for _standard_path in [
        Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
        Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
        Path.home() / "AppData" / "Local" / "Programs" / "Tesseract-OCR" / "tesseract.exe",
    ]:
        if _standard_path.exists():
            pytesseract.pytesseract.tesseract_cmd = str(_standard_path)
            break


class ExtractionService:

    def __init__(self, languages: str | None = None) -> None:
        self._image_ocr_cache: dict[str, str] = {}
        self.languages = (
            languages
            if languages is not None
            else getattr(settings, "ocr_languages", "hin+eng+tam+tel")
        )

    def _run_tesseract(self, image: Image.Image) -> object:
        """
        Execute pytesseract with configured multi-language support (e.g. hin+eng+tam+tel).
        If the multi-language traineddata packages are missing from the local Tesseract installation,
        gracefully fall back to English ('eng').
        """
        try:
            return pytesseract.image_to_string(image, lang=self.languages)
        except Exception as exc:
            if self.languages and self.languages != "eng":
                try:
                    logger.debug(
                        "Multi-language OCR (%s) failed or language pack missing (%s). Falling back to 'eng'.",
                        self.languages,
                        exc,
                    )
                    return pytesseract.image_to_string(image, lang="eng")
                except Exception:
                    pass
            raise exc

    @staticmethod
    def _clean_ocr_text(raw_output: object) -> str:
        """
        Normalize OCR output from pytesseract or mocks into a clean stripped string.
        Pytesseract can return str, bytes, or dict depending on options and stubs.
        """
        if isinstance(raw_output, dict):
            text_val = raw_output.get("text", "")
            return str(text_val).strip() if text_val else ""
        if isinstance(raw_output, (bytes, bytearray)):
            return raw_output.decode("utf-8", errors="ignore").strip()
        if isinstance(raw_output, str):
            return raw_output.strip()
        return str(raw_output).strip() if raw_output is not None else ""

    def extract_text_from_pdf(self, file_path: str) -> str:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Document not found: {file_path}"
            )

        if path.suffix.lower() != ".pdf":
            raise ValueError(
                f"Expected a PDF file, got: {path.suffix}"
            )

        document = pymupdf.open(str(path))

        pages = []

        for page in document:
            raw_text = page.get_text()
            text = raw_text.strip() if isinstance(raw_text, str) else str(raw_text or "").strip()

            if len(text) < 50:
                # Scanned PDF or sparse text layer: render page to high-res image and run OCR
                try:
                    pix = page.get_pixmap(dpi=300)
                    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                    raw_ocr = self._run_tesseract(img)
                    ocr_text = self._clean_ocr_text(raw_ocr)
                    if ocr_text:
                        pages.append(ocr_text)
                    elif text:
                        pages.append(text)
                except Exception as exc:
                    logger.debug("OCR fallback for PDF page failed or Tesseract not installed: %s", exc)
                    if text:
                        pages.append(text)
            else:
                pages.append(text)

        document.close()

        return "\n\n".join(pages)

    def extract_text_from_image(self, file_path: str) -> str:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Image not found: {file_path}"
            )

        if path.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
            raise ValueError(
                f"Expected PNG, JPG, or JPEG image, got: {path.suffix}"
            )

        cache_key = str(path.resolve())
        if cache_key in self._image_ocr_cache:
            return self._image_ocr_cache[cache_key]

        try:
            image = Image.open(path)
            raw_text = self._run_tesseract(image)
            cleaned = self._clean_ocr_text(raw_text)
            self._image_ocr_cache[cache_key] = cleaned
            return cleaned
        except Exception as exc:
            logger.warning("Image OCR failed (is Tesseract installed?): %s", exc)
            return ""

    def extract_pdf_pages(self, file_path: str) -> list[ExtractionResult]:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Document not found: {file_path}"
            )

        if path.suffix.lower() != ".pdf":
            raise ValueError(
                f"Expected a PDF file, got: {path.suffix}"
            )

        document = pymupdf.open(str(path))

        results = []

        for page_number, page in enumerate(document, start=1):
            raw_text = page.get_text()
            text = raw_text.strip() if isinstance(raw_text, str) else str(raw_text or "").strip()
            source_type = "pdf_text"

            if len(text) < 50:
                # Scanned PDF fallback: render page to high-res image and run OCR
                try:
                    pix = page.get_pixmap(dpi=300)
                    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                    raw_ocr = self._run_tesseract(img)
                    ocr_text = self._clean_ocr_text(raw_ocr)
                    if ocr_text:
                        text = ocr_text
                        source_type = "pdf_ocr"
                except Exception as exc:
                    logger.debug("OCR fallback for PDF page %d failed: %s", page_number, exc)

            if text:
                results.append(
                    ExtractionResult(
                        document_id=path.stem,
                        page_number=page_number,
                        text=text,
                        source_type=source_type,
                    )
                )

        document.close()

        return results