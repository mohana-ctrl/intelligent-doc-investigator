"""
Investigation Engine Orchestrator.
Glues document processing, balanced multi-doc indexing, conflict detection,
pairwise comparison matrices, and uncertainty-aware synthesis.
"""

from typing import List, Dict, Any, Optional
from .document_processor import DocumentProcessor, DocumentChunk
from .retriever import DocumentIndex
from .conflict_detector import ConflictDetector, ConflictReport
from .gemini_client import GeminiInvestigatorClient
from .sample_data import SAMPLE_DOSSIERS

class InvestigationEngine:
    """End-to-end investigation workspace manager."""

    def __init__(self, api_key: Optional[str] = None):
        self.processor = DocumentProcessor(chunk_size=400, chunk_overlap=60)
        self.index = DocumentIndex()
        self.conflict_detector = ConflictDetector()
        self.gemini_client = GeminiInvestigatorClient(api_key=api_key)
        self.active_dossier_name: str = "custom"

    def ingest_text(self, text: str, doc_id: str, doc_name: str) -> Dict[str, Any]:
        """Ingests raw text or markdown into the index."""
        chunks = self.processor.process_raw_text(text, doc_id, doc_name)
        self.index.add_chunks(chunks)
        return {
            "status": "success",
            "doc_id": doc_id,
            "doc_name": doc_name,
            "chunks_created": len(chunks)
        }

    def ingest_file(self, file_path: str, doc_id: str, doc_name: Optional[str] = None) -> Dict[str, Any]:
        """Ingests a file from disk into the index."""
        chunks = self.processor.process_file(file_path, doc_id, doc_name)
        self.index.add_chunks(chunks)
        return {
            "status": "success",
            "doc_id": doc_id,
            "doc_name": doc_name or file_path,
            "chunks_created": len(chunks)
        }

    def load_sample_dossier(self, dossier_key: str) -> Dict[str, Any]:
        """Loads a curated benchmark dossier with known contradictions."""
        if dossier_key not in SAMPLE_DOSSIERS:
            raise ValueError(f"Dossier '{dossier_key}' not found. Available: {list(SAMPLE_DOSSIERS.keys())}")

        dossier = SAMPLE_DOSSIERS[dossier_key]
        self.index.clear()
        self.active_dossier_name = dossier_key

        loaded_docs = []
        for doc in dossier["documents"]:
            res = self.ingest_text(doc["content"], doc["id"], doc["name"])
            loaded_docs.append(res)

        return {
            "dossier_key": dossier_key,
            "title": dossier["title"],
            "description": dossier["description"],
            "suggested_queries": dossier.get("suggested_queries", []),
            "loaded_documents": loaded_docs,
            "total_documents": len(loaded_docs)
        }

    def query_investigation(
        self,
        query: str,
        top_k: int = 8,
        per_doc_quota: int = 3,
        target_doc_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes a full cross-document investigation pass:
        1. Balanced Multi-Doc Sourcing retrieval
        2. Factual claim extraction & pairwise conflict detection
        3. Certainty scoring & uncertainty communication
        4. Evidence-backed synthesis with exact citations
        """
        # 1. Retrieve balanced evidence
        retrieved = self.index.retrieve(
            query=query,
            top_k=top_k,
            per_doc_quota=per_doc_quota,
            target_doc_id=target_doc_id
        )
        chunks = [c for c, _ in retrieved]

        # 2. Analyze cross-document conflicts
        conflict_reports = self.conflict_detector.analyze_cross_document_conflicts(chunks, query=query)

        # 3. Synthesize answer with grounding
        synthesis = self.gemini_client.generate_investigation_response(
            query=query,
            retrieved_chunks=chunks,
            conflict_reports=conflict_reports
        )

        return {
            "query": query,
            "certainty": synthesis.get("certainty", "UNKNOWN"),
            "llm_status": synthesis.get("llm_status", ""),
            "answer": synthesis.get("answer", ""),
            "citations": synthesis.get("citations", []),
            "conflicts": [cr.to_dict() for cr in conflict_reports],
            "evidence_count": len(chunks),
            "documents_consulted": list({c.doc_name for c in chunks})
        }

    def get_cross_document_conflict_matrix(self) -> Dict[str, Any]:
        """
        Generates a comprehensive pairwise conflict matrix across ALL indexed documents.
        Visualizes which documents agree and which documents clash.
        """
        all_chunks = list(self.index.chunks.values())
        all_conflicts = self.conflict_detector.analyze_cross_document_conflicts(all_chunks)

        docs = self.index.get_document_summary()
        doc_names = [d["doc_name"] for d in docs]

        # Initialize matrix
        matrix: Dict[str, Dict[str, int]] = {d1: {d2: 0 for d2 in doc_names} for d1 in doc_names}
        conflict_details: List[Dict[str, Any]] = []

        for cr in all_conflicts:
            if cr.severity == "HIGH":
                claims = cr.claims
                involved_docs = list({c.doc_name for c in claims})
                # Add edges between conflicting pairs
                for i in range(len(involved_docs)):
                    for j in range(i + 1, len(involved_docs)):
                        d1 = involved_docs[i]
                        d2 = involved_docs[j]
                        if d1 in matrix and d2 in matrix[d1]:
                            matrix[d1][d2] += 1
                            matrix[d2][d1] += 1

                conflict_details.append({
                    "topic": cr.topic,
                    "type": cr.conflict_type,
                    "involved_documents": involved_docs,
                    "description": cr.description,
                    "advice": cr.investigator_advice
                })

        return {
            "document_names": doc_names,
            "matrix": matrix,
            "conflict_count": len(conflict_details),
            "conflicts": conflict_details
        }

    def list_documents(self) -> List[Dict[str, Any]]:
        return self.index.get_document_summary()

    def clear(self):
        self.index.clear()
        self.active_dossier_name = "custom"
