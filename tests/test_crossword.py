import random

import pytest
import crossword


@pytest.mark.parametrize("seed", range(8))
def test_generate_schema_and_properties(seed):
    result = crossword.generate(rng=random.Random(seed))

    assert result["type"] == "mini_crossword"
    assert result["size"] == 5
    grid = result["solution_grid"]
    assert len(grid) == 5 and all(len(row) == 5 for row in grid)

    black_set = {tuple(b) for b in result["black_squares"]}
    for r in range(5):
        for c in range(5):
            if (r, c) in black_set:
                assert grid[r][c] == "#"
            else:
                assert grid[r][c] is not None and len(grid[r][c]) == 1

    answers = [e["answer"] for e in result["entries"]]
    assert len(answers) == len(set(answers)), "answers must be distinct"

    for entry in result["entries"]:
        assert len(entry["answer"]) == entry["length"]
        assert entry["length"] >= 2, "no isolated single-letter entries"
        # answer must match the solution grid along its cells
        for i, ch in enumerate(entry["answer"]):
            r = entry["row"] + (i if entry["direction"] == "down" else 0)
            c = entry["col"] + (i if entry["direction"] == "across" else 0)
            assert grid[r][c] == ch
        # clue must not leak the answer
        assert entry["answer"] not in entry["clue"].upper()


def test_generate_deterministic_with_seed():
    a = crossword.generate(rng=random.Random(99))
    b = crossword.generate(rng=random.Random(99))
    assert a == b


def test_compute_entries_no_length_one():
    for template in crossword.TEMPLATES:
        entries = crossword.compute_entries(template)
        assert all(e["length"] >= 2 for e in entries)


def test_compute_entries_symmetric_templates_produce_entries():
    for template in crossword.TEMPLATES:
        entries = crossword.compute_entries(template)
        assert len(entries) >= 8


def test_words_by_length_covers_needed_lengths():
    clue_bank = crossword.load_clue_bank()
    by_length = crossword.words_by_length(clue_bank)
    needed_lengths = {e["length"] for t in crossword.TEMPLATES for e in crossword.compute_entries(t)}
    for length in needed_lengths:
        assert len(by_length.get(length, [])) > 0
