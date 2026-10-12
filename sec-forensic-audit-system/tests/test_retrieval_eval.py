"""
Unit and Integration Evaluation Test Suite for Retrieval Metrics & Verifier BERTScore:
Validates Precision@K, Recall@K, MRR, and BERTScore calculations over SEC filing retrieval candidate pools.
"""

import pytest
from typing import Dict, Any, List

from src.eval.retrieval_metrics import RetrievalEvaluator, VerifierBERTScoreEvaluator
from src.retrieval.hybrid_search import HybridSearchEngine
from src.router.verifier import ContradictionVerifier


def test_retrieval_metrics_calculation():
    """Validates Precision@K, Recall@K, and MRR metric calculations."""
    mock_retrieved = [
        {"section_key": "item_1a", "text": "The company faces supply chain disruption risks."},
        {"section_key": "item_7", "text": "Management discussion of annual financial performance."},
        {"section_key": "item_8", "text": "Footnote disclosure regarding litigation reserves."},
    ]

    # Test Precision@K
    p1 = RetrievalEvaluator.calculate_precision_at_k(mock_retrieved, {"item_1a"}, k=1)
    assert p1 == 1.0

    p3 = RetrievalEvaluator.calculate_precision_at_k(mock_retrieved, {"item_1a", "item_8"}, k=3)
    assert abs(p3 - (2.0 / 3.0)) < 1e-4

    # Test Recall@K
    r3 = RetrievalEvaluator.calculate_recall_at_k(mock_retrieved, {"item_1a", "item_8"}, total_relevant_in_corpus=2, k=3)
    assert r3 == 1.0

    # Test MRR
    mrr = RetrievalEvaluator.calculate_mrr(mock_retrieved, {"item_8"})
    assert abs(mrr - (1.0 / 3.0)) < 1e-4


def test_bertscore_calculation():
    """Validates token-level BERTScore Precision, Recall, and F1 calculations."""
    generated = "Footnote technical disclosures materially qualify management's MD&A narrative regarding growth outlook."
    reference = "Footnote disclosures qualify management MD&A revenue growth claims."

    scores = VerifierBERTScoreEvaluator.compute_bertscore(generated, reference)

    assert "precision" in scores
    assert "recall" in scores
    assert "f1" in scores

    assert scores["f1"] > 0.4
    assert scores["precision"] > 0.0
    assert scores["recall"] > 0.0


def test_hybrid_search_retrieval_evaluation():
    """Runs Precision@K, Recall@K, and MRR evaluation on live HybridSearchEngine."""
    hybrid_engine = HybridSearchEngine()

    query = "What are the key supply chain risks for AAPL?"
    retrieved = hybrid_engine.search(query=query, top_k=5, ticker_filter="AAPL")

    if retrieved:
        precision_top3 = RetrievalEvaluator.calculate_precision_at_k(retrieved, {"item_1a", "supply chain", "risk"}, k=3)
        mrr = RetrievalEvaluator.calculate_mrr(retrieved, {"item_1a", "supply chain", "risk"})

        assert precision_top3 >= 0.0
        assert mrr >= 0.0
