/**
 * Lumina App - Cinematic Frontend Logic
 */

const API_BASE = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    ? "http://127.0.0.1:8000"
    : "https://movie-recommendation-app-78qp.onrender.com"; // User's Render URL

const TMDB_IMG = "https://image.tmdb.org/t/p/w500";

const LOCAL_FALLBACK = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='500' height='750' viewBox='0 0 500 750'%3E%3Crect width='500' height='750' fill='%231A1A1A'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' font-family='Outfit, sans-serif' font-size='24' fill='%236E7DFF'%3EPOSTER UNAVAILABLE%3C/text%3E%3C/svg%3E";

// --- State Management ---
let previewsEnabled = localStorage.getItem('previews_enabled') !== 'false';
let hoverTimer = null;
let currentHero = null;

// --- DOM Elements ---
const movieInput = document.getElementById('movie-input');
const searchBtn = document.getElementById('search-btn');
const resultsSection = document.getElementById('results-section');
const resultsGrid = document.getElementById('results-grid');
const trendingGrid = document.getElementById('trending-grid');
const searchPath = document.getElementById('search-path');
const heroTitle = document.getElementById('hero-title');
const heroDesc = document.getElementById('hero-desc');
const heroBackdrop = document.querySelector('#hero-backdrop img');
const playerModal = document.getElementById('player-modal');
const playerIframe = document.getElementById('player-iframe');
const playerClose = document.getElementById('player-close');
const kbModal = document.getElementById('kb-modal');
const kbHint = document.getElementById('kb-hint');
const closeKb = document.getElementById('close-kb');
const settingsBtn = document.getElementById('settings-btn');
const settingsMenu = document.getElementById('settings-menu');
const previewToggle = document.getElementById('preview-toggle');
const healthBanner = document.getElementById('health-banner');

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    fetchTrending();
    
    // Global Error Monitor
    window.addEventListener('error', (e) => {
        if (e.target.tagName !== 'IMG') {
            showHealthWarning("System connectivity issue detected.");
        }
    }, true);
    
    searchBtn.addEventListener('click', performSearch);
    movieInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') performSearch();
    });

    // Keyboard Shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.key === '/' && document.activeElement !== movieInput) {
            e.preventDefault();
            movieInput.focus();
        }
        if (e.key === 'Escape') {
            resultsSection.style.display = 'none';
            kbModal.style.display = 'none';
        }
    });

    kbHint.addEventListener('click', () => kbModal.style.display = 'flex');
    closeKb.addEventListener('click', () => kbModal.style.display = 'none');
    kbModal.style.display = 'none'; // Ensure hidden initially

    // Settings logic
    previewToggle.checked = previewsEnabled;
    settingsBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        settingsMenu.style.display = settingsMenu.style.display === 'none' ? 'block' : 'none';
    });
    previewToggle.addEventListener('change', () => {
        previewsEnabled = previewToggle.checked;
        localStorage.setItem('previews_enabled', previewsEnabled);
    });
    document.addEventListener('click', () => settingsMenu.style.display = 'none');
    settingsMenu.addEventListener('click', (e) => e.stopPropagation());

    // --- Hero Button Handlers ---
    const heroPrimary = document.getElementById('hero-primary');
    const heroSecondary = document.getElementById('hero-secondary');
    if (heroPrimary) {
        heroPrimary.addEventListener('click', () => {
            // Try to play a preview if available, otherwise fallback
            if (currentHero && currentHero.preview_url) {
                openPlayer(currentHero.preview_url);
                return;
            }
            if (resultsSection.style.display !== 'none') {
                resultsSection.scrollIntoView({ behavior: 'smooth' });
            } else {
                movieInput.focus();
            }
        });
    }
    if (heroSecondary) {
        heroSecondary.addEventListener('click', () => {
            const trendingSection = document.getElementById('trending');
            if (trendingSection) {
                trendingSection.scrollIntoView({ behavior: 'smooth' });
            }
        });
    }

    // --- Quick Picks Handler ---
    const quickPicks = document.querySelectorAll('.pick-chip');
    quickPicks.forEach(chip => {
        chip.addEventListener('click', () => {
            const title = chip.getAttribute('data-title');
            if (title) {
                movieInput.value = title;
                performSearch();
            }
        });
    });

    // --- Navigation Links ---
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            const href = link.getAttribute('href');
            if (href.startsWith('#')) {
                e.preventDefault();
                const section = document.querySelector(href);
                if (section) {
                    // Remove active state from all links
                    navLinks.forEach(l => l.classList.remove('is-active'));
                    // Add active state to clicked link
                    link.classList.add('is-active');
                    // Scroll to section
                    section.scrollIntoView({ behavior: 'smooth' });
                }
            }
        });
    });

    // --- Update Active Nav Link on Scroll ---
    window.addEventListener('scroll', () => {
        const sections = document.querySelectorAll('section[id]');
        let current = '';
        
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            if (pageYOffset >= sectionTop - 200) {
                current = section.getAttribute('id');
            }
        });

        navLinks.forEach(link => {
            link.classList.remove('is-active');
            if (link.getAttribute('href') === '#' + current) {
                link.classList.add('is-active');
            }
        });
    });

});

function showHealthWarning(msg) {
    if (!healthBanner) return;
    healthBanner.textContent = msg;
    healthBanner.style.display = 'block';
    setTimeout(() => healthBanner.style.display = 'none', 5000);
}

// Player modal helpers
function openPlayer(url) {
    if (!playerModal || !playerIframe) {
        window.open(url, '_blank');
        return;
    }
    playerIframe.src = url;
    playerModal.classList.add('is-open');
    playerModal.setAttribute('aria-hidden', 'false');
}

function closePlayer() {
    if (!playerModal || !playerIframe) return;
    playerModal.classList.remove('is-open');
    playerModal.setAttribute('aria-hidden', 'true');
    // stop playback by clearing src after a slight delay
    setTimeout(() => { playerIframe.src = ''; }, 200);
}

if (playerClose) playerClose.addEventListener('click', closePlayer);
if (playerModal) playerModal.addEventListener('click', (e) => {
    if (e.target === playerModal) closePlayer();
});

// --- API Calls ---
async function performSearch() {
    const title = movieInput.value.trim();
    if (!title) return;

    searchBtn.textContent = "...";
    searchBtn.disabled = true;

    try {
        const response = await fetch(`${API_BASE}/recommend`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, n: 10 })
        });
        
        const data = await response.json();
        renderResults(data);
    } catch (error) {
        console.error("Search failed:", error);
        alert("Discovery failed. Please try again later.");
    } finally {
        searchBtn.textContent = "Find";
        searchBtn.disabled = false;
    }
}

async function fetchTrending() {
    // For MVP, we'll just show some high-rated movies from the API or a static set
    // Actually, we can use the /movies endpoint to get some titles and pick a few
    try {
        const response = await fetch(`${API_BASE}/movies?limit=10`);
        const titles = await response.json();
        
        // Fetch recommendations for the first trending title to populate the grid
        const recResponse = await fetch(`${API_BASE}/recommend`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: titles[0], n: 10 })
        });
        const data = await recResponse.json();
        renderGrid(trendingGrid, data.recommendations);
            // Build mosaic from the recommendations (use first 12 posters)
            try {
                const tiles = (data.recommendations || []).slice(0, 12);
                buildMosaic(tiles);
            } catch (e) {
                console.warn('Mosaic build failed', e);
            }
    } catch (err) {
        console.error("Failed to fetch trending:", err);
    }
}

// Build poster mosaic in the hero backdrop
function buildMosaic(movies) {
    const container = document.getElementById('hero-backdrop');
    if (!container) return;
    container.innerHTML = '';
    if (!movies || movies.length === 0) {
        // keep fallback
        const img = document.createElement('img');
        img.className = 'mosaic-fallback';
        img.src = 'https://images.unsplash.com/photo-1626814026160-2237a95fc5a0?q=80&w=2070&auto=format&fit=crop';
        container.appendChild(img);
        return;
    }

    // Build a larger set of tiles (repeat some posters) to fill the mosaic
    const tiles = [];
    for (let i = 0; i < Math.max(12, movies.length); i++) {
        tiles.push(movies[i % movies.length]);
    }

    tiles.forEach((m, idx) => {
        const tile = document.createElement('div');
        tile.className = 'mosaic-tile';
        const path = (m && (m.poster_path || m.backdrop_path)) || '';
        tile.style.backgroundImage = path ? `url(${TMDB_IMG}${path})` : `url('${LOCAL_FALLBACK}')`;

        // Randomized spans for more organic collage
        const rnd = idx % 11;
        if (rnd === 0 || rnd === 4) tile.style.gridRow = 'span 2';
        if (rnd === 2 || rnd === 7) tile.style.gridColumn = 'span 2';
        if (rnd === 10) { tile.style.gridColumn = 'span 3'; tile.style.gridRow = 'span 2'; }

        // slight rotation/offset for realism on larger tiles
        if (tile.style.gridColumn && tile.style.gridColumn !== 'span 1') {
            tile.style.transform = 'rotate(-0.6deg)';
        }

        container.appendChild(tile);
    });
}

// --- Rendering ---
function renderResults(data) {
    if (!data.recommendations || data.recommendations.length === 0) {
        alert("No movies found matching that title.");
        return;
    }

    resultsSection.style.display = 'block';
    searchPath.textContent = `Via ${data.path.toUpperCase()} Engine`;
    renderGrid(resultsGrid, data.recommendations);
    
    // Update Hero with the first result for immersion
    updateHero(data.recommendations[0]);
    
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

function renderGrid(grid, movies) {
    grid.innerHTML = '';
    movies.forEach(movie => {
        const card = document.createElement('div');
        card.className = 'movie-card';
        
        const posterUrl = movie.id 
            ? `${API_BASE}/poster/${movie.id}`
            : LOCAL_FALLBACK;

        card.innerHTML = `
            <div class="video-container"></div>
            <img src="${posterUrl}" 
                 alt="${movie.title}" 
                 loading="lazy" 
                 onerror="this.onerror=null; this.src='${LOCAL_FALLBACK}';">
            <div class="card-info">
                <h3 class="card-title">${movie.title}</h3>
                <div class="card-meta">
                    <span>${movie.year || 'N/A'}</span>
                    <span>⭐ ${movie.vote_average > 0 ? movie.vote_average.toFixed(1) : '—'}</span>
                </div>
            </div>
        `;
        
        // --- Hover Logic (Milestone 2 & 3) ---
        card.onmouseenter = () => {
            if (!movie.preview_url || !previewsEnabled) return;
            
            // Intersection Check: only preview if mostly visible
            const observer = new IntersectionObserver((entries) => {
                if (entries[0].intersectionRatio < 0.8) {
                    clearTimeout(hoverTimer);
                    return;
                }
                
                hoverTimer = setTimeout(() => {
                    const container = card.querySelector('.video-container');
                    container.innerHTML = `<iframe src="${movie.preview_url}" allow="autoplay; encrypted-media"></iframe>`;
                    container.classList.add('active');
                    card.querySelector('img').style.opacity = '0.1';
                }, 500);
            }, { threshold: 0.8 });
            
            observer.observe(card);
            card._observer = observer; // Store for cleanup
        };

        card.onmouseleave = () => {
            clearTimeout(hoverTimer);
            if (card._observer) {
                card._observer.disconnect();
                card._observer = null;
            }
            const container = card.querySelector('.video-container');
            container.classList.remove('active');
            container.innerHTML = ''; 
            card.querySelector('img').style.opacity = '1';
        };

        card.onclick = () => updateHero(movie);
        grid.appendChild(card);
    });
}

function updateHero(movie) {
    currentHero = movie;
    heroTitle.textContent = movie.title;
    heroDesc.textContent = movie.overview || "No overview available for this title.";
    
    if (movie.poster_path) {
        heroBackdrop.src = `${TMDB_IMG}${movie.poster_path}`;
        heroBackdrop.style.opacity = "0.4";
    }
}
