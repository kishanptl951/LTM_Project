"""
SEC Parser: Uses BeautifulSoup4 to split 10-K HTML filings strictly by regulatory section boundaries.
(Item 1A: Risk Factors, Item 7: MD&A, Item 8: Notes & Footnotes)
"""
import re
import logging
import warnings
from typing import Dict
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

logger = logging.getLogger(__name__)

# Suppress XML parsed as HTML warning when handling XHTML/XML EDGAR filings
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


class SECParser:
    """
    Parses raw SEC 10-K HTML filing documents and extracts key regulatory sections:
    - Item 1A: Risk Factors
    - Item 7: Management's Discussion and Analysis (MD&A)
    - Item 8: Financial Statements and Supplementary Data / Notes & Footnotes
    """

    def __init__(self):
        # Section regex match patterns (flexible to handle 10-K and 10-Q headings)
        self.patterns = {
            "item_1a_start": r"(?:ITEM\s+1A[.\s\:\-–—]+RISK\s+FACTORS|(?:PART\s+II[.\s\:\-–—]+)?ITEM\s+1A[.\s\:\-–—]+RISK\s+FACTORS)",
            "item_1a_end": r"(?:ITEM\s+(?:1B|2)|(?:PART\s+II[.\s\:\-–—]+)?ITEM\s+2)[.\s\:\-–—]+(?:UNRESOLVED|PROPERTIES|ITEM\s+7|UNREGISTERED)",
            "item_7_start": r"(?:ITEM\s+7[.\s\:\-–—]+MANAGEMENT[’\'\s]*S\s+DISCUSSION|(?:PART\s+I[.\s\:\-–—]+)?ITEM\s+2[.\s\:\-–—]+MANAGEMENT[’\'\s]*S\s+DISCUSSION)",
            "item_7_end": r"(?:ITEM\s+(?:7A|8)|(?:PART\s+I[.\s\:\-–—]+)?ITEM\s+3)[.\s\:\-–—]+(?:QUANTITATIVE|FINANCIAL\s+STATEMENTS)",
            "item_8_start": r"(?:ITEM\s+8[.\s\:\-–—]+FINANCIAL\s+STATEMENTS|(?:PART\s+I[.\s\:\-–—]+)?ITEM\s+1[.\s\:\-–—]+FINANCIAL\s+STATEMENTS)",
            "item_8_end": r"(?:ITEM\s+(?:9[A-Z]?|10)|(?:PART\s+I[.\s\:\-–—]+)?ITEM\s+2)[.\s\:\-–—]+(?:CHANGES|CONTROLS|DIRECTORS|MANAGEMENT)",
        }

    def _html_to_text(self, html_content: str) -> str:
        """Converts raw HTML to normalized plain text."""
        if not html_content or not html_content.strip():
            return ""

        # If already plain text (no html tags)
        if "<html" not in html_content.lower() and "<body" not in html_content.lower() and "<div" not in html_content.lower():
            text = html_content
        else:
            soup = BeautifulSoup(html_content, "html.parser")
            text = soup.get_text("\n")

        # Normalize unicode non-breaking spaces and blank characters
        text = re.sub(r"[\xa0\u200b\t]", " ", text)
        return text

    def _find_body_match(self, pattern: str, text: str, min_offset: int = 0) -> int:
        """
        Finds the match index for a section header in the body of the document.
        Skips Table of Contents entries by requiring a min_offset or picking the first match past TOC.
        """
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        if not matches:
            return -1

        if len(matches) == 1:
            return matches[0].start()

        # Filter out matches before min_offset (likely Table of Contents or prior section mentions)
        valid_matches = [m for m in matches if m.start() >= min_offset]
        if valid_matches:
            return valid_matches[0].start()

        # If TOC is at index 0, pick second match if available
        if len(matches) > 1 and matches[0].start() < 3000:
            return matches[1].start()

        return matches[0].start()

    def extract_sections(self, html_content: str) -> Dict[str, str]:
        """
        Parses HTML filing text and extracts Item 1A, Item 7, and Item 8.
        Returns a dictionary mapping section keys to extracted section string text.
        """
        logger.info("Parsing HTML content for regulatory sections...")
        text = self._html_to_text(html_content)

        if not text:
            logger.warning("Empty content provided to SECParser")
            return {"item_1a": "", "item_7": "", "item_8": ""}

        # Find start and end indices sequentially to preserve document flow
        initial_offset = 2000 if len(text) > 8000 else 0
        pos_1a_start = self._find_body_match(self.patterns["item_1a_start"], text, min_offset=initial_offset)
        pos_1a_end = self._find_body_match(self.patterns["item_1a_end"], text, min_offset=pos_1a_start + 100 if pos_1a_start != -1 else initial_offset)

        pos_7_offset = pos_1a_end if pos_1a_end != -1 else (pos_1a_start + 100 if pos_1a_start != -1 else (4000 if len(text) > 12000 else 0))
        pos_7_start = self._find_body_match(self.patterns["item_7_start"], text, min_offset=pos_7_offset)
        pos_7_end = self._find_body_match(self.patterns["item_7_end"], text, min_offset=pos_7_start + 100 if pos_7_start != -1 else pos_7_offset)

        pos_8_offset = pos_7_end if pos_7_end != -1 else (pos_7_start + 100 if pos_7_start != -1 else (8000 if len(text) > 16000 else 0))
        pos_8_start = self._find_body_match(self.patterns["item_8_start"], text, min_offset=pos_8_offset)
        pos_8_end = self._find_body_match(self.patterns["item_8_end"], text, min_offset=pos_8_start + 100 if pos_8_start != -1 else pos_8_offset)

        # Extract text sections safely
        item_1a = ""
        if pos_1a_start != -1:
            end = pos_1a_end if (pos_1a_end != -1 and pos_1a_end > pos_1a_start) else len(text)
            item_1a = text[pos_1a_start:end].strip()

        item_7 = ""
        if pos_7_start != -1:
            end = pos_7_end if (pos_7_end != -1 and pos_7_end > pos_7_start) else len(text)
            item_7 = text[pos_7_start:end].strip()

        item_8 = ""
        if pos_8_start != -1:
            end = pos_8_end if (pos_8_end != -1 and pos_8_end > pos_8_start) else len(text)
            item_8 = text[pos_8_start:end].strip()

        sections = {
            "item_1a": item_1a,
            "item_7": item_7,
            "item_8": item_8,
        }

        logger.info(
            f"Extracted sections — Item 1A: {len(item_1a)} chars, Item 7: {len(item_7)} chars, Item 8: {len(item_8)} chars"
        )
        return sections
