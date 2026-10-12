"""
Section-aware Chunker: Splits Item 1A (Risk Factors), Item 7 (MD&A), and Item 8 (Footnotes)
into context-preserving text passages while embedding rich metadata.
"""
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class SectionChunker:
    """
    Splits section text into sliding window passages (default ~1200 characters / 200-300 words with 200 overlap)
    and attaches metadata for section-aware retrieval and citation generation.
    """

    def __init__(self, chunk_size: int = 1200, overlap: int = 200):
        if overlap >= chunk_size:
            raise ValueError("Overlap must be strictly smaller than chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_section(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Chunks a given section text string and embeds section metadata into each passage.
        """
        if not text or not text.strip():
            return []

        text = text.strip()
        ticker = str(metadata.get("ticker", "UNKNOWN")).upper()
        section_key = str(metadata.get("section_key", "general")).lower()
        item_title = str(metadata.get("item_title", section_key.upper()))
        fiscal_year = metadata.get("fiscal_year", "N/A")

        chunks: List[Dict[str, Any]] = []
        step = self.chunk_size - self.overlap
        start = 0
        chunk_idx = 0

        while start < len(text):
            end = min(start + self.chunk_size, len(text))

            # Snap end to nearest sentence boundary if not at end of text
            if end < len(text):
                boundary = max(
                    text.rfind(". ", start + self.chunk_size // 2, end),
                    text.rfind("?\n", start + self.chunk_size // 2, end),
                    text.rfind("!\n", start + self.chunk_size // 2, end),
                    text.rfind("\n\n", start + self.chunk_size // 2, end),
                )
                if boundary != -1:
                    end = boundary + 1

            chunk_text = text[start:end].strip()

            if chunk_text:
                chunk_id = f"{ticker}_{section_key}_{fiscal_year}_chunk_{chunk_idx}"
                chunk_record = {
                    "chunk_id": chunk_id,
                    "text": chunk_text,
                    "ticker": ticker,
                    "section_key": section_key,
                    "item_title": item_title,
                    "fiscal_year": fiscal_year,
                    "chunk_index": chunk_idx,
                    "char_start": start,
                    "char_end": end,
                }
                chunks.append(chunk_record)
                chunk_idx += 1

            if end >= len(text):
                break
            start += step

        logger.info(
            f"Chunked section '{section_key}' for {ticker} ({len(text)} chars) into {len(chunks)} passages "
            f"(chunk_size={self.chunk_size}, overlap={self.overlap})"
        )
        return chunks

    def chunk_all_sections(
        self,
        sections: Dict[str, str],
        ticker: str,
        fiscal_year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Chunks all extracted sections (item_1a, item_7, item_8) for a company filing.
        """
        section_titles = {
            # US SEC 10-K Sections
            "item_1a": "Item 1A: Risk Factors",
            "item_7": "Item 7: MD&A",
            "item_8": "Item 8: Financial Statements & Footnotes",
            # Indian Annual Report Sections
            "mda": "Management Discussion & Analysis",
            "board_report": "Board's Report / Directors' Report",
            "notes": "Notes to Financial Statements",
            "auditor_report": "Independent Auditor's Report",
        }

        all_chunks: List[Dict[str, Any]] = []
        for sec_key, sec_text in sections.items():
            if not sec_text:
                continue

            meta = {
                "ticker": ticker,
                "section_key": sec_key,
                "item_title": section_titles.get(sec_key, sec_key.upper()),
                "fiscal_year": fiscal_year or "N/A",
            }
            sec_chunks = self.chunk_section(sec_text, meta)
            all_chunks.extend(sec_chunks)

        logger.info(f"Total chunks created across all sections for {ticker}: {len(all_chunks)}")
        return all_chunks
