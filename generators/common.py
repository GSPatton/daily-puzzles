"""Shared helpers for daily puzzle generators."""
import hashlib
import random


def rng_for_date(date_str: str, salt: str = "") -> random.Random:
    """Deterministic RNG seeded from a date (+ optional salt per puzzle type)."""
    seed_material = f"{date_str}:{salt}".encode()
    seed = int(hashlib.sha256(seed_material).hexdigest(), 16)
    return random.Random(seed)


def validate_keys(d: dict, required: set, type_name: str) -> None:
    missing = required - d.keys()
    if missing:
        raise ValueError(f"{type_name} puzzle missing keys: {missing}")
