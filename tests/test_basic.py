from __future__ import annotations

from brand_name_gen import generate_names


def test_generate_names_basic():
    names = generate_names(["solar", "green"], style="modern", limit=10)
    assert isinstance(names, list)
    assert names and len(names) <= 10
    assert all(isinstance(n, str) and n[0].isupper() for n in names)


def test_generate_names_empty_keywords():
    assert generate_names([], limit=5) == []

