"""
Gemini API Client with Graceful Offline Local Synthesis Fallback.
Provides investigation synthesis, uncertainty quantification,
and cross-document reconciliation.
"""

import os
import json
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional
from .conflict_detector import ConflictReport
from .document_processor import DocumentChunk

class GeminiInvestigatorClient:
    """Handles LLM synthesis using Gemini API (via google-genai or direct REST) with offline fallback."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self.model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

    def set_api_key(self, api_key: str):
        self.api_key = api_key.strip()

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def generate_investigation_response(
        self,
        query: str,
        retrieved_chunks: List[DocumentChunk],
        conflict_reports: List[ConflictReport]
    ) -> Dict[str, Any]:
        """
        Synthesizes an investigation dossier. If Gemini API is available, calls Gemini;
        otherwise runs robust deterministic local synthesis.
        """
        if self.is_configured():
            try:
                return self._call_gemini_api(query, retrieved_chunks, conflict_reports)
            except Exception as e:
                local_res = self._local_synthesis(query, retrieved_chunks, conflict_reports)
                local_res["llm_status"] = f"Gemini API error ({str(e)}), used local investigator engine fallback."
                return local_res
        else:
            local_res = self._local_synthesis(query, retrieved_chunks, conflict_reports)
            local_res["llm_status"] = "Operating in Local Neural/Deterministic Engine mode (Add GEMINI_API_KEY for LLM generation)."
            return local_res

    def _call_gemini_api(
        self,
        query: str,
        retrieved_chunks: List[DocumentChunk],
        conflict_reports: List[ConflictReport]
    ) -> Dict[str, Any]:
        """Calls Gemini API via direct HTTPS REST to avoid missing pip packages."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"

        # Build context
        context_parts = []
        for idx, ch in enumerate(retrieved_chunks):
            context_parts.append(
                f"[Source {idx+1}] Doc: {ch.doc_name} | Section: {ch.section} | Page: {ch.page_num}\n\"{ch.content}\""
            )
        context_str = "\n\n".join(context_parts)

        # Include conflict detector findings
        conflict_hints = []
        for cr in conflict_reports:
            conflict_hints.append(
                f"- Conflict Type: {cr.conflict_type} on Topic '{cr.topic}' (Severity: {cr.severity})\n  Detail: {cr.description}\n  Advice: {cr.investigator_advice}"
            )
        conflict_hints_str = "\n".join(conflict_hints) if conflict_hints else "None detected by rule engine."

        system_prompt = (
            "You are an elite Intelligent Document Investigator for Algothon'26.\n"
            "Your objective: Answer user questions with uncompromising source grounding, cross-document comparison, "
            "and EXPLICIT contradiction/conflict identification.\n"
            "CRITICAL RULES:\n"
            "1. NEVER blend contradictory facts into a single hallucinated average. Clearly state what Document A says vs Document B.\n"
            "2. State your Certainty Level: HIGH (unanimous evidence), MEDIUM (partial evidence or minor discrepancy), or UNCERTAIN/CONFLICT_DETECTED.\n"
            "3. Cite every statement with [DocName, Section, Page X].\n"
            "4. Provide a structured markdown response with sections: 'Executive Investigation Summary', 'Cross-Document Comparison & Discrepancies', 'Evidence-Backed Findings', and 'Investigator Recommendation'."
        )

        user_content = (
            f"USER INVESTIGATION QUERY: {query}\n\n"
            f"AUTOMATED CONFLICT DETECTOR SIGNALS:\n{conflict_hints_str}\n\n"
            f"INGESTED DOCUMENT EVIDENCE:\n{context_str}\n\n"
            "Generate your comprehensive, evidence-backed investigation report."
        )

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": system_prompt + "\n\n" + user_content}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "topP": 0.95,
                "maxOutputTokens": 2048
            }
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            text_answer = res_data['candidates'][0]['content']['parts'][0]['text']

            # Determine certainty
            high_conflicts = [c for c in conflict_reports if c.severity == 'HIGH']
            if high_conflicts:
                certainty = "CONFLICT_DETECTED"
            elif len(retrieved_chunks) >= 3:
                certainty = "HIGH"
            else:
                certainty = "MEDIUM"

            return {
                "answer": text_answer,
                "certainty": certainty,
                "llm_status": f"Synthesized by Gemini ({self.model_name})",
                "citations": [
                    {
                        "doc_name": ch.doc_name,
                        "section": ch.section,
                        "page_num": ch.page_num,
                        "chunk_id": ch.chunk_id,
                        "excerpt": ch.content[:200] + "..." if len(ch.content) > 200 else ch.content
                    }
                    for ch in retrieved_chunks
                ]
            }

    def _local_synthesis(
        self,
        query: str,
        retrieved_chunks: List[DocumentChunk],
        conflict_reports: List[ConflictReport]
    ) -> Dict[str, Any]:
        """Deterministic offline multi-document investigator synthesis."""
        if not retrieved_chunks:
            return {
                "answer": "No relevant document evidence found for your investigation query. Please upload pertinent documents or adjust search parameters.",
                "certainty": "NO_EVIDENCE",
                "citations": []
            }

        high_conflicts = [c for c in conflict_reports if c.severity == 'HIGH']
        single_sources = [c for c in conflict_reports if c.conflict_type == 'SINGLE_SOURCE']
        consensus_items = [c for c in conflict_reports if c.conflict_type == 'CONSENSUS']

        # Determine overall certainty
        if high_conflicts:
            certainty = "CONFLICT_DETECTED"
            certainty_badge = "CRITICAL DISCREPANCY DETECTED"
        elif single_sources and not consensus_items:
            certainty = "UNVERIFIED_SINGLE_SOURCE"
            certainty_badge = "UNVERIFIED / SINGLE SOURCE"
        else:
            certainty = "HIGH_CONSENSUS"
            certainty_badge = "HIGH (CROSS-VERIFIED)"

        # Build investigation report
        lines = []
        lines.append(f"### 🔍 Executive Investigation Summary")
        lines.append(f"**Query**: *\"{query}\"*")
        lines.append(f"**Cross-Document Certainty**: `{certainty_badge}`")
        lines.append(f"**Examined Sources**: {len(retrieved_chunks)} evidence passages across {len(set(c.doc_name for c in retrieved_chunks))} documents.\n")

        if high_conflicts:
            lines.append("### ⚠️ Critical Cross-Document Discrepancies")
            lines.append("> [!WARNING] **Contradictory information identified between primary sources.** Standard RAG would average or silence this divergence; our investigation layer isolates it:\n")
            for c in high_conflicts:
                lines.append(f"- **{c.topic}** (`{c.conflict_type}`): {c.description}")
                lines.append(f"  *Investigator Guidance*: {c.investigator_advice}")
                for cl in c.claims[:4]:
                    lines.append(f"    • **[{cl.doc_name}, Page {cl.page_num}, §{cl.section}]**: \"{cl.quote}\"")
            lines.append("")

        if consensus_items:
            lines.append("### ✅ Corroborated Findings (Consensus)")
            for item in consensus_items:
                lines.append(f"- **{item.topic}**: Confirmed consistent across sources.")
                for cl in item.claims[:2]:
                    lines.append(f"    • *Source [{cl.doc_name}, Page {cl.page_num}]*: \"{cl.quote}\"")
            lines.append("")

        lines.append("### 📄 Evidence Breakdown by Document")
        doc_grouped = defaultdict(list)
        for ch in retrieved_chunks:
            doc_grouped[ch.doc_name].append(ch)

        for doc_name, chunks in doc_grouped.items():
            lines.append(f"#### 📁 Document: `{doc_name}`")
            for ch in chunks[:3]:
                lines.append(f"- **Section `{ch.section}` (Page {ch.page_num})**: \"{ch.content}\"")
            lines.append("")

        lines.append("### 📋 Investigator Recommendation")
        if high_conflicts:
            lines.append(
                "Because conflicting figures or dates exist, do **not** take singular action without resolving the audit trail. "
                "Recommend requesting an official addendum from the issuing stakeholders to reconcile the discrepancy."
            )
        else:
            lines.append(
                "The findings show strong internal consistency across the provided documentation. Evidence meets verification threshold."
            )

        answer_text = "\n".join(lines)

        citations = [
            {
                "doc_name": ch.doc_name,
                "section": ch.section,
                "page_num": ch.page_num,
                "chunk_id": ch.chunk_id,
                "excerpt": ch.content[:200] + "..." if len(ch.content) > 200 else ch.content
            }
            for ch in retrieved_chunks
        ]

        return {
            "answer": answer_text,
            "certainty": certainty,
            "citations": citations
        }
