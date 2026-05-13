"""
Movie Recommender — FastAPI Backend
Hosted on Render.com
"""
from __future__ import annotations

import ast
import gc
import os
import pickle
import logging
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()
from difflib import get_close_matches
from pathlib import Path
from typing import List, Optional
from contextlib import asynccontextmanager

import pandas as pd
import requests
from fastapi import FastAPI, HTTPException, Query, Header, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

movies_df: pd.DataFrame = None   # type: ignore[assignment]
similarity = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle startup and shutdown events.
    Modern replacement for @app.on_event('startup').
    """
    global movies_df, similarity

    # 1. Try precomputed pickles (opt-in)
    p_movies = _load_pickle_safely("movies_data.pkl")
    p_sim    = _load_pickle_safely("similarity.pkl")

    if p_movies is not None and p_sim is not None:
        movies_df  = pd.DataFrame(p_movies).reset_index(drop=True)
        similarity = p_sim
        print(f"[startup] Loaded {len(movies_df)} movies from pickles.")
    else:
        # 2. Build from CSV (always available in repo)
        print("[startup] Building recommender from CSV files…")
        movies_df, similarity = _build_from_csv()
        print(f"[startup] Built recommender with {len(movies_df)} movies.")
    yield

app = FastAPI(
    title="Movie Recommender API",
    description="Content-based movie recommender powered by TMDB data.",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # Vercel frontend + local dev
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_IMG  = "https://image.tmdb.org/t/p/w500"

LOCAL_FALLBACK = """<svg xmlns='http://www.w3.org/2000/svg' width='500' height='750' viewBox='0 0 500 750'><rect width='500' height='750' fill='#1A1A1A'/><text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle' font-family='sans-serif' font-size='24' fill='#6E7DFF'>POSTER UNAVAILABLE</text></svg>"""


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def _safe_eval(value):
    try:
        return ast.literal_eval(value)
    except Exception:
        return []


def _parse_names(raw, limit: Optional[int] = None) -> list[str]:
    if not isinstance(raw, str):
        return []
    parsed = _safe_eval(raw)
    if not isinstance(parsed, list):
        return []
    names: list[str] = []
    for item in parsed:
        if isinstance(item, dict) and (name := item.get("name")):
            names.append(str(name))
            if limit and len(names) >= limit:
                break
    return names


def _parse_director(raw) -> str:
    if not isinstance(raw, str):
        return ""
    parsed = _safe_eval(raw)
    if not isinstance(parsed, list):
        return ""
    for item in parsed:
        if isinstance(item, dict) and item.get("job") == "Director":
            return str(item.get("name", ""))
    return ""


def _normalize(tokens: list[str]) -> list[str]:
    return [t.replace(" ", "") for t in tokens if t]


def _build_from_csv(
    movies_csv: str = "tmdb_5000_movies.csv",
    credits_csv: str = "tmdb_5000_credits.csv",
) -> tuple[pd.DataFrame, object]:
    """Build similarity matrix from raw TMDB CSV files."""
    movies_path = Path(movies_csv)
    credits_path = Path(credits_csv)

    if not movies_path.exists() or not credits_path.exists():
        missing = [str(p) for p in (movies_path, credits_path) if not p.exists()]
        raise RuntimeError(f"Missing CSV files: {', '.join(missing)}")

    mdf = pd.read_csv(movies_path, usecols=["movie_id", "title", "overview", "genres", "keywords", "vote_average", "popularity", "release_date", "runtime", "original_language"])
    cdf = pd.read_csv(credits_path, usecols=["title", "cast", "crew"])
    merged = mdf.merge(cdf, on="title")
    
    # Cleanup individual DFs
    del mdf, cdf
    gc.collect()

    keep = ["movie_id", "title", "overview", "genres", "keywords",
            "cast", "crew", "vote_average", "popularity",
            "release_date", "runtime", "original_language"]
    merged = merged[[c for c in keep if c in merged.columns]].copy()
    merged["overview"] = merged["overview"].fillna("")

    merged["genres_list"]   = merged["genres"].apply(_parse_names)
    merged["keywords_list"] = merged["keywords"].apply(_parse_names)
    merged["cast_list"]     = merged["cast"].apply(lambda v: _parse_names(v, limit=3))
    merged["director"]      = merged["crew"].apply(_parse_director)

    merged["tags"] = merged.apply(
        lambda r: " ".join(
            [r["overview"]]
            + _normalize(r["genres_list"])
            + _normalize(r["keywords_list"])
            + _normalize(r["cast_list"])
            + _normalize([r["director"]])
        ),
        axis=1,
    )

    vectorizer = CountVectorizer(max_features=5000, stop_words="english")
    # Keep vectors as sparse matrix to avoid huge dense array spike
    vectors = vectorizer.fit_transform(merged["tags"])
    
    # Pre-calculate similarity (returns dense array)
    # Use float16 to save ~50% more memory than float32 for the large matrix
    sim_matrix = cosine_similarity(vectors).astype("float16")
    
    # Cleanup large intermediate objects
    del vectors
    merged.drop(columns=["tags"], inplace=True)
    gc.collect()

    out = merged[["movie_id", "title", "overview", "genres_list",
                  "cast_list", "director", "vote_average", "popularity",
                  "release_date", "runtime", "original_language"]].copy()
    out.rename(columns={"genres_list": "genres", "cast_list": "cast",
                         "director": "crew"}, inplace=True)
    out = out.reset_index(drop=True)
    
    # Final cleanup
    del merged
    gc.collect()
    
    return out, sim_matrix


def _load_pickle_safely(path: str):
    p = Path(path)
    if not p.exists():
        return None
    with p.open("rb") as f:
        header = f.read(64)
    if header.startswith(b"version https://git-lfs.github.com/spec/v1"):
        return None          # LFS pointer — skip
    if os.getenv("ALLOW_UNSAFE_PICKLE", "1") != "1":
        return None
    with p.open("rb") as f:
        data = pickle.load(f)
        # Convert similarity matrix to float16 if it's dense numpy array
        if "similarity" in path.lower() and hasattr(data, "astype"):
            data = data.astype("float16")
        return data


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class RecommendRequest(BaseModel):
    title: str
    n: int = 10


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok", "movies_loaded": movies_df is not None and len(movies_df)}


@app.get("/movies", response_model=List[str])
def list_movies(
    q: Optional[str] = Query(None, description="Fuzzy search query"),
    limit: int = Query(50, ge=1, le=500),
):
    """Return all movie titles, optionally fuzzy-filtered by query."""
    titles = movies_df["title"].tolist()
    if q:
        matched = get_close_matches(q, titles, n=limit, cutoff=0.3)
        return matched
    return titles[:limit]


@app.get("/poster/{movie_id}")
@app.get("/poster/{movie_id}")
def get_poster_image(movie_id: int):
    """
    Proxy the actual image bytes from TMDB to the client.
    If no key is provided, returns the local SVG fallback.
    """
    if not TMDB_API_KEY:
        return Response(content=LOCAL_FALLBACK, media_type="image/svg+xml")
    
    try:
        # 1. Get the poster path
        url = f"{TMDB_BASE}/movie/{movie_id}?api_key={TMDB_API_KEY}"
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        poster_path = r.json().get("poster_path")
        
        if not poster_path:
            return RedirectResponse(url=LOCAL_FALLBACK_URL) # Fallback to a placeholder
            
        # 2. Fetch the actual image bytes
        img_url = f"{TMDB_IMG}{poster_path}"
        img_res = requests.get(img_url, stream=True, timeout=10)
        img_res.raise_for_status()
        
        return StreamingResponse(img_res.iter_content(chunk_size=1024), media_type=img_res.headers.get("Content-Type", "image/jpeg"))
        
    except Exception as exc:
        logger.error(f"Poster proxy failed: {exc}")
        raise HTTPException(status_code=502, detail="Failed to proxy image")

from fastapi.responses import StreamingResponse, RedirectResponse


# ---------------------------------------------------------------------------
# Smart Gateway Helpers
# ---------------------------------------------------------------------------

def _get_movie_preview(tmdb_id: int) -> Optional[str]:
    """Fetch the first YouTube trailer key for a given TMDB ID."""
    if not TMDB_API_KEY or not tmdb_id:
        return None
    try:
        url = f"{TMDB_BASE}/movie/{tmdb_id}/videos?api_key={TMDB_API_KEY}"
        r = requests.get(url, timeout=3)
        r.raise_for_status()
        videos = r.json().get("results", [])
        for v in videos:
            if v.get("site") == "YouTube" and v.get("type") in ["Trailer", "Teaser"]:
                return f"https://www.youtube.com/embed/{v['key']}?autoplay=1&mute=1&controls=0&loop=1&playlist={v['key']}"
        return None
    except Exception:
        return None

def _get_local_recommendations(idx: int, n: int, role: str = "guest") -> List[dict]:
    """Path 1: Local ML Recommendations."""
    try:
        distances = similarity[idx]
        top = sorted(enumerate(distances), key=lambda x: x[1], reverse=True)[1 : n + 1]
        
        results = []
        for i, score in top:
            row = movies_df.iloc[i]
            is_member = (role == "member")
            
            results.append({
                "id": int(row["movie_id"]) if pd.notna(row.get("movie_id")) else 0,
                "title": str(row["title"]),
                "year": str(row.get("release_date", ""))[:4],
                "poster_path": None,
                "overview": str(row.get("overview", "")) if is_member else "Sign in to view summary",
                "vote_average": float(row.get("vote_average", 0.0)) if is_member else 0.0,
                "preview_url": _get_movie_preview(int(row["movie_id"])) if is_member else None,
                "is_restricted": not is_member,
                "source": "local"
            })
        return results
    except Exception:
        return []

def _get_tmdb_recommendations(title: str, n: int, role: str = "guest") -> List[dict]:
    """Path 2: TMDB API Fallback."""
    if not TMDB_API_KEY:
        return []
        
    try:
        search_url = f"{TMDB_BASE}/search/movie?api_key={TMDB_API_KEY}&query={title}"
        r = requests.get(search_url, timeout=5)
        r.raise_for_status()
        search_data = r.json()
        
        if not search_data.get("results"):
            return []
            
        tmdb_id = search_data["results"][0]["id"]
        rec_url = f"{TMDB_BASE}/movie/{tmdb_id}/recommendations?api_key={TMDB_API_KEY}"
        r = requests.get(rec_url, timeout=5)
        r.raise_for_status()
        rec_data = r.json()
        
        results = []
        is_member = (role == "member")
        for item in rec_data.get("results", [])[:n]:
            results.append({
                "id": int(item["id"]),
                "title": str(item["title"]),
                "year": str(item.get("release_date", ""))[:4],
                "poster_path": item.get("poster_path"),
                "overview": str(item.get("overview", "")) if is_member else "Sign in to view summary",
                "vote_average": float(item.get("vote_average", 0.0)) if is_member else 0.0,
                "preview_url": _get_movie_preview(int(item["id"])) if is_member else None,
                "is_restricted": not is_member,
                "source": "tmdb"
            })
        return results
    except Exception:
        return []

from fastapi import Header

@app.post("/recommend")
def recommend(req: RecommendRequest, x_user_role: Optional[str] = Header("guest")):
    """
    Smart Gateway with Gated Access:
    - Detects role from X-User-Role header (default: guest)
    - Redacts sensitive fields for guest role.
    """
    title = req.title.strip()
    n = max(1, min(req.n, 20))
    role = x_user_role if x_user_role in ["guest", "member"] else "guest"

    # Try Local Path
    local_idx = None
    if movies_df is not None:
        mask = movies_df["title"].str.lower() == title.lower()
        if mask.any():
            local_idx = movies_df[mask].index[0]

    if local_idx is not None:
        recs = _get_local_recommendations(local_idx, n, role=role)
        if recs:
            return {"query": title, "path": "local", "role": role, "recommendations": recs}

    # Try Fallback Path
    recs = _get_tmdb_recommendations(title, n, role=role)
    if recs:
        return {"query": title, "path": "tmdb", "role": role, "recommendations": recs}

    return {"query": title, "path": "none", "role": role, "recommendations": []}


# Mount frontend for local development preview.
# On Vercel the frontend is served directly; this only kicks in locally.
# We mount at '/' last so that API routes (/movies, /recommend) take precedence.
_frontend_dir = Path(__file__).parent.parent / "frontend"
if _frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dir), html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    # Use 0.0.0.0 to allow access from local network if needed
    uvicorn.run(app, host="0.0.0.0", port=8000)

