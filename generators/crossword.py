"""Mini crossword generator: symmetric black-square template + backtracking fill."""
import json
import pathlib
import random
from collections import defaultdict

from common import validate_keys

SIZE = 5
CLUE_BANK_PATH = pathlib.Path(__file__).resolve().parent.parent / "data" / "wordlists" / "crossword_clues.json"

# 180-degree rotationally symmetric, connected black-square layouts where every run is
# length >= 2 (spec only forbids isolated single-letter entries). Chosen by searching all
# symmetric 5x5 patterns with 2-4 black squares for ones that minimize fully-crossing
# length-5 entries, which keeps backtracking fill fast and reliable.
TEMPLATES = [
    [[0, 4], [1, 3], [3, 1], [4, 0]],
    [[0, 0], [1, 1], [3, 3], [4, 4]],
    [[0, 3], [1, 0], [3, 4], [4, 1]],
    [[0, 1], [1, 4], [3, 0], [4, 3]],
]


def load_clue_bank():
    return json.loads(CLUE_BANK_PATH.read_text())


def words_by_length(clue_bank):
    by_len = defaultdict(list)
    for word in clue_bank:
        by_len[len(word)].append(word)
    return by_len


def compute_entries(black_squares, size=SIZE):
    black = {tuple(b) for b in black_squares}

    def is_black(r, c):
        return not (0 <= r < size and 0 <= c < size) or (r, c) in black

    entries = []
    number = 1
    for r in range(size):
        for c in range(size):
            if is_black(r, c):
                continue
            starts_across = is_black(r, c - 1) and not is_black(r, c + 1)
            starts_down = is_black(r - 1, c) and not is_black(r + 1, c)
            if not (starts_across or starts_down):
                continue
            if starts_across:
                length = 0
                while not is_black(r, c + length):
                    length += 1
                entries.append({"id": f"{number}across", "number": number, "row": r, "col": c,
                                 "direction": "across", "length": length})
            if starts_down:
                length = 0
                while not is_black(r + length, c):
                    length += 1
                entries.append({"id": f"{number}down", "number": number, "row": r, "col": c,
                                 "direction": "down", "length": length})
            number += 1
    return entries


def _cells(entry):
    for i in range(entry["length"]):
        r = entry["row"] + (i if entry["direction"] == "down" else 0)
        c = entry["col"] + (i if entry["direction"] == "across" else 0)
        yield r, c


def _rebuild_grid(assignment, entries_by_id, size=SIZE):
    grid = [[None] * size for _ in range(size)]
    for eid, word in assignment.items():
        entry = entries_by_id[eid]
        for (r, c), ch in zip(_cells(entry), word):
            grid[r][c] = ch
    return grid


# Bounds per fill attempt: candidates tried per slot and total recursive nodes visited.
# Keeps each attempt fast by failing quickly and letting generate() retry with a fresh
# shuffle, rather than exhaustively searching a huge tree over a large word list.
MAX_CANDIDATES_PER_NODE = 25
MAX_NODES_PER_ATTEMPT = 800


class _AttemptExhausted(Exception):
    pass


def _fill(assignment, remaining_ids, entries_by_id, by_length, rng, node_counter, size=SIZE):
    if not remaining_ids:
        return True

    node_counter[0] += 1
    if node_counter[0] > MAX_NODES_PER_ATTEMPT:
        raise _AttemptExhausted

    grid = _rebuild_grid(assignment, entries_by_id, size)
    used = set(assignment.values())

    best_id, best_candidates = None, None
    for eid in remaining_ids:
        entry = entries_by_id[eid]
        pattern = [grid[r][c] for r, c in _cells(entry)]
        candidates = [
            w for w in by_length.get(entry["length"], [])
            if w not in used and all(p is None or p == ch for p, ch in zip(pattern, w))
        ]
        if best_candidates is None or len(candidates) < len(best_candidates):
            best_id, best_candidates = eid, candidates
        if not candidates:
            break

    if not best_candidates:
        return False

    order = best_candidates[:]
    rng.shuffle(order)
    order = order[:MAX_CANDIDATES_PER_NODE]
    remaining_after = [eid for eid in remaining_ids if eid != best_id]
    for word in order:
        assignment[best_id] = word
        if _fill(assignment, remaining_after, entries_by_id, by_length, rng, node_counter, size):
            return True
        del assignment[best_id]
    return False


def generate(rng: random.Random = None, max_attempts_per_template: int = 20) -> dict:
    if rng is None:
        rng = random.Random()

    clue_bank = load_clue_bank()
    by_length = words_by_length(clue_bank)

    templates = TEMPLATES[:]
    rng.shuffle(templates)

    for black_squares in templates:
        entries = compute_entries(black_squares)
        entries_by_id = {e["id"]: e for e in entries}
        for _ in range(max_attempts_per_template):
            assignment = {}
            try:
                filled = _fill(assignment, list(entries_by_id.keys()), entries_by_id, by_length,
                                rng, [0])
            except _AttemptExhausted:
                continue
            if filled:
                grid = _rebuild_grid(assignment, entries_by_id)
                black_set = {tuple(b) for b in black_squares}
                solution_grid = [
                    ["#" if (r, c) in black_set else grid[r][c] for c in range(SIZE)]
                    for r in range(SIZE)
                ]
                result_entries = []
                for e in entries:
                    answer = assignment[e["id"]]
                    clue = clue_bank[answer]
                    if answer in clue.upper():
                        continue  # clue leaks the answer, skip this fill attempt's entry set
                    result_entries.append({**e, "answer": answer, "clue": clue})
                if len(result_entries) != len(entries):
                    continue
                result = {
                    "type": "mini_crossword",
                    "size": SIZE,
                    "black_squares": black_squares,
                    "entries": result_entries,
                    "solution_grid": solution_grid,
                }
                validate_keys(result, {"type", "size", "black_squares", "entries", "solution_grid"},
                              "mini_crossword")
                return result

    raise RuntimeError("crossword generation failed for all templates/attempts")


if __name__ == "__main__":
    print(json.dumps(generate(), indent=2))
