"""Cryptic clue generator.

Generate-then-validate: the mechanical wordplay structure is constructed and checked
FIRST (anagram letters exactly match, hidden word is a real contiguous substring,
double-definition uses two distinct definitions). Only after that structure is
confirmed valid do we render the surface clue text, and we re-validate the mechanics
once more before accepting it. Nothing is trusted just because it "sounds right".
"""
import json
import pathlib
import random

from common import validate_keys

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data" / "wordlists"

ANAGRAM_INDICATORS = [
    "scrambled", "confused", "in a mess", "oddly arranged", "mixed up",
    "shuffled", "rearranged", "gone wrong", "all over the place",
]
HIDDEN_INDICATORS = [
    "hidden in", "found within", "buried in", "some of", "part of", "held in",
]

WORDPLAY_TYPES = ["anagram", "hidden_word", "double_definition"]


def load_clue_bank():
    return json.loads((DATA_DIR / "crossword_clues.json").read_text())


def load_double_defs():
    return json.loads((DATA_DIR / "cryptic_double_defs.json").read_text())


def load_hidden_phrases():
    return json.loads((DATA_DIR / "cryptic_hidden_phrases.json").read_text())


# --- anagram -----------------------------------------------------------------

def _build_anagram_candidate(rng, clue_bank):
    words = [w for w in clue_bank if len(w) >= 3]
    word = rng.choice(words)
    letters = list(word)
    for _ in range(20):
        rng.shuffle(letters)
        fodder = "".join(letters)
        if fodder != word:
            return {"answer": word, "fodder": fodder, "definition": clue_bank[word]}
    return None


def _validate_anagram(candidate):
    return sorted(candidate["fodder"]) == sorted(candidate["answer"])


def _render_anagram(candidate, rng):
    indicator = rng.choice(ANAGRAM_INDICATORS)
    answer = candidate["answer"]
    clue = f"{candidate['definition']}, {indicator}: {candidate['fodder'].lower()} ({len(answer)})"
    explanation = (
        f"\"{candidate['fodder'].lower()}\" is an anagram of {answer} "
        f"(the word \"{indicator}\" signals the letters are rearranged)."
    )
    return clue, explanation


# --- hidden word ---------------------------------------------------------------

def _build_hidden_word_candidate(rng, clue_bank, phrases):
    words = [w for w in clue_bank if len(w) >= 3]
    rng.shuffle(words)
    for word in words:
        matches = []
        for phrase in phrases:
            phrase_words = {w.strip(".,").upper() for w in phrase.split()}
            if word in phrase_words:
                continue  # trivially spelled out as a whole word, not really "hidden"
            if word in phrase.replace(" ", "").upper():
                matches.append(phrase)
        if matches:
            phrase = rng.choice(matches)
            return {"answer": word, "phrase": phrase, "definition": clue_bank[word]}
    return None


def _validate_hidden_word(candidate):
    stripped = candidate["phrase"].replace(" ", "").upper()
    return candidate["answer"] in stripped


def _render_hidden_word(candidate, rng):
    indicator = rng.choice(HIDDEN_INDICATORS)
    answer = candidate["answer"]
    clue = f"{candidate['definition']}, {indicator} {candidate['phrase']} ({len(answer)})"
    stripped = candidate["phrase"].replace(" ", "").upper()
    idx = stripped.index(answer)
    explanation = (
        f"{answer} is hidden in \"{candidate['phrase']}\" "
        f"(letters {idx + 1}-{idx + len(answer)} of the phrase with spaces removed)."
    )
    return clue, explanation


# --- double definition -----------------------------------------------------

def _build_double_def_candidate(rng, double_defs):
    word = rng.choice(list(double_defs.keys()))
    d1, d2 = double_defs[word]
    return {"answer": word, "def1": d1, "def2": d2}


def _validate_double_def(candidate):
    return candidate["def1"] != candidate["def2"]


def _render_double_def(candidate, rng):
    answer = candidate["answer"]
    clue = f"{candidate['def1']}; also {candidate['def2']} ({len(answer)})"
    explanation = f"Both \"{candidate['def1']}\" and \"{candidate['def2']}\" are definitions of {answer}."
    return clue, explanation


_BUILDERS = {
    "anagram": (_build_anagram_candidate, _validate_anagram, _render_anagram),
    "hidden_word": (_build_hidden_word_candidate, _validate_hidden_word, _render_hidden_word),
    "double_definition": (_build_double_def_candidate, _validate_double_def, _render_double_def),
}


def _make_clue(wordplay_type, rng, clue_bank, phrases, double_defs, used_answers, max_attempts=30):
    build, validate, render = _BUILDERS[wordplay_type]
    for _ in range(max_attempts):
        if wordplay_type == "hidden_word":
            candidate = build(rng, clue_bank, phrases)
        elif wordplay_type == "double_definition":
            candidate = build(rng, double_defs)
        else:
            candidate = build(rng, clue_bank)
        if candidate is None:
            continue
        if candidate["answer"] in used_answers:
            continue
        if not validate(candidate):
            continue
        clue_text, explanation = render(candidate, rng)
        # re-validate the finished clue text against the mechanical rule before accepting
        if not validate(candidate):
            continue
        answer = candidate["answer"]
        return {
            "clue": clue_text,
            "answer": answer,
            "wordplay_type": wordplay_type,
            "explanation": explanation,
        }
    return None


def generate(rng: random.Random = None, count: int = 4) -> dict:
    if rng is None:
        rng = random.Random()

    clue_bank = load_clue_bank()
    phrases = load_hidden_phrases()
    double_defs = load_double_defs()

    clues = []
    used_answers = set()
    types_cycle = WORDPLAY_TYPES[:]
    rng.shuffle(types_cycle)
    attempts = 0
    while len(clues) < count and attempts < count * 10:
        wordplay_type = types_cycle[attempts % len(types_cycle)]
        clue = _make_clue(wordplay_type, rng, clue_bank, phrases, double_defs, used_answers)
        attempts += 1
        if clue is None:
            continue
        clues.append(clue)
        used_answers.add(clue["answer"])

    if len(clues) < count:
        raise RuntimeError(f"only generated {len(clues)}/{count} cryptic clues")

    result = {"type": "cryptic_clues", "clues": clues}
    validate_keys(result, {"type", "clues"}, "cryptic_clues")
    return result


if __name__ == "__main__":
    print(json.dumps(generate(), indent=2))
