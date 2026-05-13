"""
Movie Recommender — FastAPI Backend
Hosted on Render.com
"""
from __future__ import annotations

import ast
import os
import pickle
from difflib import get_close_matches
from pathlib import Path
from typing import List, Optional

import pandas as pd
import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Movie Recommender API",
    description="Content-based movie recommender powered by TMDB data.",
    version="2.0.0",
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

# Global recommendation state (loaded at startup)
movies_df: pd.DataFrame = None   # type: ignore[assignment]
similarity = None


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

    mdf = pd.read_csv(movies_path)
    cdf = pd.read_csv(credits_path)
    merged = mdf.merge(cdf, on="title")

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
    vectors = vectorizer.fit_transform(merged["tags"]).toarray()
    sim_matrix = cosine_similarity(vectors)

    out = merged[["movie_id", "title", "overview", "genres_list",
                  "cast_list", "director", "vote_average", "popularity",
                  "release_date", "runtime", "original_language"]].copy()
    out.rename(columns={"genres_list": "genres", "cast_list": "cast",
                         "director": "crew"}, inplace=True)
    out = out.reset_index(drop=True)
    return out, sim_matrix


def _load_pickle_safely(path: str):
    p = Path(path)
    if not p.exists():
        return None
    with p.open("rb") as f:
        header = f.read(64)
    if header.startswith(b"version https://git-lfs.github.com/spec/v1"):
        return None          # LFS pointer — skip
    if os.getenv("ALLOW_UNSAFE_PICKLE", "0") != "1":
        return None
    with p.open("rb") as f:
        return pickle.load(f)


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

@app.on_event("startup")
def prepare():
    global movies_df, similarity

    # 1. Try precomputed pickles (opt-in)
    p_movies = _load_pickle_safely("movies_data.pkl")
    p_sim    = _load_pickle_safely("similarity.pkl")

    if p_movies is not None and p_sim is not None:
        movies_df  = pd.DataFrame(p_movies).reset_index(drop=True)
        similarity = p_sim
        print(f"[startup] Loaded {len(movies_df)} movies from pickles.")
        return

    # 2. Build from CSV (always available in repo)
    print("[startup] Building recommender from CSV files…")
    movies_df, similarity = _build_from_csv()
    print(f"[startup] Built recommender with {len(movies_df)} movies.")


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
def get_poster(movie_id: int):
    """Proxy TMDB poster URL so the API key is never exposed to the browser."""
    if not TMDB_API_KEY:
        raise HTTPException(status_code=503, detail="TMDB_API_KEY not configured")
    try:
        url = f"{TMDB_BASE}/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"
        r = requests.get(url, timeout=6)
        r.raise_for_status()
        data = r.json()
        poster_path = data.get("poster_path")
        if not poster_path:
            raise HTTPException(status_code=404, detail="No poster available")
        return {"poster_url": f"{TMDB_IMG}{poster_path}"}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.post("/recommend")
def recommend(req: RecommendRequest):
    """Return up to `n` content-based recommendations for the given title."""
    title = req.title.strip()
    n     = max(1, min(req.n, 20))

    # Exact match first, then case-insensitive
    mask = movies_df["title"] == title
    if not mask.any():
        mask = movies_df["title"].str.lower() == title.lower()
    if not mask.any():
        raise HTTPException(status_code=404, detail=f"Movie '{title}' not found")

    idx       = movies_df[mask].index[0]
    distances = similarity[idx]
    top       = sorted(enumerate(distances), key=lambda x: x[1], reverse=True)[1: n + 1]

    results = []
    for i, score in top:
        row = movies_df.iloc[i]
        genres = row["genres"] if isinstance(row["genres"], list) else []
        cast   = row["cast"]   if isinstance(row["cast"],   list) else []
        results.append({
            "movie_id":          int(row["movie_id"]) if pd.notna(row.get("movie_id")) else None,
            "title":             row["title"],
            "overview":          row["overview"] if isinstance(row["overview"], str) else "",
            "genres":            genres,
            "cast":              cast[:3],
            "director":          row["crew"] if isinstance(row["crew"], str) else "",
            "vote_average":      float(row["vote_average"]) if pd.notna(row.get("vote_average")) else 0.0,
            "popularity":        float(row["popularity"])   if pd.notna(row.get("popularity"))   else 0.0,
            "release_date":      str(row.get("release_date", "")) or "",
            "runtime":           int(row["runtime"]) if pd.notna(row.get("runtime")) else None,
            "original_language": str(row.get("original_language", "")) or "",
            "similarity_score":  round(float(score), 4),
        })

    # Seed movie info
    seed = movies_df.iloc[idx]
    seed_genres = seed["genres"] if isinstance(seed["genres"], list) else []
    seed_cast   = seed["cast"]   if isinstance(seed["cast"],   list) else []

    return {
        "query": title,
        "seed": {
            "movie_id":          int(seed["movie_id"]) if pd.notna(seed.get("movie_id")) else None,
            "title":             seed["title"],
            "overview":          seed["overview"] if isinstance(seed["overview"], str) else "",
            "genres":            seed_genres,
            "cast":              seed_cast[:3],
            "director":          seed["crew"] if isinstance(seed["crew"], str) else "",
            "vote_average":      float(seed["vote_average"]) if pd.notna(seed.get("vote_average")) else 0.0,
            "popularity":        float(seed["popularity"])   if pd.notna(seed.get("popularity"))   else 0.0,
            "release_date":      str(seed.get("release_date", "")) or "",
            "runtime":           int(seed["runtime"]) if pd.notna(seed.get("runtime")) else None,
            "original_language": str(seed.get("original_language", "")) or "",
        },
        "results": results,
    }


# Mount frontend for local development preview.
# On Vercel the frontend is served directly; this only kicks in locally.
# We mount at '/' last so that API routes (/movies, /recommend) take precedence.
_frontend_dir = Path(__file__).parent.parent / "frontend"
if _frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dir), html=True), name="frontend")

