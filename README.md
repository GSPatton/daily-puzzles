# Puzzle Freaks

A personal daily puzzle site: sudoku, a mini crossword, cryptic clues, and a
Connections-style word/logic puzzle, generated fresh each morning.

## Project layout

```
generators/     one Python module per puzzle type (sudoku, crossword, cryptic, connections)
data/wordlists/ curated word/clue banks used by the generators
data/puzzles/   generated daily bundles, YYYY-MM-DD.json, plus manifest.json
runner.py       assembles the day's bundle and writes it to data/puzzles/
web/            the frontend (plain HTML/CSS/JS, no build step)
tests/          pytest suite for the generators
```

## Running it locally

Requires Python 3.11+ and no external packages.

Generate today's puzzle bundle:

```bash
python runner.py
```

This is idempotent — re-running it for a date that already has a bundle does
nothing unless you pass `--force`. Useful flags:

```bash
python runner.py --date 2026-09-03 --difficulty hard --force
```

Serve the frontend (any static file server works; the JS fetches
`../data/puzzles/...` relative to `web/`):

```bash
python3 -m http.server 8765
```

Then open `http://localhost:8765/web/index.html`.

## Tests

Requires `pytest` (`pip install pytest`):

```bash
python -m pytest tests/
```

## Hosting: GitHub Pages + a scheduled Action

This repo is set up to host on GitHub Pages with a GitHub Action
(`.github/workflows/daily-puzzle.yml`) that runs `runner.py` every morning
and commits the new bundle.

To finish wiring it up:

1. Create a GitHub repository and push this project to it.
2. In the repo's **Settings → Pages**, set the source to **Deploy from a
   branch**, branch `main`, folder `/ (root)`. The site will be served at
   `https://<you>.github.io/<repo>/` (the root `index.html` redirects to
   `web/index.html`).
3. The workflow runs on a daily cron (`10:00 UTC` by default — edit the
   `cron` line in the workflow file to suit your timezone) and pushes
   `data/puzzles/<date>.json` + the updated `manifest.json` back to `main`.
   You can also trigger it manually from the Actions tab
   (`workflow_dispatch`).
4. GitHub Pages redeploys automatically whenever `main` updates, so the new
   puzzle shows up shortly after the Action runs.

No secrets or extra setup are needed — the workflow uses the default
`GITHUB_TOKEN` (with `contents: write` permission) to push.

## Progress and streaks

Completion state and streaks live in the browser's `localStorage` — there's
no backend and no accounts. This is a single-user, personal project by
design.
