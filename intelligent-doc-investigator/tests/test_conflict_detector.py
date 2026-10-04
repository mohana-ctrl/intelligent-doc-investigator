"""
Unit tests for Conflict & Contradiction Detection Engine.
Verifies numerical, temporal, polarity, and consensus classification.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.conflict_detector import ConflictDetector, Claim
from backend.document_processor import DocumentChunk

def test_numerical_conflict_detection():
    detector = ConflictDetector()

    chunk1 = DocumentChunk(
        chunk_id="c1",
        doc_id="doc_a",
        doc_name="Term_Sheet_v1.md",
        content="The agreed acquisition valuation for the company is $50,000,000 USD payable in cash.",
        section="Valuation",
        page_num=1
    )

    chunk2 = DocumentChunk(
        chunk_id="c2",
        doc_id="doc_b",
        doc_name="Audit_Report_v2.md",
        content="Following forensic accounting adjustments, the revised valuation is established at $41,800,000 USD.",
        section="Adjustments",
        page_num=2
    )

    conflicts = detector.analyze_cross_document_conflicts([chunk1, chunk2])
    
    assert any(c.conflict_type == "NUMERICAL_MISMATCH" for c in conflicts), "Failed to detect numerical valuation mismatch!"
    high_conflict = [c for c in conflicts if c.conflict_type == "NUMERICAL_MISMATCH"][0]
    assert high_conflict.severity == "HIGH"
    print("PASS: test_numerical_conflict_detection")


def test_temporal_date_conflict_detection():
    detector = ConflictDetector()

    chunk1 = DocumentChunk(
        chunk_id="c1",
        doc_id="doc_a",
        doc_name="Contract_Draft.md",
        content="The definitive closing date is scheduled for October 15, 2026.",
        section="Milestones",
        page_num=1
    )

    chunk2 = DocumentChunk(
        chunk_id="c2",
        doc_id="doc_b",
        doc_name="Board_Minutes.md",
        content="The Board voted to postpone the final closing date to November 30, 2026.",
        section="Resolutions",
        page_num=3
    )

    conflicts = detector.analyze_cross_document_conflicts([chunk1, chunk2])
    assert any(c.conflict_type == "TEMPORAL_MISMATCH" for c in conflicts), "Failed to detect temporal date mismatch!"
    print("PASS: test_temporal_date_conflict_detection")


def test_polarity_contradiction_detection():
    detector = ConflictDetector()

    chunk1 = DocumentChunk(
        chunk_id="c1",
        doc_id="doc_a",
        doc_name="Legal_Warranty.md",
        content="The software intellectual property is approved and free from claims.",
        section="Warranties",
        page_num=1
    )

    chunk2 = DocumentChunk(
        chunk_id="c2",
        doc_id="doc_b",
        doc_name="IP_Audit.md",
        content="The codebase is not cleanly owned and rejected due to license infringement.",
        section="Infringements",
        page_num=4
    )

    conflicts = detector.analyze_cross_document_conflicts([chunk1, chunk2])
    assert any(c.conflict_type == "POLARITY_CONTRADICTION" for c in conflicts), "Failed to detect polarity contradiction!"
    print("PASS: test_polarity_contradiction_detection")


def test_consensus_agreement():
    detector = ConflictDetector()

    chunk1 = DocumentChunk(
        chunk_id="c1",
        doc_id="doc_a",
        doc_name="Spec_A.md",
        content="The network port requirement is approved for port 8080.",
        section="Network",
        page_num=1
    )

    chunk2 = DocumentChunk(
        chunk_id="c2",
        doc_id="doc_b",
        doc_name="Spec_B.md",
        content="All ingress traffic is approved for port 8080.",
        section="Ports",
        page_num=1
    )

    conflicts = detector.analyze_cross_document_conflicts([chunk1, chunk2])
    assert any(c.conflict_type == "CONSENSUS" for c in conflicts), "Failed to confirm consensus agreement!"
    print("PASS: test_consensus_agreement")


if __name__ == "__main__":
    test_numerical_conflict_detection()
    test_temporal_date_conflict_detection()
    test_polarity_contradiction_detection()
    test_consensus_agreement()
    print("\nAll Conflict Detector unit tests passed successfully!")
