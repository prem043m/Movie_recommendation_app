/**
 * Lumina App - Cinematic Frontend Logic
 */

const API_BASE = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    ? "http://127.0.0.1:8000"
    : "https://movie-recommendation-app-78qp.onrender.com"; // User's Render URL

const TMDB_IMG = "https://image.tmdb.org/t/p/w500";

// --- State Management ---
let currentUserRole = localStorage.getItem('user_role') || 'guest';
let previewsEnabled = localStorage.getItem('previews_enabled') !== 'false';
let hoverTimer = null;

// --- DOM Elements ---
const authBtn = document.getElementById('auth-btn');
const movieInput = document.getElementById('movie-input');
const searchBtn = document.getElementById('search-btn');
const resultsSection = document.getElementById('results-section');
const resultsGrid = document.getElementById('results-grid');
const trendingGrid = document.getElementById('trending-grid');
const searchPath = document.getElementById('search-path');
const heroTitle = document.getElementById('hero-title');
const heroDesc = document.getElementById('hero-desc');
const heroBackdrop = document.querySelector('#hero-backdrop img');
const kbModal = document.getElementById('kb-modal');
const kbHint = document.getElementById('kb-hint');
const closeKb = document.getElementById('close-kb');
const settingsBtn = document.getElementById('settings-btn');
const settingsMenu = document.getElementById('settings-menu');
const previewToggle = document.getElementById('preview-toggle');

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    fetchTrending();
    
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

    // Auth Simulation
    updateAuthUI();
    authBtn.addEventListener('click', () => {
        currentUserRole = (currentUserRole === 'guest') ? 'member' : 'guest';
        localStorage.setItem('user_role', currentUserRole);
        updateAuthUI();
        performSearch(); // Refresh search with new permissions
    });
});

function updateAuthUI() {
    authBtn.textContent = (currentUserRole === 'member') ? 'Sign Out' : 'Sign In';
    authBtn.style.borderColor = (currentUserRole === 'member') ? 'var(--cyan)' : 'var(--glass-border)';
}

// --- API Calls ---
async function performSearch() {
    const title = movieInput.value.trim();
    if (!title) return;

    searchBtn.textContent = "...";
    searchBtn.disabled = true;

    try {
        const response = await fetch(`${API_BASE}/recommend`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-User-Role': currentUserRole
            },
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
    } catch (err) {
        console.error("Failed to fetch trending:", err);
    }
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
        
        const posterUrl = movie.poster_path 
            ? `${TMDB_IMG}${movie.poster_path}`
            : `https://via.placeholder.com/500x750/1A1A1A/FFFFFF?text=${encodeURIComponent(movie.title)}`;

        const blurStyle = movie.is_restricted ? 'filter: blur(4px); user-select: none;' : '';

        card.innerHTML = `
            ${movie.is_restricted ? '<span class="preview-tag" style="color: #FF6B6B; border-color: #FF6B6B;">RESTRICTED</span>' : ''}
            <div class="video-container"></div>
            <img src="${posterUrl}" alt="${movie.title}" loading="lazy">
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
            if (!movie.preview_url || movie.is_restricted || !previewsEnabled) return;
            
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
    heroTitle.textContent = movie.title;
    
    if (movie.is_restricted) {
        heroDesc.innerHTML = `<span style="color: #FF6B6B; font-weight: 600;">[Member Only Content]</span><br><span style="filter: blur(5px); opacity: 0.5;">${movie.overview}</span>`;
    } else {
        heroDesc.textContent = movie.overview || "No overview available for this title.";
    }
    
    if (movie.poster_path) {
        // In a real app, we'd use a backdrop path, but poster is a good fallback
        heroBackdrop.src = `${TMDB_IMG}${movie.poster_path}`;
        heroBackdrop.style.opacity = "0.4";
    }
}
