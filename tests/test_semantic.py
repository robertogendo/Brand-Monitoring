import pytest
from scorer import semantic_similarity

def test_semantic_similarity_prefers_brand_templates():
    templates = ["BRAND_PLACEHOLDER is giving away", "Update your BRAND_PLACEHOLDER profile"]
    text_similar = "BRAND_PLACEHOLDER is giving away free airtime to users"
    text_unrelated = "This is a random unrelated sentence about gardening."
    sim_similar = semantic_similarity(text_similar, templates)
    sim_unrelated = semantic_similarity(text_unrelated, templates)
    assert isinstance(sim_similar, float)
    assert isinstance(sim_unrelated, float)
    assert sim_similar > sim_unrelated