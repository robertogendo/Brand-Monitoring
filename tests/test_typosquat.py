import pytest
from utils import is_typosquat

def test_typosquat_detects_similar():
    official = ["brandplaceholder.com", "example.com"]
    assert is_typosquat("brandplaceh0lder.com", official, threshold=60)
    assert not is_typosquat("unrelated-site.com", official, threshold=60)