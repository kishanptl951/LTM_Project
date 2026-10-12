"""
Hybrid Retrieval Engine: Combines ChromaDB Dense Vector Search + BM25 Lexical Search with Flashrank Re-ranking.
"""
import os
import re
import logging
from typing import List, Dict, Any, Optional, cast
import chromadb
from chromadb.api.types import Metadata
from rank_bm25 import BM25Okapi
from flashrank import Ranker, RerankRequest

logger = logging.getLogger(__name__)


def _simple_tokenize(text: str) -> List[str]:
    """Basic lowercased alphanumeric tokenizer for BM25 indexing."""
    return re.findall(r"\w+", text.lower())


class HybridSearchEngine:
    """
    Combines ChromaDB vector similarity, BM25 keyword matching, and Flashrank re-ranking
    to retrieve high-precision section passages with source citations.
    """

    def __init__(
        self,
        db_path: str = "data/chroma_db",
        collection_name: str = "financial_disclosures"
    ):
        self.db_path = db_path
        self.collection_name = collection_name
        os.makedirs(self.db_path, exist_ok=True)

        self.client = chromadb.PersistentClient(path=self.db_path)
        self.collection = self.client.get_or_create_collection(name=self.collection_name)
        
        # Initialize Flashrank cross-encoder reranker
        self.ranker = Ranker()
        
        # BM25 index & internal chunk catalog
        self.bm25: Optional[BM25Okapi] = None
        self.chunk_catalog: Dict[str, Dict[str, Any]] = {}
        self.indexed_chunk_ids: List[str] = []

        # Auto-reload catalog from ChromaDB if stored chunks exist
        self._reload_catalog_from_chroma()

    def _reload_catalog_from_chroma(self) -> None:
        """Reloads in-memory chunk catalog and BM25 index from persistent ChromaDB collection."""
        try:
            results = self.collection.get(include=["documents", "metadatas"])
            if not results or not results.get("ids"):
                return

            ids = results["ids"]
            documents = results.get("documents") or []
            metadatas = results.get("metadatas") or []

            tokenized_corpus: List[List[str]] = []
            valid_ids: List[str] = []

            for cid, doc, meta in zip(ids, documents, metadatas):
                if not cid or not doc:
                    continue
                valid_ids.append(cid)
                meta_dict = dict(meta) if meta else {}
                self.chunk_catalog[cid] = {
                    "chunk_id": cid,
                    "text": doc,
                    **meta_dict
                }
                tokenized_corpus.append(_simple_tokenize(doc))

            if valid_ids and tokenized_corpus:
                self.bm25 = BM25Okapi(tokenized_corpus)
                self.indexed_chunk_ids = valid_ids
                logger.info(f"Reloaded {len(valid_ids)} chunks from ChromaDB into BM25 index.")
        except Exception as e:
            logger.warning(f"Could not reload catalog from ChromaDB: {e}")

    def index_chunks(self, chunks: List[Dict[str, Any]]) -> int:

        """
        Indexes chunks into ChromaDB vector store and BM25 lexical search index.
        Returns the number of indexed chunks.
        """
        if not chunks:
            logger.warning("No chunks provided to index_chunks")
            return 0

        ids: List[str] = []
        documents: List[str] = []
        metadatas: List[Metadata] = []

        tokenized_corpus: List[List[str]] = []

        for chunk in chunks:
            chunk_id = str(chunk.get("chunk_id"))
            text = str(chunk.get("text", ""))
            
            if not chunk_id or not text.strip():
                continue

            ids.append(chunk_id)
            documents.append(text)

            meta: Metadata = {
                "ticker": str(chunk.get("ticker", "")).upper(),
                "section_key": str(chunk.get("section_key", "")).lower(),
                "item_title": str(chunk.get("item_title", "")),
                "fiscal_year": str(chunk.get("fiscal_year", "")),
                "chunk_index": int(chunk.get("chunk_index", 0)),
                "char_start": int(chunk.get("char_start", 0)),
                "char_end": int(chunk.get("char_end", 0)),
            }
            metadatas.append(meta)

            self.chunk_catalog[chunk_id] = {
                "chunk_id": chunk_id,
                "text": text,
                **meta
            }

            tokenized_corpus.append(_simple_tokenize(text))

        if not ids:
            return 0

        # Upsert into ChromaDB in batches if needed
        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

        # Build BM25 index
        self.bm25 = BM25Okapi(tokenized_corpus)
        self.indexed_chunk_ids = list(ids)

        logger.info(f"Successfully indexed {len(ids)} chunks into ChromaDB persistent collection and BM25 index.")
        return len(ids)

    def search(
        self,
        query: Optional[str] = None,
        top_k: int = 5,
        section_filter: Optional[str] = None,
        ticker_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Performs hybrid retrieval:
        1. Dense vector query via ChromaDB (Top-15 candidates)
        2. Lexical keyword query via BM25 (Top-15 candidates)
        3. Candidate deduplication & candidate pool assembly
        4. Cross-encoder re-ranking via Flashrank
        Returns top_k re-ranked passage results.
        """
        if not query or not query.strip():
            return []

        if not self.chunk_catalog:
            logger.warning("Search invoked on empty HybridSearchEngine catalog")
            return []

        candidate_ids: set = set()

        # Build ChromaDB metadata filter with exchange suffix resilience (RELIANCE vs RELIANCE.NS)
        chroma_filter: Dict[str, Any] = {}
        tf_base = ticker_filter.upper().replace(".NS", "").replace(".BO", "") if ticker_filter else None
        
        if ticker_filter:
            valid_tickers = list({ticker_filter.upper(), tf_base, f"{tf_base}.NS", f"{tf_base}.BO"})
            ticker_clause = {"ticker": {"$in": valid_tickers}} if len(valid_tickers) > 1 else {"ticker": ticker_filter.upper()}
            if section_filter:
                chroma_filter = {"$and": [{"section_key": section_filter.lower()}, ticker_clause]}
            else:
                chroma_filter = ticker_clause
        elif section_filter:
            chroma_filter = {"section_key": section_filter.lower()}

        # 1. Dense Vector Retrieval (ChromaDB)
        try:
            query_kwargs: Dict[str, Any] = {"query_texts": [query], "n_results": min(15, len(self.chunk_catalog))}
            if chroma_filter:
                query_kwargs["where"] = chroma_filter

            vector_results = self.collection.query(**query_kwargs)
            if vector_results and "ids" in vector_results and vector_results["ids"]:
                for cid in vector_results["ids"][0]:
                    candidate_ids.add(cid)
        except Exception as e:
            logger.error(f"ChromaDB vector query failed: {e}")

        # 2. Lexical BM25 Retrieval
        if self.bm25 and self.indexed_chunk_ids:
            query_tokens = _simple_tokenize(query)
            bm25_scores = self.bm25.get_scores(query_tokens)
            
            # Sort top BM25 matches
            top_bm25_indices = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:15]
            for idx in top_bm25_indices:
                if bm25_scores[idx] > 0:
                    cid = self.indexed_chunk_ids[idx]
                    chunk_meta = self.chunk_catalog.get(cid, {})

                    # Apply filter manually if specified
                    if section_filter and chunk_meta.get("section_key") != section_filter.lower():
                        continue
                    if ticker_filter:
                        chunk_t = str(chunk_meta.get("ticker", "")).upper()
                        chunk_base = chunk_t.replace(".NS", "").replace(".BO", "")
                        if chunk_t != ticker_filter.upper() and chunk_base != tf_base:
                            continue
                        
                    candidate_ids.add(cid)

        if not candidate_ids:
            logger.info("No candidates matched vector or BM25 search criteria")
            return []

        # 3. Flashrank Re-ranking Stage
        passages: List[Dict[str, Any]] = []
        for cid in candidate_ids:
            chunk = self.chunk_catalog.get(cid)
            if chunk:
                passages.append({
                    "id": cid,
                    "text": chunk["text"],
                    "meta": chunk
                })

        try:
            rerank_request = RerankRequest(query=query, passages=passages)
            rerank_results = self.ranker.rerank(rerank_request)
        except Exception as e:
            logger.error(f"Flashrank reranking failed: {e}. Falling back to un-ranked candidates.")
            rerank_results = passages[:top_k]

        # 4. Format top_k passage results
        final_results: List[Dict[str, Any]] = []
        for res in rerank_results[:top_k]:
            cid = str(res.get("id"))
            chunk = self.chunk_catalog.get(cid, {})
            score = float(res.get("score", 0.0))

            final_results.append({
                "chunk_id": cid,
                "score": score,
                "text": chunk.get("text", res.get("text", "")),
                "ticker": chunk.get("ticker"),
                "section_key": chunk.get("section_key"),
                "item_title": chunk.get("item_title"),
                "fiscal_year": chunk.get("fiscal_year"),
                "char_start": chunk.get("char_start"),
                "char_end": chunk.get("char_end"),
                "citation": f"{chunk.get('ticker')} {chunk.get('fiscal_year')} [{chunk.get('item_title')}]"
            })

        logger.info(f"Hybrid retrieval complete for query '{query}': returned {len(final_results)} re-ranked passages.")
        return final_results
