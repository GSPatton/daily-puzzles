"""Sudoku generator: random full grid -> unique-solution puzzle via cell removal."""
import random

from common import validate_keys

DIFFICULTY_GIVENS = {"easy": 36, "medium": 30, "hard": 24}


def is_valid(grid, row, col, num):
    for i in range(9):
        if grid[row][i] == num or grid[i][col] == num:
            return False
    box_row, box_col = 3 * (row // 3), 3 * (col // 3)
    for r in range(box_row, box_row + 3):
        for c in range(box_col, box_col + 3):
            if grid[r][c] == num:
                return False
    return True


def find_empty(grid):
    for r in range(9):
        for c in range(9):
            if grid[r][c] == 0:
                return r, c
    return None


def generate_full_grid(rng: random.Random):
    grid = [[0] * 9 for _ in range(9)]

    def fill(grid):
        empty = find_empty(grid)
        if empty is None:
            return True
        r, c = empty
        nums = list(range(1, 10))
        rng.shuffle(nums)
        for n in nums:
            if is_valid(grid, r, c, n):
                grid[r][c] = n
                if fill(grid):
                    return True
                grid[r][c] = 0
        return False

    fill(grid)
    return grid


def count_solutions(grid, limit=2):
    count = 0

    def backtrack():
        nonlocal count
        if count >= limit:
            return
        empty = find_empty(grid)
        if empty is None:
            count += 1
            return
        r, c = empty
        for n in range(1, 10):
            if count >= limit:
                return
            if is_valid(grid, r, c, n):
                grid[r][c] = n
                backtrack()
                grid[r][c] = 0

    backtrack()
    return count


def remove_cells(solution, rng: random.Random, target_givens, max_passes=5):
    puzzle = [row[:] for row in solution]
    givens = 81
    for _ in range(max_passes):
        if givens <= target_givens:
            break
        filled = [(r, c) for r in range(9) for c in range(9) if puzzle[r][c] != 0]
        rng.shuffle(filled)
        removed_any = False
        for r, c in filled:
            if givens <= target_givens:
                break
            backup = puzzle[r][c]
            puzzle[r][c] = 0
            probe = [row[:] for row in puzzle]
            if count_solutions(probe, limit=2) == 1:
                givens -= 1
                removed_any = True
            else:
                puzzle[r][c] = backup
        if not removed_any:
            break
    return puzzle, givens


def generate(difficulty: str = "medium", rng: random.Random = None) -> dict:
    if rng is None:
        rng = random.Random()
    if difficulty not in DIFFICULTY_GIVENS:
        raise ValueError(f"unknown difficulty: {difficulty}")

    solution = generate_full_grid(rng)
    target = DIFFICULTY_GIVENS[difficulty]
    puzzle, givens_count = remove_cells(solution, rng, target)

    result = {
        "type": "sudoku",
        "difficulty": difficulty,
        "puzzle": puzzle,
        "solution": solution,
        "givens_count": givens_count,
    }
    validate_keys(result, {"type", "difficulty", "puzzle", "solution", "givens_count"}, "sudoku")
    return result


if __name__ == "__main__":
    import json

    print(json.dumps(generate(), indent=2))
