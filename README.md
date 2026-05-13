# CineMatch — Movie Recommendation App

Content-based movie recommender split into two independently hosted services:

| Layer    | Tech          | Host   |
|----------|---------------|--------|
| Backend  | FastAPI + sklearn | [Render.com](https://render.com) |
| Frontend | HTML + CSS + JS   | [Vercel.com](https://vercel.com) |

---

## Architecture

```
Browser → Vercel (frontend/) → Render (api/recommend.py) → TMDB API
```

- The frontend is a **zero-dependency static site** (no build step needed).
- The backend builds the similarity matrix from CSV files at startup — no Git LFS required.

---

## Folder Structure

```
Movie_recommendation_app/
├── api/
│   ├── recommend.py        ← FastAPI app (Render)
│   └── requirements.txt    ← Backend deps
├── frontend/
│   ├── index.html          ← Single-page app (Vercel)
│   ├── style.css
│   ├── app.js
│   └── vercel.json
├── tmdb_5000_movies.csv    ← Source data (required by backend)
├── tmdb_5000_credits.csv   ← Source data (required by backend)
├── render.yaml             ← Render deployment blueprint
└── requirements.txt        ← Legacy Streamlit deps (not used for deploy)
```

---

## Deploy — Backend (Render)

1. Push this repo to GitHub.
2. Go to [render.com](https://render.com) → **New → Web Service**.
3. Connect your GitHub repo.
4. Settings:
   - **Root Directory**: `Movie_recommendation_app`
   - **Build command**: `pip install -r api/requirements.txt`
   - **Start command**: `uvicorn api.recommend:app --host 0.0.0.0 --port $PORT`
5. Under **Environment Variables**, add:
   ```
   TMDB_API_KEY = <your TMDB API key>
   ```
6. Click **Deploy**. First startup takes ~60 s (building similarity matrix).
7. Note your Render URL, e.g. `https://movie-recommender-api.onrender.com`.

### Health check
```
GET https://your-service.onrender.com/health
→ {"status":"ok","movies_loaded":4807}
```

---

## Deploy — Frontend (Vercel)

1. Open `frontend/app.js` and set `API_BASE` to your Render URL:
   ```js
   const API_BASE = "https://movie-recommender-api.onrender.com";
   ```
2. Push to GitHub.
3. Go to [vercel.com](https://vercel.com) → **New Project**.
4. Connect the same repo.
5. Settings:
   - **Root Directory**: `Movie_recommendation_app/frontend`
   - Framework preset: **Other** (plain static)
6. Click **Deploy** → your site is live.

---

## Run Locally

### Backend
```bash
cd Movie_recommendation_app
pip install -r api/requirements.txt
uvicorn api.recommend:app --reload
# → http://localhost:8000
# → http://localhost:8000/docs  (interactive Swagger UI)
```

### Frontend
Just open `frontend/index.html` in a browser, **or**:
```bash
cd Movie_recommendation_app/frontend
python -m http.server 3000
# → http://localhost:3000
```

> **Note**: Update `API_BASE` in `app.js` to `http://localhost:8000` for local development.

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/health` | Health check |
| `GET`  | `/movies?q=<query>&limit=50` | List / fuzzy-search titles |
| `POST` | `/recommend` | `{"title":"...", "n":10}` → recommendations |
| `GET`  | `/poster/{movie_id}` | Proxy TMDB poster URL |

---

## Environment Variables

| Variable | Where | Purpose |
|----------|-------|---------|
| `TMDB_API_KEY` | Render dashboard | Fetches movie posters |
| `ALLOW_UNSAFE_PICKLE` | Optional, Render | Set to `1` to use prebuilt `.pkl` files instead of CSV |
