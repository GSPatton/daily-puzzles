import random

import pytest
import sudoku


def rows_cols_boxes_valid(grid):
    for r in range(9):
        row = grid[r]
        if sorted(row) != list(range(1, 10)):
            return False
    for c in range(9):
        col = [grid[r][c] for r in range(9)]
        if sorted(col) != list(range(1, 10)):
            return False
    for br in range(0, 9, 3):
        for bc in range(0, 9, 3):
            box = [grid[r][c] for r in range(br, br + 3) for c in range(bc, bc + 3)]
            if sorted(box) != list(range(1, 10)):
                return False
    return True


def test_full_grid_is_valid_sudoku():
    grid = sudoku.generate_full_grid(random.Random(1))
    assert rows_cols_boxes_valid(grid)


def test_full_grid_deterministic_with_seed():
    a = sudoku.generate_full_grid(random.Random(42))
    b = sudoku.generate_full_grid(random.Random(42))
    assert a == b


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_generate_schema_and_properties(difficulty):
    result = sudoku.generate(difficulty=difficulty, rng=random.Random(7))

    assert result["type"] == "sudoku"
    assert result["difficulty"] == difficulty
    assert len(result["puzzle"]) == 9 and all(len(row) == 9 for row in result["puzzle"])
    assert len(result["solution"]) == 9 and all(len(row) == 9 for row in result["solution"])

    # solution is fully solved and valid
    assert rows_cols_boxes_valid(result["solution"])

    # puzzle's non-zero cells match the solution
    puzzle, solution = result["puzzle"], result["solution"]
    for r in range(9):
        for c in range(9):
            if puzzle[r][c] != 0:
                assert puzzle[r][c] == solution[r][c]

    # givens_count matches actual non-zero cell count
    actual_givens = sum(1 for row in puzzle for cell in row if cell != 0)
    assert actual_givens == result["givens_count"]

    # target reached (or close to it if uniqueness constraints prevented it)
    target = sudoku.DIFFICULTY_GIVENS[difficulty]
    assert 17 <= result["givens_count"] <= target + 6

    # puzzle has exactly one solution, and it's the stored solution
    probe = [row[:] for row in puzzle]
    assert sudoku.count_solutions(probe, limit=2) == 1


def test_generate_unknown_difficulty_raises():
    with pytest.raises(ValueError):
        sudoku.generate(difficulty="impossible")


def test_count_solutions_detects_multiple():
    # an almost-empty grid has many solutions
    grid = [[0] * 9 for _ in range(9)]
    assert sudoku.count_solutions(grid, limit=2) == 2


def test_count_solutions_detects_unique():
    full = sudoku.generate_full_grid(random.Random(3))
    assert sudoku.count_solutions([row[:] for row in full], limit=2) == 1
