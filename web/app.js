const THEME_KEY = "puzzleFreaks:theme";

function initTheme() {
  const saved = localStorage.getItem(THEME_KEY);
  if (saved) document.documentElement.setAttribute("data-theme", saved);
  document.getElementById("theme-toggle").addEventListener("click", () => {
    const current = document.documentElement.getAttribute("data-theme")
      || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    const next = current === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem(THEME_KEY, next);
  });
}

function initTabs() {
  document.getElementById("tabs").addEventListener("click", e => {
    const btn = e.target.closest("button[data-tab]");
    if (!btn) return;
    document.querySelectorAll("nav.tabs button").forEach(b => b.classList.remove("active"));
    document.querySelectorAll("main .panel").forEach(p => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(`panel-${btn.dataset.tab}`).classList.add("active");
  });
}

function formatDateline(dateStr) {
  const d = new Date(`${dateStr}T00:00:00`);
  return d.toLocaleDateString(undefined, { weekday: "long", year: "numeric", month: "long", day: "numeric" });
}

function refreshTabChecks(date) {
  document.querySelectorAll("nav.tabs button[data-tab]").forEach(btn => {
    const type = btn.dataset.tab;
    const existingCheck = btn.querySelector(".check");
    if (existingCheck) existingCheck.remove();
    if (PuzzleProgress.isComplete(date, type)) {
      const span = document.createElement("span");
      span.className = "check";
      span.textContent = "✓";
      btn.appendChild(span);
    }
  });
}

function refreshStreakBanner(date) {
  const streak = PuzzleProgress.getStreak(date);
  const banner = document.getElementById("streak-banner");
  banner.innerHTML = streak > 0
    ? `<strong>${streak}</strong> day streak`
    : "Complete all four today to start a streak";
}

async function loadBundle() {
  const manifest = await fetch("../data/puzzles/manifest.json").then(r => r.json());
  const today = new Date().toISOString().slice(0, 10);
  const requested = new URLSearchParams(location.search).get("date");

  let date;
  if (requested && manifest.includes(requested)) {
    date = requested;
  } else {
    const available = manifest.filter(d => d <= today).sort();
    date = available.length ? available[available.length - 1] : manifest.sort().slice(-1)[0];
  }

  const bundle = await fetch(`../data/puzzles/${date}.json`).then(r => r.json());
  document.getElementById("dateline").textContent =
    formatDateline(date) + (date !== today ? " (archived day)" : "");
  return bundle;
}

function startTimer(elId) {
  const el = document.getElementById(elId);
  const start = Date.now();
  const interval = setInterval(() => {
    const elapsed = Math.floor((Date.now() - start) / 1000);
    const m = Math.floor(elapsed / 60);
    const s = elapsed % 60;
    el.textContent = `${m}:${String(s).padStart(2, "0")}`;
  }, 1000);
  return () => clearInterval(interval);
}

function renderSudoku(sudoku, date) {
  const table = document.getElementById("sudoku-grid");
  table.innerHTML = "";
  for (let r = 0; r < 9; r++) {
    const tr = document.createElement("tr");
    for (let c = 0; c < 9; c++) {
      const td = document.createElement("td");
      const given = sudoku.puzzle[r][c];
      const input = document.createElement("input");
      input.maxLength = 1;
      input.dataset.row = r;
      input.dataset.col = c;
      if (given !== 0) {
        input.value = given;
        input.disabled = true;
      }
      input.addEventListener("input", () => {
        input.value = input.value.replace(/[^1-9]/, "");
      });
      td.appendChild(input);
      tr.appendChild(td);
    }
    table.appendChild(tr);
  }

  const stopTimer = startTimer("sudoku-timer");
  const resultEl = document.getElementById("sudoku-result");
  let gaveUp = false;

  function currentGrid() {
    const grid = Array.from({ length: 9 }, () => Array(9).fill(0));
    table.querySelectorAll("input").forEach(input => {
      grid[input.dataset.row][input.dataset.col] = input.value ? Number(input.value) : 0;
    });
    return grid;
  }

  document.getElementById("sudoku-check").addEventListener("click", () => {
    const solved = JSON.stringify(currentGrid()) === JSON.stringify(sudoku.solution);
    if (solved && gaveUp) {
      resultEl.textContent = "Correct, but revealed cells don't count toward your streak.";
      resultEl.className = "result-msg";
    } else {
      resultEl.textContent = solved ? "Solved!" : "Not solved yet (or has mistakes).";
      resultEl.className = `result-msg ${solved ? "correct" : "wrong"}`;
    }
    if (solved && !gaveUp) {
      stopTimer();
      PuzzleProgress.markComplete(date, "sudoku");
      refreshTabChecks(date);
      refreshStreakBanner(date);
    }
  });

  document.getElementById("sudoku-hint").addEventListener("click", () => {
    const empties = Array.from(table.querySelectorAll("input")).filter(i => !i.disabled && !i.value);
    if (empties.length === 0) return;
    const pick = empties[Math.floor(Math.random() * empties.length)];
    pick.value = sudoku.solution[pick.dataset.row][pick.dataset.col];
    pick.disabled = true;
  });

  document.getElementById("sudoku-reveal").addEventListener("click", () => {
    stopTimer();
    gaveUp = true;
    table.querySelectorAll("input").forEach(input => {
      input.value = sudoku.solution[input.dataset.row][input.dataset.col];
    });
    resultEl.textContent = "Solution revealed.";
    resultEl.className = "result-msg";
  });
}

function entryCells(entry) {
  const cells = [];
  for (let i = 0; i < entry.length; i++) {
    const r = entry.row + (entry.direction === "down" ? i : 0);
    const c = entry.col + (entry.direction === "across" ? i : 0);
    cells.push([r, c]);
  }
  return cells;
}

function renderCrossword(crosswordData, date) {
  const { size, black_squares, entries, solution_grid } = crosswordData;
  const blackSet = new Set(black_squares.map(([r, c]) => `${r},${c}`));
  const entriesById = Object.fromEntries(entries.map(e => [e.id, e]));

  const cellEntries = {};
  for (let r = 0; r < size; r++) {
    for (let c = 0; c < size; c++) cellEntries[`${r},${c}`] = { across: null, down: null };
  }
  entries.forEach(entry => {
    entryCells(entry).forEach(([r, c]) => {
      cellEntries[`${r},${c}`][entry.direction] = entry.id;
    });
  });

  const numberAt = {};
  entries.forEach(entry => { numberAt[`${entry.row},${entry.col}`] = entry.number; });

  const table = document.getElementById("crossword-grid");
  table.innerHTML = "";
  const inputAt = {};
  for (let r = 0; r < size; r++) {
    const tr = document.createElement("tr");
    for (let c = 0; c < size; c++) {
      const td = document.createElement("td");
      if (blackSet.has(`${r},${c}`)) {
        td.className = "black";
      } else {
        const num = numberAt[`${r},${c}`];
        if (num) {
          const label = document.createElement("span");
          label.className = "cell-number";
          label.textContent = num;
          td.appendChild(label);
        }
        const input = document.createElement("input");
        input.maxLength = 1;
        input.dataset.row = r;
        input.dataset.col = c;
        td.appendChild(input);
        inputAt[`${r},${c}`] = input;
      }
      tr.appendChild(td);
    }
    table.appendChild(tr);
  }

  let selectedEntryId = entries[0].id;
  let gaveUp = false;
  const stopTimer = startTimer("crossword-timer");
  const resultEl = document.getElementById("crossword-result");

  function highlight(entryId) {
    selectedEntryId = entryId;
    table.querySelectorAll("td").forEach(td => td.classList.remove("highlight"));
    entryCells(entriesById[entryId]).forEach(([r, c]) => {
      inputAt[`${r},${c}`]?.closest("td").classList.add("highlight");
    });
    document.querySelectorAll(".clue-list li").forEach(li => li.classList.remove("active"));
    document.querySelector(`.clue-list li[data-id="${entryId}"]`)?.classList.add("active");
  }

  function focusCell(r, c) {
    inputAt[`${r},${c}`]?.focus();
  }

  ["across", "down"].forEach(direction => {
    const list = document.getElementById(`clues-${direction}`);
    list.innerHTML = "";
    entries.filter(e => e.direction === direction).sort((a, b) => a.number - b.number).forEach(entry => {
      const li = document.createElement("li");
      li.dataset.id = entry.id;
      li.innerHTML = `<span class="num">${entry.number}</span>${entry.clue} (${entry.length})`;
      li.addEventListener("click", () => {
        highlight(entry.id);
        const [r, c] = entryCells(entry)[0];
        focusCell(r, c);
      });
      list.appendChild(li);
    });
  });

  Object.entries(inputAt).forEach(([key, input]) => {
    const [r, c] = key.split(",").map(Number);
    input.addEventListener("focus", () => {
      const cellDirs = cellEntries[key];
      const preferred = cellDirs[entriesById[selectedEntryId]?.direction] === selectedEntryId
        ? selectedEntryId
        : (cellDirs.across || cellDirs.down);
      if (preferred) highlight(preferred);
    });
    input.addEventListener("click", () => {
      const cellDirs = cellEntries[key];
      if (cellDirs.across && cellDirs.down) {
        const currentDir = entriesById[selectedEntryId]?.direction;
        const isAcrossSelected = cellDirs.across === selectedEntryId;
        highlight(isAcrossSelected && currentDir === "across" ? cellDirs.down : cellDirs.across);
      }
    });
    input.addEventListener("input", () => {
      input.value = input.value.replace(/[^a-zA-Z]/, "").toUpperCase();
      if (input.value) {
        const entry = entriesById[selectedEntryId];
        const cells = entryCells(entry);
        const idx = cells.findIndex(([cr, cc]) => cr === r && cc === c);
        const next = cells[idx + 1];
        if (next) focusCell(next[0], next[1]);
      }
    });
    input.addEventListener("keydown", e => {
      if (e.key === "Backspace" && !input.value) {
        const entry = entriesById[selectedEntryId];
        const cells = entryCells(entry);
        const idx = cells.findIndex(([cr, cc]) => cr === r && cc === c);
        const prev = cells[idx - 1];
        if (prev) focusCell(prev[0], prev[1]);
      }
    });
  });

  highlight(entries[0].id);

  function currentValues() {
    const grid = Array.from({ length: size }, () => Array(size).fill(null));
    Object.entries(inputAt).forEach(([key, input]) => {
      const [r, c] = key.split(",").map(Number);
      grid[r][c] = input.value || null;
    });
    return grid;
  }

  document.getElementById("crossword-check").addEventListener("click", () => {
    const current = currentValues();
    let solved = true;
    for (let r = 0; r < size; r++) {
      for (let c = 0; c < size; c++) {
        if (blackSet.has(`${r},${c}`)) continue;
        if (current[r][c] !== solution_grid[r][c]) solved = false;
      }
    }
    if (solved && gaveUp) {
      resultEl.textContent = "Correct, but revealed cells don't count toward your streak.";
      resultEl.className = "result-msg";
    } else {
      resultEl.textContent = solved ? "Solved!" : "Not solved yet (or has mistakes).";
      resultEl.className = `result-msg ${solved ? "correct" : "wrong"}`;
    }
    if (solved && !gaveUp) {
      stopTimer();
      PuzzleProgress.markComplete(date, "mini_crossword");
      refreshTabChecks(date);
      refreshStreakBanner(date);
    }
  });

  document.getElementById("crossword-hint").addEventListener("click", () => {
    const empties = Object.entries(inputAt).filter(([, input]) => !input.disabled && !input.value);
    if (empties.length === 0) return;
    const [key, input] = empties[Math.floor(Math.random() * empties.length)];
    const [r, c] = key.split(",").map(Number);
    input.value = solution_grid[r][c];
    input.disabled = true;
  });

  document.getElementById("crossword-reveal").addEventListener("click", () => {
    stopTimer();
    gaveUp = true;
    Object.entries(inputAt).forEach(([key, input]) => {
      const [r, c] = key.split(",").map(Number);
      input.value = solution_grid[r][c];
    });
    resultEl.textContent = "Solution revealed.";
    resultEl.className = "result-msg";
  });
}

function renderCryptic(crypticData, date) {
  const list = document.getElementById("cryptic-list");
  list.innerHTML = "";
  const stopTimer = startTimer("cryptic-timer");
  const revealed = new Set();

  crypticData.clues.forEach((clueObj, idx) => {
    const li = document.createElement("li");
    li.className = "cryptic-item";

    const clueText = document.createElement("div");
    clueText.className = "clue-text";
    clueText.textContent = clueObj.clue;
    li.appendChild(clueText);

    const controls = document.createElement("div");
    controls.className = "controls";
    const answerBtn = document.createElement("button");
    answerBtn.className = "action";
    answerBtn.textContent = "Reveal answer";
    const explainBtn = document.createElement("button");
    explainBtn.className = "action";
    explainBtn.textContent = "Reveal explanation";
    controls.appendChild(answerBtn);
    controls.appendChild(explainBtn);
    li.appendChild(controls);

    const box = document.createElement("div");
    box.className = "reveal-box";
    li.appendChild(box);

    function checkAllRevealed() {
      if (revealed.size === crypticData.clues.length) {
        stopTimer();
        PuzzleProgress.markComplete(date, "cryptic_clues");
        refreshTabChecks(date);
        refreshStreakBanner(date);
      }
    }

    answerBtn.addEventListener("click", () => {
      box.textContent = `Answer: ${clueObj.answer}`;
      revealed.add(idx);
      checkAllRevealed();
    });
    explainBtn.addEventListener("click", () => {
      box.textContent = clueObj.explanation;
      revealed.add(idx);
      checkAllRevealed();
    });

    list.appendChild(li);
  });
}

const MISTAKE_LIMIT = 4;

function shuffled(arr) {
  const copy = arr.slice();
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

function renderConnections(connectionsData, date) {
  const groups = connectionsData.groups;
  const wordToGroup = {};
  groups.forEach(g => g.words.forEach(w => { wordToGroup[w] = g; }));

  const grid = document.getElementById("connections-grid");
  const solvedEl = document.getElementById("connections-solved");
  const mistakesEl = document.getElementById("connections-mistakes");
  const resultEl = document.getElementById("connections-result");
  const submitBtn = document.getElementById("connections-submit");
  const deselectBtn = document.getElementById("connections-deselect");

  let words = shuffled(groups.flatMap(g => g.words));
  let selected = new Set();
  let mistakes = 0;
  let solvedCount = 0;
  let gameOver = false;
  const stopTimer = startTimer("connections-timer");

  function updateMistakes() {
    mistakesEl.textContent = `Mistakes: ${"●".repeat(mistakes)}${"○".repeat(MISTAKE_LIMIT - mistakes)}`;
  }

  function renderGrid() {
    grid.innerHTML = "";
    words.forEach(word => {
      const tile = document.createElement("button");
      tile.className = "connections-tile";
      tile.textContent = word;
      if (selected.has(word)) tile.classList.add("selected");
      tile.disabled = gameOver;
      tile.addEventListener("click", () => {
        if (selected.has(word)) {
          selected.delete(word);
        } else if (selected.size < 4) {
          selected.add(word);
        }
        renderGrid();
      });
      grid.appendChild(tile);
    });
    submitBtn.disabled = selected.size !== 4 || gameOver;
  }

  function revealSolvedGroup(group) {
    const row = document.createElement("div");
    row.className = `solved-group tier-${group.tier}`;
    row.innerHTML = `<div class="cat-name">${group.category}</div><div class="cat-words">${group.words.join(", ")}</div>`;
    solvedEl.appendChild(row);
  }

  function endGame(won) {
    gameOver = true;
    stopTimer();
    if (won) {
      resultEl.textContent = "Solved!";
      resultEl.className = "result-msg correct";
      PuzzleProgress.markComplete(date, "connections");
      refreshTabChecks(date);
      refreshStreakBanner(date);
    } else {
      groups.forEach(g => { if (words.some(w => g.words.includes(w))) revealSolvedGroup(g); });
      words = [];
      resultEl.textContent = "Out of guesses — here are the categories.";
      resultEl.className = "result-msg wrong";
    }
    renderGrid();
  }

  submitBtn.addEventListener("click", () => {
    if (selected.size !== 4) return;
    const selectedWords = Array.from(selected);
    const group = groups.find(g => selectedWords.every(w => g.words.includes(w)) && g.words.length === 4
      && selectedWords.length === g.words.length);
    if (group) {
      revealSolvedGroup(group);
      words = words.filter(w => !group.words.includes(w));
      selected.clear();
      solvedCount++;
      resultEl.textContent = "";
      resultEl.className = "result-msg";
      if (solvedCount === groups.length) {
        endGame(true);
        return;
      }
      renderGrid();
    } else {
      mistakes++;
      updateMistakes();
      selected.clear();
      if (mistakes >= MISTAKE_LIMIT) {
        endGame(false);
        return;
      }
      resultEl.textContent = "Not quite — try again.";
      resultEl.className = "result-msg wrong";
      renderGrid();
    }
  });

  deselectBtn.addEventListener("click", () => {
    selected.clear();
    renderGrid();
  });

  updateMistakes();
  renderGrid();
}

initTheme();
initTabs();

loadBundle().then(bundle => {
  renderSudoku(bundle.sudoku, bundle.date);
  if (bundle.mini_crossword) renderCrossword(bundle.mini_crossword, bundle.date);
  if (bundle.cryptic_clues) renderCryptic(bundle.cryptic_clues, bundle.date);
  if (bundle.connections) renderConnections(bundle.connections, bundle.date);
  refreshTabChecks(bundle.date);
  refreshStreakBanner(bundle.date);
});
