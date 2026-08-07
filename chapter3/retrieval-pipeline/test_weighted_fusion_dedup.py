import pytest
from fusion import weighted_score_fusion

def test_weighted_score_fusion_preserves_top_score_on_duplicate_doc_id():
    """Verify weighted score fusion preserves top score when duplicate doc_ids exist in ranked list."""
    ranked_lists = {
        "dense": [("doc1", 0.95), ("doc2", 0.80), ("doc1", 0.10)],
        "sparse": [("doc1", 10.0), ("doc2", 5.0)]
    }

    results = weighted_score_fusion(ranked_lists)

    assert results[0][0] == "doc1"
    assert results[1][0] == "doc2"
    assert results[0][1] > results[1][1]
