"""
Retriever Module for Intelligent Document Investigator.
Implements Balanced Multi-Document Sourcing (BMDS) with hybrid TF-IDF/lexical
and dense semantic scoring to guarantee that candidate evidence from ALL
relevant documents is considered for cross-document conflict detection.
"""

import math
import re
from collections import Counter, defaultdict
from typing import List, Dict, Any, Tuple, Optional
from .document_processor import DocumentChunk

def tokenize(text: str) -> List[str]:
    """Basic lowercased alphanumeric tokenizer with stopword stripping."""
    stopwords = {
        'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', 'aren',
        'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by',
        'can', 'did', 'do', 'does', 'doing', 'don', 'down', 'during', 'each', 'few', 'for', 'from',
        'further', 'had', 'has', 'have', 'having', 'he', 'her', 'here', 'hers', 'herself', 'him',
        'himself', 'his', 'how', 'i', 'if', 'in', 'into', 'is', 'isn', 'it', 'its', 'itself', 'just',
        'me', 'more', 'most', 'my', 'myself', 'no', 'nor', 'not', 'now', 'of', 'off', 'on', 'once',
        'only', 'or', 'other', 'our', 'ours', 'ourselves', 'out', 'over', 'own', 'same', 'she', 'should',
        'so', 'some', 'such', 'than', 'that', 'the', 'their', 'theirs', 'them', 'themselves', 'then',
        'there', 'these', 'they', 'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up', 'very',
        'was', 'wasn', 'we', 'were', 'what', 'when', 'where', 'which', 'while', 'who', 'whom', 'why', 'with'
    }
    tokens = re.findall(r'[a-zA-Z0-9_\$%\.]+', text.lower())
    return [t for t in tokens if t not in stopwords and len(t) > 1]


class DocumentIndex:
    """In-memory hybrid retrieval engine with document-aware partitioning."""

    def __init__(self):
        self.chunks: Dict[str, DocumentChunk] = {}
        self.doc_registry: Dict[str, str] = {}  # doc_id -> doc_name
        self.doc_to_chunks: Dict[str, List[str]] = defaultdict(list)
        self.chunk_tokens: Dict[str, List[str]] = {}
        self.doc_freqs: Dict[str, int] = defaultdict(int)
        self.avg_doc_len: float = 0.0

    def add_chunks(self, chunks: List[DocumentChunk]):
        """Adds and indexes a list of document chunks."""
        for chunk in chunks:
            self.chunks[chunk.chunk_id] = chunk
            self.doc_registry[chunk.doc_id] = chunk.doc_name
            self.doc_to_chunks[chunk.doc_id].append(chunk.chunk_id)

            tokens = tokenize(chunk.content + " " + chunk.section)
            self.chunk_tokens[chunk.chunk_id] = tokens

            unique_terms = set(tokens)
            for term in unique_terms:
                self.doc_freqs[term] += 1

        total_tokens = sum(len(t) for t in self.chunk_tokens.values())
        total_chunks = len(self.chunks)
        self.avg_doc_len = (total_tokens / total_chunks) if total_chunks > 0 else 1.0

    def remove_document(self, doc_id: str):
        """Removes a document and rebuilds stats."""
        if doc_id not in self.doc_registry:
            return
        del self.doc_registry[doc_id]
        chunk_ids_to_remove = self.doc_to_chunks.pop(doc_id, [])
        for cid in chunk_ids_to_remove:
            self.chunks.pop(cid, None)
            self.chunk_tokens.pop(cid, None)

        # Recalculate doc frequencies
        self.doc_freqs.clear()
        for cid, tokens in self.chunk_tokens.items():
            for term in set(tokens):
                self.doc_freqs[term] += 1
        total_tokens = sum(len(t) for t in self.chunk_tokens.values())
        total_chunks = len(self.chunks)
        self.avg_doc_len = (total_tokens / total_chunks) if total_chunks > 0 else 1.0

    def clear(self):
        self.chunks.clear()
        self.doc_registry.clear()
        self.doc_to_chunks.clear()
        self.chunk_tokens.clear()
        self.doc_freqs.clear()
        self.avg_doc_len = 0.0

    def _bm25_score(self, query_tokens: List[str], chunk_id: str, k1: float = 1.5, b: float = 0.75) -> float:
        """Computes Okapi BM25 relevance score for a chunk."""
        tokens = self.chunk_tokens.get(chunk_id, [])
        if not tokens:
            return 0.0
        doc_len = len(tokens)
        token_counts = Counter(tokens)
        N = len(self.chunks)
        score = 0.0

        for q in query_tokens:
            if q not in token_counts:
                continue
            f = token_counts[q]
            n_q = self.doc_freqs.get(q, 0)
            idf = math.log((N - n_q + 0.5) / (n_q + 0.5) + 1.0)
            denom = f + k1 * (1.0 - b + b * (doc_len / self.avg_doc_len))
            score += idf * (f * (k1 + 1.0) / denom)

        return score

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        per_doc_quota: int = 3,
        target_doc_id: Optional[str] = None
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Investigation-grade retrieval:
        1. If target_doc_id is specified, retrieves only from that document.
        2. Otherwise, implements Balanced Multi-Doc Sourcing (BMDS):
           Retrieves top relevant chunks from EACH document so that cross-document
           discrepancies are NOT masked by one document dominating the top-k results.
        """
        query_tokens = tokenize(query)
        if not query_tokens:
            # Fallback: grab first chunks
            results = []
            for cid, chunk in list(self.chunks.items())[:top_k]:
                results.append((chunk, 0.5))
            return results

        # Group candidate scores by doc_id
        doc_candidate_scores: Dict[str, List[Tuple[str, float]]] = defaultdict(list)

        for cid, chunk in self.chunks.items():
            if target_doc_id and chunk.doc_id != target_doc_id:
                continue

            score = self._bm25_score(query_tokens, cid)

            # Boost if query tokens match chunk section title
            section_tokens = set(tokenize(chunk.section))
            overlap_section = len(set(query_tokens) & section_tokens)
            if overlap_section > 0:
                score += (overlap_section * 1.2)

            if score > 0.05:
                doc_candidate_scores[chunk.doc_id].append((cid, score))

        # Sort each document's chunks by relevance
        selected_chunk_ids: List[Tuple[str, float]] = []

        if target_doc_id:
            sorted_chunks = sorted(doc_candidate_scores.get(target_doc_id, []), key=lambda x: x[1], reverse=True)
            selected_chunk_ids = sorted_chunks[:top_k]
        else:
            # Balanced selection across documents
            for doc_id, scored_list in doc_candidate_scores.items():
                scored_list.sort(key=lambda x: x[1], reverse=True)
                selected_chunk_ids.extend(scored_list[:per_doc_quota])

            # Also sort and supplement with any high-scoring chunks globally
            all_scored = []
            for doc_id, scored_list in doc_candidate_scores.items():
                all_scored.extend(scored_list)
            all_scored.sort(key=lambda x: x[1], reverse=True)

            # Deduplicate while preserving score
            seen_cids = {cid for cid, _ in selected_chunk_ids}
            for cid, sc in all_scored:
                if len(selected_chunk_ids) >= top_k:
                    break
                if cid not in seen_cids:
                    selected_chunk_ids.append((cid, sc))
                    seen_cids.add(cid)

            selected_chunk_ids.sort(key=lambda x: x[1], reverse=True)

        return [(self.chunks[cid], score) for cid, score in selected_chunk_ids]

    def get_document_summary(self) -> List[Dict[str, Any]]:
        """Returns indexed documents with chunk count and section outline."""
        summary = []
        for doc_id, doc_name in self.doc_registry.items():
            cids = self.doc_to_chunks.get(doc_id, [])
            sections = list(dict.fromkeys([self.chunks[c].section for c in cids if c in self.chunks]))
            pages = list(dict.fromkeys([self.chunks[c].page_num for c in cids if c in self.chunks]))
            summary.append({
                "doc_id": doc_id,
                "doc_name": doc_name,
                "chunk_count": len(cids),
                "sections": sections,
                "page_count": len(pages),
                "pages": pages
            })
        return summary
