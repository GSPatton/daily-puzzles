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

function formatDateline(dateStr) {
  const d = new Date(`${dateStr}T00:00:00`);
  return d.toLocaleDateString(undefined, { weekday: "short", year: "numeric", month: "short", day: "numeric" });
}

initTheme();

fetch("../data/puzzles/manifest.json").then(r => r.json()).then(manifest => {
  const list = document.getElementById("archive-list");
  const dates = manifest.slice().sort().reverse();
  if (dates.length === 0) {
    list.innerHTML = '<li class="placeholder">No puzzles generated yet.</li>';
    return;
  }
  dates.forEach(date => {
    const li = document.createElement("li");
    li.className = "archive-row";
    const progress = PuzzleProgress.getDayProgress(date);
    const solved = PuzzleProgress.isDayFullyComplete(date);
    li.innerHTML = `
      <a href="index.html?date=${date}">${formatDateline(date)}</a>
      <span class="archive-badges">
        ${["sudoku", "mini_crossword", "cryptic_clues", "connections"].map(t =>
          `<span class="badge ${progress[t] ? "done" : ""}"></span>`).join("")}
        ${solved ? '<span class="archive-solved">Solved</span>' : ""}
      </span>`;
    list.appendChild(li);
  });
});
