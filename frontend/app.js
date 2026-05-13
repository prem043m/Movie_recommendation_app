/* ─────────────────────────────────────────────────────────────
   CineMatch — app.js
   Talks to the FastAPI backend on Render.
   Set API_BASE to your Render URL before deploying.
   ───────────────────────────────────────────────────────────── */

// ── Configuration ───────────────────────────────────────────
// Auto-detect: local dev uses localhost:8000, production uses Render URL.
// Override by setting window.API_BASE before this script loads.
const _isLocal = location.hostname === "localhost" || location.hostname === "127.0.0.1";
const API_BASE = window.API_BASE || (_isLocal
  ? "http://127.0.0.1:8000"
  : "https://movie-recommender-api.onrender.com");

const COLD_START_MS     = 60_000;   // Render free tier can take ~60 s
const DEBOUNCE_MS       = 260;
const SUGGESTIONS_LIMIT = 12;
const POPULAR_COUNT     = 30;       // titles shown in browse grid

// ── State ────────────────────────────────────────────────────
let allTitles   = [];     // full title list from /movies
let selectedMovie = null; // { title, seed, ... }
let debounceTimer = null;

// ── DOM refs ─────────────────────────────────────────────────
const $searchInput   = document.getElementById("search-input");
const $searchClear   = document.getElementById("search-clear");
const $suggestions   = document.getElementById("suggestions");
const $coldNotice    = document.getElementById("cold-notice");
const $statusDot     = document.getElementById("status-dot");
const $statusLabel   = document.getElementById("status-label");
const $navbar        = document.getElementById("navbar");
const $seedSection   = document.getElementById("seed-section");
const $seedCard      = document.getElementById("seed-card");
const $recsSection   = document.getElementById("recs-section");
const $recsGrid      = document.getElementById("recs-grid");
const $recsCount     = document.getElementById("recs-count");
const $popularSection= document.getElementById("popular-section");
const $popularGrid   = document.getElementById("popular-grid");
const $modalOverlay  = document.getElementById("modal-overlay");
const $modalBody     = document.getElementById("modal-body");
const $modalClose    = document.getElementById("modal-close");
const $toast         = document.getElementById("toast");
const $typewriter    = document.getElementById("typewriter");

// ── Typewriter ────────────────────────────────────────────────
const phrases = ["Favourite Film", "Next Adventure", "Cinematic Escape", "Hidden Gem"];
let phraseIdx = 0, charIdx = 0, deleting = false;

function typeLoop() {
  const phrase = phrases[phraseIdx];
  if (!deleting) {
    $typewriter.textContent = phrase.slice(0, ++charIdx);
    if (charIdx === phrase.length) {
      deleting = true;
      setTimeout(typeLoop, 2000);
      return;
    }
  } else {
    $typewriter.textContent = phrase.slice(0, --charIdx);
    if (charIdx === 0) {
      deleting = false;
      phraseIdx = (phraseIdx + 1) % phrases.length;
    }
  }
  setTimeout(typeLoop, deleting ? 55 : 90);
}
typeLoop();

// ── Navbar scroll shadow ──────────────────────────────────────
window.addEventListener("scroll", () => {
  $navbar.classList.toggle("scrolled", window.scrollY > 40);
}, { passive: true });

// ── API helpers ───────────────────────────────────────────────
function setStatus(state) {
  $statusDot.className = "status-dot " + state;
  if (state === "loading") $statusLabel.textContent = "Loading…";
  if (state === "online")  $statusLabel.textContent = "API online";
  if (state === "offline") $statusLabel.textContent = "API offline";
}

async function apiFetch(path, options = {}, timeoutMs = COLD_START_MS) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(API_BASE + path, {
      ...options,
      signal: controller.signal,
      headers: { "Content-Type": "application/json", ...options.headers },
    });
    clearTimeout(timer);
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `HTTP ${res.status}`);
    }
    return await res.json();
  } catch (err) {
    clearTimeout(timer);
    throw err;
  }
}

// ── Bootstrap: load movie list & health check ─────────────────
async function init() {
  setStatus("loading");
  showSkeletons($popularGrid, POPULAR_COUNT);

  // Show cold-start notice after 3 s if still loading
  const coldTimer = setTimeout(() => $coldNotice.classList.add("visible"), 3000);

  try {
    const titles = await apiFetch(`/movies?limit=500`);
    clearTimeout(coldTimer);
    $coldNotice.classList.remove("visible");
    allTitles = titles;
    setStatus("online");

    // Render first N as browse cards (no posters yet — lazy loaded)
    renderBrowseGrid(titles.slice(0, POPULAR_COUNT));
  } catch (err) {
    clearTimeout(coldTimer);
    $coldNotice.classList.remove("visible");
    setStatus("offline");
    showToast("⚠️ Could not reach the API. " + err.message);
    $popularGrid.innerHTML = `<p style="color:var(--text-400);grid-column:1/-1">
      Could not load movies. Is the Render service running?</p>`;
  }
}

// ── Browse grid ───────────────────────────────────────────────
function renderBrowseGrid(titles) {
  $popularGrid.innerHTML = "";
  titles.forEach((title, i) => {
    const card = createTitleCard(title, i);
    $popularGrid.appendChild(card);
  });
}

function createTitleCard(title, idx) {
  const card = document.createElement("div");
  card.className = "movie-card";
  card.style.animationDelay = `${Math.min(idx, 15) * 0.04}s`;
  card.innerHTML = `
    <div class="card-poster-placeholder" id="ph-${slugify(title)}">
      <span class="poster-emoji">🎬</span>
      <span>${escHtml(title)}</span>
    </div>
    <div class="card-overlay"><span class="card-overlay-cta">View Details →</span></div>
    <div class="card-info">
      <p class="card-title">${escHtml(title)}</p>
    </div>
  `;
  card.addEventListener("click", () => selectMovieByTitle(title));
  return card;
}

// ── Search & Suggestions ──────────────────────────────────────
$searchInput.addEventListener("input", () => {
  const q = $searchInput.value.trim();
  $searchClear.classList.toggle("visible", q.length > 0);
  clearTimeout(debounceTimer);
  if (!q) { closeSuggestions(); return; }
  debounceTimer = setTimeout(() => showSuggestions(q), DEBOUNCE_MS);
});

$searchClear.addEventListener("click", () => {
  $searchInput.value = "";
  $searchClear.classList.remove("visible");
  closeSuggestions();
  $searchInput.focus();
});

document.addEventListener("click", (e) => {
  if (!e.target.closest("#search-wrap")) closeSuggestions();
});

function showSuggestions(q) {
  const lower = q.toLowerCase();
  const filtered = allTitles
    .filter(t => t.toLowerCase().includes(lower))
    .slice(0, SUGGESTIONS_LIMIT);

  if (!filtered.length) { closeSuggestions(); return; }

  $suggestions.innerHTML = "";
  filtered.forEach(title => {
    const li = document.createElement("li");
    li.className = "suggestion-item";
    li.setAttribute("role", "option");
    // Highlight matching characters
    const highlighted = escHtml(title).replace(
      new RegExp(escRegex(q), "gi"),
      m => `<strong>${m}</strong>`
    );
    li.innerHTML = highlighted;
    li.addEventListener("click", () => selectMovieByTitle(title));
    $suggestions.appendChild(li);
  });

  $suggestions.classList.add("open");
}

function closeSuggestions() { $suggestions.classList.remove("open"); $suggestions.innerHTML = ""; }

// ── Select movie ──────────────────────────────────────────────
async function selectMovieByTitle(title) {
  closeSuggestions();
  $searchInput.value = title;
  $searchClear.classList.add("visible");

  // Show seed skeleton
  $seedSection.hidden = false;
  $recsSection.hidden = true;
  $popularSection.hidden = true;
  $seedCard.innerHTML = buildSeedSkeleton();

  window.scrollTo({ top: $seedSection.offsetTop - 80, behavior: "smooth" });

  try {
    // Show cold-start notice if it takes time
    const coldTimer = setTimeout(() => $coldNotice.classList.add("visible"), 4000);

    const data = await apiFetch("/recommend", {
      method: "POST",
      body: JSON.stringify({ title, n: 10 }),
    });

    clearTimeout(coldTimer);
    $coldNotice.classList.remove("visible");

    selectedMovie = data;
    renderSeedCard(data.seed);
    renderRecsGrid(data.results);

  } catch (err) {
    $coldNotice.classList.remove("visible");
    $seedCard.innerHTML = `<p style="color:var(--text-400);padding:var(--sp-xl)">
      ❌ ${err.message}</p>`;
    showToast("Could not load recommendations — " + err.message);
  }
}

// ── Seed card ─────────────────────────────────────────────────
function renderSeedCard(seed) {
  const year      = seed.release_date ? seed.release_date.slice(0, 4) : "—";
  const genres    = Array.isArray(seed.genres) ? seed.genres : [];
  const cast      = Array.isArray(seed.cast)   ? seed.cast   : [];
  const runtime   = seed.runtime ? `${seed.runtime} min` : "—";
  const lang      = seed.original_language ? seed.original_language.toUpperCase() : "—";
  const rating    = seed.vote_average ? seed.vote_average.toFixed(1) : "—";

  $seedCard.innerHTML = `
    <div id="seed-poster-wrap">
      <div class="seed-poster-placeholder"><span style="font-size:2.5rem">🎬</span></div>
    </div>
    <div class="seed-info">
      <h3 class="seed-title">${escHtml(seed.title)}</h3>
      <div class="seed-badges">
        ${genres.map(g => `<span class="badge badge-genre">${escHtml(g)}</span>`).join("")}
        ${lang !== "—" ? `<span class="badge badge-lang">${lang}</span>` : ""}
      </div>
      <div class="seed-stats">
        <div class="stat"><span class="stat-value">⭐ ${rating}</span><span class="stat-label">Rating</span></div>
        <div class="stat"><span class="stat-value">${year}</span><span class="stat-label">Year</span></div>
        <div class="stat"><span class="stat-value">${runtime}</span><span class="stat-label">Runtime</span></div>
      </div>
      ${seed.overview ? `<p class="seed-overview">${escHtml(seed.overview.slice(0, 320))}${seed.overview.length > 320 ? "…" : ""}</p>` : ""}
      ${cast.length ? `<p class="seed-cast"><strong>Cast:</strong> ${cast.map(escHtml).join(", ")}</p>` : ""}
      ${seed.crew ? `<p class="seed-cast"><strong>Director:</strong> ${escHtml(seed.crew)}</p>` : ""}
      <button class="rec-btn" id="get-recs-btn">🎯 Get 10 Recommendations</button>
    </div>
  `;

  // Fetch poster
  if (seed.movie_id) fetchAndSetPoster(seed.movie_id, "seed-poster-wrap", "seed-poster");

  document.getElementById("get-recs-btn").addEventListener("click", () => {
    window.scrollTo({ top: $recsSection.offsetTop - 80, behavior: "smooth" });
  });
}

function buildSeedSkeleton() {
  return `
    <div class="skeleton" style="width:180px;aspect-ratio:2/3;border-radius:12px;flex-shrink:0"></div>
    <div style="display:flex;flex-direction:column;gap:16px;flex:1">
      <div class="skeleton" style="height:2rem;width:60%;border-radius:8px"></div>
      <div class="skeleton" style="height:1rem;width:40%;border-radius:8px"></div>
      <div class="skeleton" style="height:1rem;width:90%;border-radius:8px"></div>
      <div class="skeleton" style="height:1rem;width:80%;border-radius:8px"></div>
      <div class="skeleton" style="height:1rem;width:70%;border-radius:8px"></div>
    </div>
  `;
}

// ── Recs grid ─────────────────────────────────────────────────
function renderRecsGrid(results) {
  $recsSection.hidden = false;
  $recsCount.textContent = `${results.length} picks`;
  $recsGrid.innerHTML = "";

  results.forEach((movie, i) => {
    const card = createMovieCard(movie, i);
    $recsGrid.appendChild(card);
  });

  window.scrollTo({ top: $recsSection.offsetTop - 80, behavior: "smooth" });
}

function createMovieCard(movie, idx) {
  const year   = movie.release_date ? movie.release_date.slice(0, 4) : "";
  const rating = movie.vote_average ? movie.vote_average.toFixed(1)  : "—";
  const cardId = `mc-${idx}-${slugify(movie.title)}`;

  const card = document.createElement("div");
  card.className = "movie-card";
  card.id = cardId;
  card.innerHTML = `
    <div id="poster-wrap-${idx}">
      <div class="card-poster-placeholder">
        <span class="poster-emoji">🎬</span>
        <span>${escHtml(movie.title)}</span>
      </div>
    </div>
    <div class="card-overlay"><span class="card-overlay-cta">More info →</span></div>
    <div class="card-info">
      <p class="card-title">${escHtml(movie.title)}</p>
      <div class="card-meta">
        <span class="card-rating">⭐ ${rating}</span>
        ${year ? `<span>${year}</span>` : ""}
      </div>
    </div>
  `;
  card.addEventListener("click", () => openModal(movie));

  // Lazy-fetch poster
  if (movie.movie_id) {
    fetchAndSetPoster(movie.movie_id, `poster-wrap-${idx}`, `poster-img-${idx}`);
  }

  return card;
}

// ── Poster fetching ───────────────────────────────────────────
async function fetchAndSetPoster(movieId, wrapId, imgId) {
  try {
    const data = await apiFetch(`/poster/${movieId}`, {}, 8000);
    const wrap = document.getElementById(wrapId);
    if (!wrap) return;
    if (imgId === "seed-poster") {
      wrap.innerHTML = `<img src="${data.poster_url}" class="seed-poster" alt="poster" loading="lazy" />`;
    } else {
      wrap.innerHTML = `<img src="${data.poster_url}" class="card-poster" alt="poster" loading="lazy" id="${imgId}" />`;
    }
  } catch {
    // placeholder already shown — silently skip
  }
}

// ── Modal ─────────────────────────────────────────────────────
function openModal(movie) {
  const year    = movie.release_date ? movie.release_date.slice(0, 4) : "";
  const genres  = Array.isArray(movie.genres) ? movie.genres : [];
  const cast    = Array.isArray(movie.cast)   ? movie.cast   : [];
  const rating  = movie.vote_average ? `⭐ ${movie.vote_average.toFixed(1)}/10` : "";
  const runtime = movie.runtime ? `${movie.runtime} min` : "";
  const lang    = movie.original_language ? movie.original_language.toUpperCase() : "";

  $modalBody.innerHTML = `
    <div id="modal-poster-wrap">
      <div class="modal-poster-placeholder">🎬</div>
    </div>
    <h2 class="modal-title" id="modal-title">${escHtml(movie.title)}</h2>
    <div class="modal-meta">
      ${rating   ? `<span>${rating}</span>`   : ""}
      ${year     ? `<span>📅 ${year}</span>`  : ""}
      ${runtime  ? `<span>⏱ ${runtime}</span>`: ""}
      ${lang     ? `<span>🌍 ${lang}</span>`  : ""}
      ${movie.director ? `<span>🎬 ${escHtml(movie.director)}</span>` : ""}
    </div>
    ${movie.overview ? `<p class="modal-overview">${escHtml(movie.overview)}</p>` : ""}
    ${genres.length ? `
      <p class="modal-section-label">Genres</p>
      <div class="modal-badge-row">
        ${genres.map(g => `<span class="badge badge-genre">${escHtml(g)}</span>`).join("")}
      </div>` : ""}
    ${cast.length ? `
      <p class="modal-section-label">Cast</p>
      <div class="modal-badge-row">
        ${cast.map(c => `<span class="badge badge-lang">${escHtml(c)}</span>`).join("")}
      </div>` : ""}
    <button class="rec-btn" id="modal-find-similar" style="width:100%;justify-content:center;text-align:center;margin-top:8px">
      🔍 Find Similar Movies
    </button>
  `;

  if (movie.movie_id) fetchAndSetModalPoster(movie.movie_id);

  document.getElementById("modal-find-similar").addEventListener("click", () => {
    closeModal();
    selectMovieByTitle(movie.title);
  });

  $modalOverlay.hidden = false;
  document.body.style.overflow = "hidden";
}

async function fetchAndSetModalPoster(movieId) {
  try {
    const data = await apiFetch(`/poster/${movieId}`, {}, 8000);
    const wrap = document.getElementById("modal-poster-wrap");
    if (wrap) {
      wrap.innerHTML = `<img src="${data.poster_url}" class="modal-poster" alt="poster" loading="lazy" />`;
    }
  } catch { /* placeholder stays */ }
}

function closeModal() {
  $modalOverlay.hidden = true;
  document.body.style.overflow = "";
}

$modalClose.addEventListener("click", closeModal);
$modalOverlay.addEventListener("click", e => { if (e.target === $modalOverlay) closeModal(); });
document.addEventListener("keydown", e => { if (e.key === "Escape") closeModal(); });

// ── Skeleton loaders ──────────────────────────────────────────
function showSkeletons(container, count) {
  container.innerHTML = "";
  for (let i = 0; i < count; i++) {
    const s = document.createElement("div");
    s.className = "skeleton skeleton-card";
    container.appendChild(s);
  }
}

// ── Toast ─────────────────────────────────────────────────────
let toastTimer = null;
function showToast(msg) {
  $toast.textContent = msg;
  $toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => $toast.classList.remove("show"), 4000);
}

// ── Utilities ─────────────────────────────────────────────────
function escHtml(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
function escRegex(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
function slugify(str) {
  return str.toLowerCase().replace(/[^a-z0-9]+/g, "-");
}

// ── Boot ──────────────────────────────────────────────────────
init();
