// Progress + streak tracking, backed by localStorage. Single-user, no backend.
const PuzzleProgress = (() => {
  const STORAGE_KEY = "puzzleFreaks:progress";
  const PUZZLE_TYPES = ["sudoku", "mini_crossword", "cryptic_clues", "connections"];

  function readAll() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {};
    } catch {
      return {};
    }
  }

  function writeAll(data) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  }

  function markComplete(date, type) {
    const all = readAll();
    all[date] = all[date] || {};
    all[date][type] = true;
    writeAll(all);
  }

  function isComplete(date, type) {
    const all = readAll();
    return !!(all[date] && all[date][type]);
  }

  function getDayProgress(date) {
    const all = readAll();
    const day = all[date] || {};
    return Object.fromEntries(PUZZLE_TYPES.map(t => [t, !!day[t]]));
  }

  function isDayFullyComplete(date) {
    const progress = getDayProgress(date);
    return PUZZLE_TYPES.every(t => progress[t]);
  }

  function fmt(d) {
    return d.toISOString().slice(0, 10);
  }

  function getStreak(todayStr) {
    let cursor = new Date(`${todayStr}T00:00:00`);
    if (!isDayFullyComplete(todayStr)) {
      cursor.setDate(cursor.getDate() - 1);
    }
    let count = 0;
    while (isDayFullyComplete(fmt(cursor))) {
      count++;
      cursor.setDate(cursor.getDate() - 1);
    }
    return count;
  }

  return { PUZZLE_TYPES, markComplete, isComplete, getDayProgress, isDayFullyComplete, getStreak };
})();
