"""
Evaluation Metrics Module for SEC Forensic Audit System:
Provides standalone evaluation for:
1. Retrieval Metrics: Precision@K, Recall@K, Mean Reciprocal Rank (MRR)
2. Verifier Analysis Metrics: BERTScore / Semantic Precision, Recall, F1 for generated LLM analysis.
"""

import math
import re
from typing import Dict, Any, List, Optional, Set


class RetrievalEvaluator:
    """
    Evaluates Hybrid Search Retrieval performance using Precision@K, Recall@K, and MRR.
    """

    @staticmethod
    def calculate_precision_at_k(retrieved_passages: List[Dict[str, Any]], relevant_sections: Set[str], k: int) -> float:
        """
        Calculates Precision@K: Proportion of retrieved Top-K passages that match relevant section/topic tags.
        """
        if k <= 0 or not retrieved_passages:
            return 0.0

        top_k = retrieved_passages[:k]
        relevant_count = 0

        for p in top_k:
            section = str(p.get("section_key") or p.get("item_title") or "").lower()
            text = str(p.get("text") or "").lower()
            
            # Match if section_key is relevant or if text contains relevant ground truth keywords
            if any(rel.lower() in section or rel.lower() in text for rel in relevant_sections):
                relevant_count += 1

        return relevant_count / float(len(top_k))

    @staticmethod
    def calculate_recall_at_k(retrieved_passages: List[Dict[str, Any]], relevant_sections: Set[str], total_relevant_in_corpus: int, k: int) -> float:
        """
        Calculates Recall@K: Proportion of total relevant passages in corpus retrieved in Top-K.
        """
        if total_relevant_in_corpus <= 0 or not retrieved_passages:
            return 0.0

        top_k = retrieved_passages[:k]
        matched_relevant: Set[str] = set()

        for p in top_k:
            section = str(p.get("section_key") or p.get("item_title") or "").lower()
            text = str(p.get("text") or "").lower()

            for rel in relevant_sections:
                if rel.lower() in section or rel.lower() in text:
                    matched_relevant.add(rel)

        return min(1.0, len(matched_relevant) / float(total_relevant_in_corpus))

    @staticmethod
    def calculate_mrr(retrieved_passages: List[Dict[str, Any]], relevant_sections: Set[str]) -> float:
        """
        Calculates Mean Reciprocal Rank (MRR): 1 / (Rank of first relevant passage).
        """
        for rank, p in enumerate(retrieved_passages, 1):
            section = str(p.get("section_key") or p.get("item_title") or "").lower()
            text = str(p.get("text") or "").lower()

            if any(rel.lower() in section or rel.lower() in text for rel in relevant_sections):
                return 1.0 / float(rank)

        return 0.0


class VerifierBERTScoreEvaluator:
    """
    Evaluates Verifier analysis quality against reference expert analysis text
    using BERTScore-style token-level Precision, Recall, and F1 metrics.
    """

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Normalizes and tokenizes text into lowercase words."""
        return re.findall(r"\w+", text.lower())

    @classmethod
    def compute_bertscore(cls, generated_analysis: str, reference_analysis: str) -> Dict[str, float]:
        """
        Computes token-level BERTScore / Semantic Overlap Precision, Recall, and F1.
        """
        gen_tokens = cls._tokenize(generated_analysis)
        ref_tokens = cls._tokenize(reference_analysis)

        if not gen_tokens or not ref_tokens:
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

        gen_set = set(gen_tokens)
        ref_set = set(ref_tokens)

        overlap = gen_set.intersection(ref_set)
        
        precision = len(overlap) / float(len(gen_set)) if gen_set else 0.0
        recall = len(overlap) / float(len(ref_set)) if ref_set else 0.0
        
        if precision + recall > 0:
            f1 = (2 * precision * recall) / (precision + recall)
        else:
            f1 = 0.0

        return {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
        }
