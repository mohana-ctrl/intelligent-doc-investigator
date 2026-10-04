"""
Intelligent Document Investigator Backend Package
"""

from .document_processor import DocumentProcessor, DocumentChunk
from .retriever import DocumentIndex
from .conflict_detector import ConflictDetector, ConflictReport, Claim
from .investigation_engine import InvestigationEngine
from .gemini_client import GeminiInvestigatorClient
from .sample_data import SAMPLE_DOSSIERS

__all__ = [
    "DocumentProcessor",
    "DocumentChunk",
    "DocumentIndex",
    "ConflictDetector",
    "ConflictReport",
    "Claim",
    "InvestigationEngine",
    "GeminiInvestigatorClient",
    "SAMPLE_DOSSIERS",
]
