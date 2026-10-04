"""
Integration tests for End-to-End Investigation Engine on Benchmark Dossiers.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.investigation_engine import InvestigationEngine

def test_ma_dossier_investigation():
    engine = InvestigationEngine()
    engine.load_sample_dossier("ma_due_diligence")

    # 1. Test valuation query
    res = engine.query_investigation("What is the agreed purchase price and valuation?")
    assert res["certainty"] == "CONFLICT_DETECTED"
    assert any(c["conflict_type"] == "NUMERICAL_MISMATCH" for c in res["conflicts"])
    assert len(res["citations"]) > 0
    print("PASS: M&A Valuation Conflict Detected ($50M vs $41.8M)")

    # 2. Test closing date query
    res_date = engine.query_investigation("What is the scheduled closing date for the acquisition?")
    assert res_date["certainty"] == "CONFLICT_DETECTED"
    assert any(c["conflict_type"] == "TEMPORAL_MISMATCH" for c in res_date["conflicts"])
    print("PASS: M&A Closing Date Conflict Detected (Oct 15 vs Nov 30)")

    # 3. Test pairwise conflict matrix
    matrix_res = engine.get_cross_document_conflict_matrix()
    assert matrix_res["conflict_count"] >= 2
    print("PASS: M&A Cross-Document Pairwise Conflict Matrix Generated")


def test_clinical_safety_dossier():
    engine = InvestigationEngine()
    engine.load_sample_dossier("clinical_safety")

    res = engine.query_investigation("What is the maximum allowed daily dosage for CT-904?")
    assert res["certainty"] == "CONFLICT_DETECTED"
    print("PASS: Clinical Trial Dosage Conflict Detected (100mg vs 50mg)")


if __name__ == "__main__":
    test_ma_dossier_investigation()
    test_clinical_safety_dossier()
    print("\nAll End-to-End Investigation tests passed successfully!")
