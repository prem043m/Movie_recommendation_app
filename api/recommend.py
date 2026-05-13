from pathlib import Path
import ast
import os
import pickle
from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity


app = FastAPI(title="Movie Recommender API")


class RecommendRequest(BaseModel):
    title: str


def safe_literal_eval(value):
    try:
        return ast.literal_eval(value)
    except Exception:
        return []


def parse_names(raw_value, limit=None):
    if not isinstance(raw_value, str):
        return []
    parsed = safe_literal_eval(raw_value)
    if not isinstance(parsed, list):
        return []
    names = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        name = item.get('name')
        if name:
            names.append(str(name))
            if limit and len(names) >= limit:
                break
    return names


def parse_director(raw_value):
    if not isinstance(raw_value, str):
        return ''
    parsed = safe_literal_eval(raw_value)
    if not isinstance(parsed, list):
        return ''
    for item in parsed:
        if isinstance(item, dict) and item.get('job') == 'Director':
            return str(item.get('name', ''))
    return ''


def normalize_for_tags(tokens):
    return [token.replace(' ', '') for token in tokens if token]


def build_recommender_from_csv(movies_csv='tmdb_5000_movies.csv', credits_csv='tmdb_5000_credits.csv'):
    movies_path = Path(movies_csv)
    credits_path = Path(credits_csv)
    if not movies_path.exists() or not credits_path.exists():
        missing = []
        if not movies_path.exists():
            missing.append(str(movies_path))
        if not credits_path.exists():
            missing.append(str(credits_path))
        raise RuntimeError(f"Missing CSV files: {', '.join(missing)}")

    movies_df = pd.read_csv(movies_path)
    credits_df = pd.read_csv(credits_path)

    merged = movies_df.merge(credits_df, on='title')
    merged = merged[['movie_id', 'title', 'overview', 'genres', 'keywords', 'cast', 'crew']].copy()
    merged['overview'] = merged['overview'].fillna('')

    merged['genres_list'] = merged['genres'].apply(parse_names)
    merged['keywords_list'] = merged['keywords'].apply(parse_names)
    merged['cast_list'] = merged['cast'].apply(lambda value: parse_names(value, limit=3))
    merged['director'] = merged['crew'].apply(parse_director)

    merged['tags'] = merged.apply(
        lambda row: ' '.join(
            [row['overview']]
            + normalize_for_tags(row['genres_list'])
            + normalize_for_tags(row['keywords_list'])
            + normalize_for_tags(row['cast_list'])
            + normalize_for_tags([row['director']])
        ),
        axis=1,
    )

    vectorizer = CountVectorizer(max_features=5000, stop_words='english')
    vectors = vectorizer.fit_transform(merged['tags']).toarray()
    similarity_matrix = cosine_similarity(vectors)

    prepared_movies = merged[['title', 'overview', 'genres_list', 'cast_list', 'director']].copy()
    prepared_movies.rename(
        columns={
            'genres_list': 'genres',
            'cast_list': 'cast',
            'director': 'crew',
        },
        inplace=True,
    )
    prepared_movies['genres'] = prepared_movies['genres'].apply(lambda items: ', '.join(items))
    prepared_movies['cast'] = prepared_movies['cast'].apply(lambda items: ', '.join(items))

    return prepared_movies, similarity_matrix


@app.on_event('startup')
def prepare():
    """Load or build the recommender on startup."""
    global movies_df, similarity
    movies_df = None
    similarity = None

    # Try to load precomputed pickles if ALLOW_UNSAFE_PICKLE=1
    try:
        if os.environ.get('ALLOW_UNSAFE_PICKLE', '0') == '1':
            p_movies = Path('movies_data.pkl')
            p_sim = Path('similarity.pkl')
            if p_movies.exists() and p_sim.exists():
                with p_movies.open('rb') as f:
                    movies_df = pd.DataFrame(pickle.load(f))
                with p_sim.open('rb') as f:
                    similarity = pickle.load(f)
    except Exception:
        movies_df = None
        similarity = None

    if movies_df is None or similarity is None:
        movies_df, similarity = build_recommender_from_csv()


@app.get('/movies', response_model=List[str])
def list_movies():
    return movies_df['title'].tolist()


@app.post('/recommend')
def recommend(req: RecommendRequest):
    try:
        movie_matches = movies_df[movies_df['title'] == req.title]
        if movie_matches.empty:
            raise HTTPException(status_code=404, detail='Movie not found')
        movie_index = movie_matches.index[0]
        distances = similarity[movie_index]
        movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

        recommended = []
        for i in movies_list:
            movie_data = movies_df.iloc[i[0]]
            recommended.append({
                'title': movie_data.title,
                'overview': movie_data.overview,
                'genres': movie_data.genres,
                'cast': movie_data.cast,
                'director': movie_data.crew,
            })
        return {'results': recommended}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
