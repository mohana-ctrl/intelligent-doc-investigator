"""
Unit tests for In-Memory DocumentIndex and Balanced Multi-Doc Sourcing.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.retriever import DocumentIndex
from backend.document_processor import DocumentProcessor

def test_balanced_multi_doc_retrieval():
    processor = DocumentProcessor()
    index = DocumentIndex()

    # Document 1: heavy repetition of keyword
    doc1_text = """# Financial Overview
The project budget is $50,000. The budget is very strict.
Additional budget details are discussed elsewhere."""
    chunks1 = processor.process_raw_text(doc1_text, "doc1", "Doc_A.md")
    index.add_chunks(chunks1)

    # Document 2: single mention of budget, but different number
    doc2_text = """# Auditor Discrepancy
The audited project budget is established at $75,000 due to revised requirements."""
    chunks2 = processor.process_raw_text(doc2_text, "doc2", "Doc_B.md")
    index.add_chunks(chunks2)

    # Balanced retrieval ensures Doc_B is NOT pushed out of top results
    retrieved = index.retrieve("what is the project budget?", top_k=4, per_doc_quota=2)
    doc_ids_returned = {chunk.doc_id for chunk, _ in retrieved}

    assert "doc1" in doc_ids_returned, "Doc 1 missing from retrieval!"
    assert "doc2" in doc_ids_returned, "Doc 2 missing from retrieval! Balanced Sourcing failed."
    print("PASS: test_balanced_multi_doc_retrieval")


def test_section_boundary_detection():
    processor = DocumentProcessor()
    text = """# Executive Summary
This is overview content.

## SECTION 2: Payment Milestones
Payment of $10,000 is due on milestone 1.
"""
    chunks = processor.process_raw_text(text, "doc_test", "Contract.md")
    assert len(chunks) >= 2
    assert any("Payment Milestones" in c.section for c in chunks)
    print("PASS: test_section_boundary_detection")


if __name__ == "__main__":
    test_balanced_multi_doc_retrieval()
    test_section_boundary_detection()
    print("\nAll Retriever unit tests passed successfully!")
