/**
 * Lumina App - Cinematic Frontend Logic
 */

const API_BASE = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    ? "http://127.0.0.1:8000"
    : "https://movie-recommendation-app-78qp.onrender.com"; // User's Render URL

const TMDB_IMG = "https://image.tmdb.org/t/p/w500";

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
const kbModal = document.getElementById('kb-modal');
const kbHint = document.getElementById('kb-hint');
const closeKb = document.getElementById('close-kb');

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

        card.innerHTML = `
            <img src="${posterUrl}" alt="${movie.title}" loading="lazy">
            <div class="card-info">
                <h3 class="card-title">${movie.title}</h3>
                <div class="card-meta">
                    <span>${movie.release_date.slice(0, 4) || 'N/A'}</span>
                    <span>⭐ ${movie.vote_average.toFixed(1)}</span>
                </div>
            </div>
        `;
        
        card.onclick = () => updateHero(movie);
        grid.appendChild(card);
    });
}

function updateHero(movie) {
    heroTitle.textContent = movie.title;
    heroDesc.textContent = movie.overview || "No overview available for this title.";
    
    if (movie.poster_path) {
        // In a real app, we'd use a backdrop path, but poster is a good fallback
        heroBackdrop.src = `${TMDB_IMG}${movie.poster_path}`;
        heroBackdrop.style.opacity = "0.4";
    }
}
