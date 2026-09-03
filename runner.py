#!/usr/bin/env python3
"""Assembles and writes the daily puzzle bundle to data/puzzles/YYYY-MM-DD.json."""
import argparse
import datetime
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "generators"))

import connections
import crossword
import cryptic
import sudoku
from common import rng_for_date

DATA_DIR = pathlib.Path(__file__).resolve().parent / "data" / "puzzles"
MANIFEST_PATH = DATA_DIR / "manifest.json"


def build_bundle(date_str: str, difficulty: str) -> dict:
    return {
        "date": date_str,
        "sudoku": sudoku.generate(difficulty=difficulty, rng=rng_for_date(date_str, "sudoku")),
        "mini_crossword": crossword.generate(rng=rng_for_date(date_str, "crossword")),
        "cryptic_clues": cryptic.generate(rng=rng_for_date(date_str, "cryptic")),
        "connections": connections.generate(rng=rng_for_date(date_str, "connections")),
    }


def update_manifest(date_str: str) -> None:
    dates = set()
    if MANIFEST_PATH.exists():
        dates.update(json.loads(MANIFEST_PATH.read_text()))
    dates.add(date_str)
    MANIFEST_PATH.write_text(json.dumps(sorted(dates), indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=datetime.date.today().isoformat(),
                         help="date to generate for (YYYY-MM-DD), defaults to today")
    parser.add_argument("--force", action="store_true",
                         help="regenerate even if a bundle for this date already exists")
    parser.add_argument("--difficulty", default="medium", choices=["easy", "medium", "hard"],
                         help="sudoku difficulty for this day's bundle")
    args = parser.parse_args()

    out_path = DATA_DIR / f"{args.date}.json"
    if out_path.exists() and not args.force:
        print(f"{out_path} already exists, skipping (use --force to regenerate)")
        return

    bundle = build_bundle(args.date, args.difficulty)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(bundle, indent=2))
    update_manifest(args.date)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
