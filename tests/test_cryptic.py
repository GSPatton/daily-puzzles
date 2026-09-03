import random

import pytest
import cryptic


@pytest.mark.parametrize("seed", range(10))
def test_generate_schema_and_mechanics(seed):
    result = cryptic.generate(rng=random.Random(seed), count=4)

    assert result["type"] == "cryptic_clues"
    assert len(result["clues"]) == 4

    answers = [c["answer"] for c in result["clues"]]
    assert len(answers) == len(set(answers)), "answers must be distinct within a day's set"

    for clue in result["clues"]:
        assert clue["wordplay_type"] in cryptic.WORDPLAY_TYPES
        assert f"({len(clue['answer'])})" in clue["clue"], "answer length must be shown"
        assert clue["answer"] not in clue["clue"].replace(f"({len(clue['answer'])})", "")
        assert clue["explanation"]


def test_anagram_mechanically_valid():
    rng = random.Random(5)
    clue_bank = cryptic.load_clue_bank()
    for _ in range(20):
        candidate = cryptic._build_anagram_candidate(rng, clue_bank)
        assert candidate is not None
        assert cryptic._validate_anagram(candidate)
        assert candidate["fodder"] != candidate["answer"]


def test_hidden_word_is_real_substring_not_whole_word():
    rng = random.Random(7)
    clue_bank = cryptic.load_clue_bank()
    phrases = cryptic.load_hidden_phrases()
    for _ in range(20):
        candidate = cryptic._build_hidden_word_candidate(rng, clue_bank, phrases)
        if candidate is None:
            continue
        assert cryptic._validate_hidden_word(candidate)
        phrase_words = {w.strip(".,").upper() for w in candidate["phrase"].split()}
        assert candidate["answer"] not in phrase_words


def test_double_definition_uses_two_distinct_defs():
    rng = random.Random(3)
    double_defs = cryptic.load_double_defs()
    for _ in range(10):
        candidate = cryptic._build_double_def_candidate(rng, double_defs)
        assert cryptic._validate_double_def(candidate)
        assert candidate["def1"] != candidate["def2"]


def test_generate_deterministic_with_seed():
    a = cryptic.generate(rng=random.Random(42))
    b = cryptic.generate(rng=random.Random(42))
    assert a == b
