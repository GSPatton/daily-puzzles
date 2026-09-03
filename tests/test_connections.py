import random

import pytest
import connections


@pytest.mark.parametrize("seed", range(15))
def test_generate_schema_and_properties(seed):
    result = connections.generate(rng=random.Random(seed))

    assert result["type"] == "connections"
    assert len(result["groups"]) == 4

    all_words = []
    tiers_seen = []
    categories_seen = set()
    for group in result["groups"]:
        assert len(group["words"]) == 4
        assert group["tier"] in connections.TIERS
        tiers_seen.append(group["tier"])
        categories_seen.add(group["category"])
        all_words.extend(group["words"])

    assert len(all_words) == 16
    assert len(set(all_words)) == 16, "no word should appear in more than one group"
    assert len(categories_seen) == 4, "categories must be distinct"
    assert sorted(tiers_seen) == sorted(connections.TIERS)


def test_generate_deterministic_with_seed():
    a = connections.generate(rng=random.Random(11))
    b = connections.generate(rng=random.Random(11))
    assert a == b


def test_category_bank_has_no_cross_category_duplicates():
    categories = connections.load_categories()
    all_words = [w for cat in categories for w in cat["words"]]
    assert len(all_words) == len(set(all_words))
