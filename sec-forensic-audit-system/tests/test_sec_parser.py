"""
Unit tests for SEC Parser module.
"""
import pytest
from pathlib import Path
from src.ingestion.sec_parser import SECParser

SAMPLE_HTML = """
<html>
<body>
<div>
    <h1>TABLE OF CONTENTS</h1>
    <p>ITEM 1A. RISK FACTORS ........................... 5</p>
    <p>ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS .... 15</p>
    <p>ITEM 8. FINANCIAL STATEMENTS ..................... 30</p>
</div>
<div>
    <h2>ITEM 1A. RISK FACTORS</h2>
    <p>Our business faces cyber security and supply chain risks.</p>

    <h2>ITEM 1B. UNRESOLVED STAFF COMMENTS</h2>
    <p>None.</p>

    <h2>ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION</h2>
    <p>Revenue increased by 12% year over year driven by services.</p>

    <h2>ITEM 7A. QUANTITATIVE AND QUALITATIVE DISCLOSURES ABOUT MARKET RISK</h2>
    <p>We are exposed to interest rate risk.</p>

    <h2>ITEM 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA</h2>
    <p>Consolidated Statements of Operations and Footnote 1 Accounting Policies.</p>

    <h2>ITEM 9. CHANGES IN AND DISAGREEMENTS WITH ACCOUNTANTS</h2>
    <p>None.</p>
</div>
</body>
</html>
"""


def test_sec_parser_extraction_synthetic():
    parser = SECParser()
    sections = parser.extract_sections(SAMPLE_HTML)

    assert "item_1a" in sections
    assert "item_7" in sections
    assert "item_8" in sections

    assert "cyber security and supply chain risks" in sections["item_1a"]
    assert "Revenue increased by 12%" in sections["item_7"]
    assert "Consolidated Statements of Operations" in sections["item_8"]


def test_sec_parser_empty_input():
    parser = SECParser()
    sections = parser.extract_sections("")

    assert sections["item_1a"] == ""
    assert sections["item_7"] == ""
    assert sections["item_8"] == ""


def test_sec_parser_real_filing_if_cached():
    cached_filing = Path("data/sec_corpus/AAPL/filings/10-K_2024.html")
    if cached_filing.exists():
        with open(cached_filing, "r", encoding="utf-8") as f:
            html = f.read()

        parser = SECParser()
        sections = parser.extract_sections(html)

        assert len(sections["item_1a"]) > 1000
        assert len(sections["item_7"]) > 1000
        assert len(sections["item_8"]) > 1000
