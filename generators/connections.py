"""Connections-style word/logic puzzle generator: 4 categories x 4 words, no cross-category overlap."""
import json
import pathlib
import random

from common import validate_keys

CATEGORIES_PATH = (
    pathlib.Path(__file__).resolve().parent.parent / "data" / "wordlists" / "connections_categories.json"
)
TIERS = ["yellow", "green", "blue", "purple"]


def load_categories():
    return json.loads(CATEGORIES_PATH.read_text())


def generate(rng: random.Random = None) -> dict:
    if rng is None:
        rng = random.Random()

    categories = load_categories()
    if len(categories) < 4:
        raise RuntimeError("need at least 4 categories to generate a connections puzzle")

    chosen = rng.sample(categories, 4)

    seen = set()
    for cat in chosen:
        for word in cat["words"]:
            if word in seen:
                raise RuntimeError(f"word {word!r} appears in more than one selected category")
            seen.add(word)

    groups = [
        {"category": cat["category"], "words": cat["words"], "tier": tier}
        for cat, tier in zip(chosen, TIERS)
    ]

    result = {"type": "connections", "groups": groups}
    validate_keys(result, {"type", "groups"}, "connections")
    return result


if __name__ == "__main__":
    print(json.dumps(generate(), indent=2))
