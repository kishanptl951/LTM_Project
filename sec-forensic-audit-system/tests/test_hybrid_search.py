"""
Unit tests for SectionChunker and HybridSearchEngine modules.
"""
import pytest
from pathlib import Path
from src.retrieval.chunker import SectionChunker
from src.retrieval.hybrid_search import HybridSearchEngine


def test_section_chunker_basic():
    chunker = SectionChunker(chunk_size=1200, overlap=200)
    sample_text = "Word " * 500  # ~2500 characters
    meta = {
        "ticker": "TEST",
        "section_key": "item_7",
        "item_title": "Item 7: MD&A",
        "fiscal_year": 2024
    }

    chunks = chunker.chunk_section(sample_text, meta)
    assert len(chunks) > 1
    assert chunks[0]["ticker"] == "TEST"
    assert chunks[0]["section_key"] == "item_7"
    assert chunks[0]["fiscal_year"] == 2024
    assert len(chunks[0]["text"]) <= 1200


def test_section_chunker_short_text():
    chunker = SectionChunker(chunk_size=1200, overlap=200)
    short_text = "Short section summary."
    meta = {"ticker": "TEST", "section_key": "item_1a"}

    chunks = chunker.chunk_section(short_text, meta)
    assert len(chunks) == 1
    assert chunks[0]["text"] == short_text
    assert chunks[0]["chunk_index"] == 0


@pytest.fixture
def temp_hybrid_engine(tmp_path):
    chroma_dir = tmp_path / "chroma_test_db"
    engine = HybridSearchEngine(db_path=str(chroma_dir), collection_name="test_sec_disclosures")
    yield engine


def test_hybrid_search_indexing_and_query(temp_hybrid_engine):
    sample_chunks = [
        {
            "chunk_id": "TEST_item_7_2024_chunk_0",
            "text": "The Company experienced strong revenue growth in services, offsetting hardware supply chain constraints.",
            "ticker": "TEST",
            "section_key": "item_7",
            "item_title": "Item 7: MD&A",
            "fiscal_year": 2024,
            "chunk_index": 0,
            "char_start": 0,
            "char_end": 100
        },
        {
            "chunk_id": "TEST_item_1a_2024_chunk_0",
            "text": "Cybersecurity risks, regulatory compliance, and geopolitical supply chain disruptions could impact operations.",
            "ticker": "TEST",
            "section_key": "item_1a",
            "item_title": "Item 1A: Risk Factors",
            "fiscal_year": 2024,
            "chunk_index": 0,
            "char_start": 0,
            "char_end": 100
        },
        {
            "chunk_id": "TEST_item_8_2024_chunk_0",
            "text": "Footnote 1: Summary of Significant Accounting Policies. Revenue is recognized when control of goods is transferred.",
            "ticker": "TEST",
            "section_key": "item_8",
            "item_title": "Item 8: Footnotes",
            "fiscal_year": 2024,
            "chunk_index": 0,
            "char_start": 0,
            "char_end": 100
        }
    ]

    indexed_count = temp_hybrid_engine.index_chunks(sample_chunks)
    assert indexed_count == 3

    # Query for supply chain risks
    results = temp_hybrid_engine.search("supply chain disruptions", top_k=2)
    assert len(results) > 0
    assert "score" in results[0]
    assert "citation" in results[0]

    # Query specifically with section filter
    item_8_results = temp_hybrid_engine.search("revenue accounting policy", top_k=2, section_filter="item_8")
    assert len(item_8_results) > 0
    assert item_8_results[0]["section_key"] == "item_8"
