"""
Indian Report Parser: Parses Indian annual report HTML/text documents and extracts key sections:
- Management Discussion & Analysis (MD&A)
- Board's Report / Directors' Report
- Notes to Financial Statements (Notes to Accounts)
- Independent Auditor's Report

These are the Indian equivalents of SEC 10-K sections (Item 1A, Item 7, Item 8).
"""
import re
import logging
import warnings
from typing import Dict
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

logger = logging.getLogger(__name__)

# Suppress XML parsed as HTML warning
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


class IndianReportParser:
    """
    Parses Indian annual report HTML/text documents and extracts key regulatory sections
    mandated by SEBI LODR and Companies Act 2013:
    - MD&A: Management Discussion and Analysis
    - Board Report: Board's Report / Directors' Report
    - Notes: Notes to Financial Statements / Notes to Accounts
    - Auditor Report: Independent Auditor's Report
    """

    def __init__(self):
        # Section regex match patterns for Indian annual reports
        self.patterns = {
            # MD&A Section
            "mda_start": r"(?:MANAGEMENT\s+DISCUSSION\s+AND\s+ANALYSIS|MANAGEMENT[\s'\u2019]*S?\s+DISCUSSION|MD\s*&\s*A\s+REPORT)",
            "mda_end": r"(?:BOARD[\s'\u2019]*S?\s+REPORT|DIRECTORS[\s'\u2019]*?\s+REPORT|CORPORATE\s+GOVERNANCE|REPORT\s+ON\s+CORPORATE\s+GOVERNANCE)",

            # Board's Report / Directors' Report
            "board_report_start": r"(?:BOARD[\s'\u2019]*S?\s+REPORT|DIRECTORS[\s'\u2019]*?\s+REPORT|REPORT\s+OF\s+THE\s+BOARD\s+OF\s+DIRECTORS)",
            "board_report_end": r"(?:CORPORATE\s+GOVERNANCE|INDEPENDENT\s+AUDITOR|AUDITOR[\s'\u2019]*S?\s+REPORT|FINANCIAL\s+STATEMENTS|STANDALONE\s+FINANCIAL)",

            # Independent Auditor's Report
            "auditor_report_start": r"(?:INDEPENDENT\s+AUDITOR[\s'\u2019]*S?\s+REPORT|AUDITOR[\s'\u2019]*S?\s+REPORT|REPORT\s+OF\s+THE\s+INDEPENDENT\s+AUDITOR)",
            "auditor_report_end": r"(?:BALANCE\s+SHEET|STATEMENT\s+OF\s+PROFIT\s+AND\s+LOSS|STANDALONE\s+BALANCE|CONSOLIDATED\s+BALANCE|NOTES\s+TO\s+(?:THE\s+)?FINANCIAL)",

            # Notes to Financial Statements
            "notes_start": r"(?:NOTES\s+TO\s+(?:THE\s+)?(?:STANDALONE\s+)?FINANCIAL\s+STATEMENTS|NOTES\s+TO\s+ACCOUNTS|NOTES\s+FORMING\s+PART\s+OF)",
            "notes_end": r"(?:INDEPENDENT\s+AUDITOR[\s'\u2019]*S?\s+REPORT\s+ON\s+(?:THE\s+)?CONSOLIDATED|CONSOLIDATED\s+FINANCIAL|STATEMENT\s+OF\s+CHANGES\s+IN\s+EQUITY|CASH\s+FLOW\s+STATEMENT\s+FOR)",
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
        Skips Table of Contents entries by requiring a min_offset.
        """
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        if not matches:
            return -1

        if len(matches) == 1:
            return matches[0].start()

        # Filter out matches before min_offset (likely Table of Contents)
        valid_matches = [m for m in matches if m.start() >= min_offset]
        if valid_matches:
            return valid_matches[0].start()

        # If TOC is at index 0, pick second match if available
        if len(matches) > 1 and matches[0].start() < 3000:
            return matches[1].start()

        return matches[0].start()

    def extract_sections(self, html_content: str) -> Dict[str, str]:
        """
        Parses Indian annual report text and extracts MD&A, Board's Report,
        Auditor's Report, and Notes to Accounts sections.
        Returns a dictionary mapping section keys to extracted section string text.
        """
        logger.info("Parsing Indian annual report for regulatory sections...")
        text = self._html_to_text(html_content)

        if not text:
            logger.warning("Empty content provided to IndianReportParser")
            return {"mda": "", "board_report": "", "auditor_report": "", "notes": ""}

        initial_offset = 2000 if len(text) > 8000 else 0

        # Find MD&A
        pos_mda_start = self._find_body_match(self.patterns["mda_start"], text, min_offset=initial_offset)
        pos_mda_end = self._find_body_match(
            self.patterns["mda_end"], text,
            min_offset=pos_mda_start + 100 if pos_mda_start != -1 else initial_offset
        )

        # Find Board Report
        br_offset = pos_mda_end if pos_mda_end != -1 else (pos_mda_start + 100 if pos_mda_start != -1 else initial_offset)
        pos_br_start = self._find_body_match(self.patterns["board_report_start"], text, min_offset=br_offset)
        pos_br_end = self._find_body_match(
            self.patterns["board_report_end"], text,
            min_offset=pos_br_start + 100 if pos_br_start != -1 else br_offset
        )

        # Find Auditor Report
        ar_offset = pos_br_end if pos_br_end != -1 else (pos_br_start + 100 if pos_br_start != -1 else initial_offset)
        pos_ar_start = self._find_body_match(self.patterns["auditor_report_start"], text, min_offset=ar_offset)
        pos_ar_end = self._find_body_match(
            self.patterns["auditor_report_end"], text,
            min_offset=pos_ar_start + 100 if pos_ar_start != -1 else ar_offset
        )

        # Find Notes to Financial Statements
        notes_offset = pos_ar_end if pos_ar_end != -1 else (pos_ar_start + 100 if pos_ar_start != -1 else initial_offset)
        pos_notes_start = self._find_body_match(self.patterns["notes_start"], text, min_offset=notes_offset)
        pos_notes_end = self._find_body_match(
            self.patterns["notes_end"], text,
            min_offset=pos_notes_start + 100 if pos_notes_start != -1 else notes_offset
        )

        # Extract text sections safely
        def _extract(start: int, end: int) -> str:
            if start == -1:
                return ""
            actual_end = end if (end != -1 and end > start) else len(text)
            return text[start:actual_end].strip()

        mda = _extract(pos_mda_start, pos_mda_end)
        board_report = _extract(pos_br_start, pos_br_end)
        auditor_report = _extract(pos_ar_start, pos_ar_end)
        notes = _extract(pos_notes_start, pos_notes_end)

        sections = {
            "mda": mda,
            "board_report": board_report,
            "auditor_report": auditor_report,
            "notes": notes,
        }

        logger.info(
            f"Extracted sections — MD&A: {len(mda)} chars, Board Report: {len(board_report)} chars, "
            f"Auditor Report: {len(auditor_report)} chars, Notes: {len(notes)} chars"
        )
        return sections
