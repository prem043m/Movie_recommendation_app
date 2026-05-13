<<<<<<< HEAD
import streamlit as st
import pandas as pd
import pickle
import requests
import os
from dotenv import load_dotenv
from difflib import get_close_matches

load_dotenv()

st.set_page_config(page_title="🎬 Movie Recommender", layout="wide", page_icon="🎬")

st.markdown("""
    <style>
        * {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .main {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .stApp {
            background: linear-gradient(135deg, #4a4a4a 0%, #2c2c2c 100%);
        }
        h1 {
            color: #ffffff;
            text-align: center;
            font-size: 3rem;
            margin-bottom: 2rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .movie-card {
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            margin: 20px 0;
            border: 1px solid rgba(255,255,255,0.2);
        }
        .rating {
            background: linear-gradient(45deg, #ff6b6b, #feca57);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: bold;
            font-size: 1.2em;
        }
    </style>
""", unsafe_allow_html=True)

api_key = ""
try:
    api_key = st.secrets["TMDB_API_KEY"]
except Exception:
    api_key = os.getenv("TMDB_API_KEY", "")

if not api_key:
    st.warning(
        "TMDB API key not found. For local runs, add TMDB_API_KEY in .env. "
        "For Streamlit Cloud, add it in app Secrets."
    )

@st.cache_data
def fetch_poster(movie_id):
    if not api_key:
        return None

    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return "https://image.tmdb.org/t/p/w500" + data['poster_path'] if data.get("poster_path") else None
    except:
        return None


def render_poster(poster_url):
    if poster_url:
        st.image(poster_url, use_container_width=True)
    else:
        st.caption("Poster unavailable")
=======
import ast
import os
import pickle
from pathlib import Path

import pandas as pd
import streamlit as st
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def load_pickle_file(file_path):
    """Load a pickle file and provide clear guidance for common setup issues."""
    path = Path(file_path)

    if not path.exists():
        raise RuntimeError(
            f"Missing required file: {file_path}. "
            "Make sure project assets are present in the repository."
        )

    # Git LFS pointer files are plain text and start with this marker.
    with path.open('rb') as f:
        header = f.read(64)

    if header.startswith(b"version https://git-lfs.github.com/spec/v1"):
        raise RuntimeError(
            f"{file_path} is a Git LFS pointer, not the actual data file.\n"
            "Install and fetch LFS objects, then re-run the app:\n"
            "  git lfs install\n"
            "  git lfs pull"
        )

    # Avoid unpickling by default. Unpickling can execute arbitrary code
    # if the pickle file is untrusted. Require an explicit opt-in via
    # the ALLOW_UNSAFE_PICKLE environment variable to proceed.
    if os.environ.get('ALLOW_UNSAFE_PICKLE', '0') != '1':
        raise RuntimeError(
            f"Refusing to unpickle {file_path} by default.\n"
            "If you trust this file and understand the risks, set the"
            " environment variable ALLOW_UNSAFE_PICKLE=1 and retry, or"
            " remove the pickle and let the app build artifacts from CSV."
        )

    try:
        with path.open('rb') as f:
            return pickle.load(f)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to read {file_path}: invalid or unsafe pickle content. "
            "If this repo uses Git LFS, run 'git lfs pull'."
        ) from exc
>>>>>>> fd27852 ( risk managed)

def recommend(movie):
    try:
        movie = movie.strip().lower()
        movies['title_clean'] = movies['title'].str.strip().str.lower()

        movie_matches = movies[movies['title_clean'] == movie]
        if movie_matches.empty:
            return [] 

        # Use positional index to match the similarity matrix row positions.
        movie_index = movie_matches.index[0]
        distances = similarity[movie_index]
        movies_list = sorted(
            list(enumerate(distances)),
            reverse=True,
            key=lambda x: x[1]
        )[1:11] 

        recommended_movies = []
        for i in movies_list:
            movie_data = movies.iloc[i[0]]
            recommended_movies.append({
                'title': movie_data['title'],
                'overview': movie_data['overview'],
                'genres': movie_data['genres'],
                'cast': movie_data['cast'],
                'crew': movie_data['crew'],
                'keywords': movie_data['keywords'],
                'poster': fetch_poster(movie_data['movie_id']),
                'popularity': movie_data['popularity'],
                'budget': movie_data['budget'],
                'homepage': movie_data['homepage'],
                'release_date': movie_data['release_date'],
                'runtime': movie_data['runtime'],
                'status': movie_data['status'],
                'original_language': movie_data['original_language'],
                'vote_average': movie_data['vote_average']
            })

        return recommended_movies
    except Exception as e:
        st.error(f"Error in recommendation: {e}")
        return []

@st.cache_data
def load_data():
    with open("movies_data.pkl", "rb") as f:
        movies = pickle.load(f)
        if not isinstance(movies, pd.DataFrame):
            movies = pd.DataFrame(movies)
    with open("similarity.pkl", "rb") as f:
        similarity = pickle.load(f)

<<<<<<< HEAD
    # Ensure dataframe row positions align with similarity matrix indices.
    movies = movies.reset_index(drop=True)

    if len(movies) != len(similarity):
        valid_size = min(len(movies), len(similarity))
        movies = movies.iloc[:valid_size].reset_index(drop=True)
        similarity = similarity[:valid_size, :valid_size]
=======
def parse_names(raw_value, limit=None):
    """Extract person/category names from JSON-like list strings."""
    if not isinstance(raw_value, str):
        return []

    try:
        parsed = ast.literal_eval(raw_value)
    except (SyntaxError, ValueError):
        return []

    if not isinstance(parsed, list):
        return []

    names = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        name = item.get('name')
        if not name:
            continue
        names.append(str(name))
        if limit and len(names) >= limit:
            break
    return names


def parse_director(raw_value):
    """Extract the movie director from JSON-like crew data."""
    if not isinstance(raw_value, str):
        return ''

    try:
        parsed = ast.literal_eval(raw_value)
    except (SyntaxError, ValueError):
        return ''

    if not isinstance(parsed, list):
        return ''

    for item in parsed:
        if isinstance(item, dict) and item.get('job') == 'Director':
            return str(item.get('name', ''))
    return ''


def normalize_for_tags(tokens):
    """Normalize tokens to improve text-vector matching quality."""
    return [token.replace(' ', '') for token in tokens if token]


@st.cache_resource(show_spinner=False)
def build_recommender_from_csv():
    """Build recommendation artifacts directly from TMDB CSV files."""
    movies_path = Path('tmdb_5000_movies.csv')
    credits_path = Path('tmdb_5000_credits.csv')

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


# Load recommendation artifacts, preferring precomputed pickle files.
try:
    movies_data = load_pickle_file('movies_data.pkl')
    movies = pd.DataFrame(movies_data)
    similarity = load_pickle_file('similarity.pkl')
except RuntimeError as exc:
    st.warning(str(exc))
    st.info('Falling back to CSV processing. The first run may take up to a minute.')
    try:
        movies, similarity = build_recommender_from_csv()
    except Exception as csv_exc:
        st.error(f'Could not build recommender from CSV files: {csv_exc}')
        st.stop()
>>>>>>> fd27852 ( risk managed)

    movies["title_clean"] = movies["title"].str.strip().str.lower()
    return movies, similarity

try:
    movies, similarity = load_data()
except FileNotFoundError as e:
    st.error(f"Required file missing: {e}")
    st.stop()

# Initialize session state
if 'recommendations' not in st.session_state:
    st.session_state.recommendations = []
if 'selected_movie' not in st.session_state:
    st.session_state.selected_movie = None
if 'favorites' not in st.session_state:
    st.session_state.favorites = []
if 'user_ratings' not in st.session_state:
    st.session_state.user_ratings = {}

st.markdown("<h1>🎬 Movie Recommendation System</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.2em; color: #7f8c8d; margin-bottom: 2rem;'>Discover your next favorite movie with AI-powered recommendations</p>", unsafe_allow_html=True)

# Sidebar
st.sidebar.markdown("### 🔍 Movie Search")
search_query = st.sidebar.text_input("Search for a movie: ", placeholder="Type movie name....")

# Filters
all_genres = set()
for genres_list in movies['genres']:
    if isinstance(genres_list, list):
        all_genres.update(genres_list)
genres_filter = st.sidebar.selectbox("Filter by genre:", ["All Genres"] + sorted(list(all_genres)))

min_rating = st.sidebar.slider("Minimum Rating: ", 0.0, 10.0, 0.0, 0.1)

# Year filter
movies['year'] = pd.to_datetime(movies['release_date'], errors='coerce').dt.year
min_year = int(movies['year'].min()) if not movies['year'].isna().all() else 1900
max_year = int(movies['year'].max()) if not movies['year'].isna().all() else 2024
year_range = st.sidebar.slider("Release Year Range:", min_year, max_year, (min_year, max_year))

# Apply filters
filtered_movies = movies.copy()
if genres_filter != "All Genres":
    filtered_movies = filtered_movies[filtered_movies['genres'].apply(
        lambda x: genres_filter in x if isinstance(x, list) else False
    )]
filtered_movies = filtered_movies[filtered_movies['vote_average'] >= min_rating]
filtered_movies = filtered_movies[
    (filtered_movies['year'] >= year_range[0]) & 
    (filtered_movies['year'] <= year_range[1])
]

# Search logic
selected_movie_name = None
if search_query:
    movie_title = filtered_movies['title'].tolist()
    matches = get_close_matches(search_query, movie_title, n=10, cutoff=0.3)
    if matches:
        selected_movie_name = st.sidebar.selectbox("Select from matches:", matches)
    else:
        st.sidebar.error("NO movies found matching your search.")    
else:
    if not filtered_movies.empty:
        selected_movie_name = st.sidebar.selectbox("Choose a movie:", filtered_movies['title'].values)

# User rating system
if selected_movie_name:
    user_rating = st.sidebar.slider(f"Rate '{selected_movie_name}':", 1, 5, 3)
    if st.sidebar.button("⭐ Save Rating"):
        st.session_state.user_ratings[selected_movie_name] = user_rating
        st.sidebar.success(f"Rated {user_rating}/5 stars!")

st.sidebar.markdown("---")
st.sidebar.markdown("💡 **Tip:** Select any movie and click 'Get Recommendations' to discover similar films!")

# Control buttons
if st.sidebar.button("🔄 Clear Recommendations"):
    st.session_state.recommendations = []
    st.session_state.selected_movie = None
    st.rerun()

# Quick stats
st.sidebar.markdown("### 📊 Quick Stats")
st.sidebar.metric("Total Movies", len(movies))
st.sidebar.metric("Filtered Movies", len(filtered_movies))
st.sidebar.metric("Available Genres", len(all_genres))

# Favorites section
if st.session_state.favorites:
    st.sidebar.markdown("### ⭐ Favorites")
    for fav in st.session_state.favorites[-3:]:
        st.sidebar.write(f"• {fav['title']}")
    if st.sidebar.button("View All Favorites"):
        st.session_state.show_favorites = True

# Get recommendations
if st.sidebar.button("🎯 Get Recommendations", type="primary") and selected_movie_name:
    with st.spinner('🎬 Getting recommendations...'):
        recommendations = recommend(selected_movie_name)
        st.session_state.recommendations = recommendations
        st.session_state.selected_movie = selected_movie_name

# Display recommendations
if st.session_state.recommendations:
    recommendations = st.session_state.recommendations
    selected_movie_name = st.session_state.selected_movie

    if recommendations:
        # Selected movie
        selected_movie_data = movies[movies['title'] == selected_movie_name].iloc[0]
        
        st.markdown(f"<div class='movie-card'><h2 style='color: #2c3e50; margin-bottom: 1rem;'>🎬 Selected Movie: {selected_movie_name}</h2></div>", unsafe_allow_html=True)
        col1, col2 = st.columns([1, 2])

        with col1:
            render_poster(fetch_poster(selected_movie_data.movie_id))

        with col2:
            st.markdown(f"""
                <h3 style="margin:0;">{selected_movie_data.title}</h3>
                <p style="margin:5px 0;" class="rating">
                    ⭐ {selected_movie_data.vote_average}/10
                </p>
                <p style="margin:0; color:gray;">
                    📅 {selected_movie_data.release_date} &nbsp;&nbsp; | &nbsp;&nbsp; 
                    ⏳ {int(selected_movie_data.runtime) if pd.notna(selected_movie_data.runtime) else 'N/A'} min &nbsp;&nbsp; | &nbsp;&nbsp;
                    🌍 {selected_movie_data.original_language.upper()}
                </p>
                <hr style="margin:10px 0;">
                <p>
                    <b>🎭 Genres:</b> {', '.join(selected_movie_data.genres) if isinstance(selected_movie_data.genres, list) else 'N/A'}<br>
                    <b>🎬 Director:</b> {', '.join(selected_movie_data.crew) if isinstance(selected_movie_data.crew, list) else 'N/A'}<br>
                    <b>👥 Cast:</b> {', '.join(selected_movie_data.cast[:3]) if isinstance(selected_movie_data.cast, list) else 'N/A'}<br>
                    <b>🔥 Popularity:</b> {round(selected_movie_data.popularity, 2)}<br>
                    <b>💰 Budget:</b> ${selected_movie_data.budget:,} if pd.notna(selected_movie_data.budget) and selected_movie_data.budget > 0 else 'N/A'<br>
                    <b>📌 Status:</b> {selected_movie_data.status}
                </p>
            """, unsafe_allow_html=True)

            # Overview section
            with st.expander("📖 Overview"):
                overview_text = ' '.join(selected_movie_data.overview) if isinstance(selected_movie_data.overview, list) else selected_movie_data.overview
                st.write(overview_text)

            # Homepage
            if pd.notna(selected_movie_data.homepage) and selected_movie_data.homepage != "":
                st.markdown(f"[🔗 Official Website]({selected_movie_data.homepage})", unsafe_allow_html=True)

        # Show user ratings
        if st.session_state.user_ratings:
            with st.expander("📊 Your Ratings"):
                for movie, rating in st.session_state.user_ratings.items():
                    st.write(f"⭐ {movie}: {rating}/5")

        st.markdown("<div style='margin: 3rem 0 2rem 0;'><h2 style='color: #2c3e50; text-align: center;'>🎯 Movies You Might Love</h2><p style='text-align: center; color: #7f8c8d;'>Based on your selection, here are our top recommendations:</p></div>", unsafe_allow_html=True)

        # Recommended movies
        for i, movie in enumerate(recommendations, 1):
            col1, col2 = st.columns([1, 2])

            with col1:
                render_poster(movie['poster'])

            with col2:
                st.markdown(f"""
                    <h3 style="margin:0;">{movie['title']}</h3>
                    <p style="margin:5px 0;" class="rating">
                        ⭐ {movie['vote_average']}/10
                    </p>
                    <p style="margin:0; color:gray;">
                        📅 {movie['release_date']} &nbsp;&nbsp; | &nbsp;&nbsp; 
                        ⏳ {int(movie['runtime']) if movie['runtime'] else 'N/A'} min &nbsp;&nbsp; | &nbsp;&nbsp;
                        🌍 {movie['original_language'].upper() if movie['original_language'] else 'N/A'}
                    </p>
                    <hr style="margin:10px 0;">
                    <p>
                        <b>🎭 Genres:</b> {', '.join(movie['genres']) if isinstance(movie['genres'], list) and movie['genres'] else 'N/A'}<br>
                        <b>🎬 Director:</b> {', '.join(movie['crew']) if isinstance(movie['crew'], list) and movie['crew'] else 'N/A'}<br>
                        <b>👥 Cast:</b> {', '.join(movie['cast'][:3]) if isinstance(movie['cast'], list) and movie['cast'] else 'N/A'}<br>
                        <b>🔥 Popularity:</b> {round(movie['popularity'], 2) if movie['popularity'] else 'N/A'}<br>
                        <b>💰 Budget:</b> ${movie['budget']:,} <br>
                        <b>📌 Status:</b> {movie['status'] if movie['status'] else 'N/A'}
                    </p>
                """, unsafe_allow_html=True)

                # Overview
                with st.expander("📖 Overview"):
                    overview_text = ' '.join(movie['overview']) if isinstance(movie['overview'], list) else movie['overview']
                    st.write(overview_text if overview_text else "No overview available.")

                # Homepage
                if movie['homepage']:
                    st.markdown(f"[🔗 Official Website]({movie['homepage']})", unsafe_allow_html=True)
                
                # Add to favorites
                if st.button(f"⭐ Add to Favorites", key=f"fav_{i}"):
                    if movie['title'] not in [fav['title'] for fav in st.session_state.favorites]:
                        st.session_state.favorites.append(movie)
                        st.success(f"Added {movie['title']} to favorites!")
                    else:
                        st.info("Already in favorites!")

            st.markdown("<div style='margin: 2rem 0; border-bottom: 2px solid #ecf0f1;'></div>", unsafe_allow_html=True)
        
        # Export functionality
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save Recommendations"):
                rec_data = pd.DataFrame(recommendations)
                csv = rec_data.to_csv(index=False)
                st.download_button(
                    label="📎 Download CSV",
                    data=csv,
                    file_name=f"recommendations_{selected_movie_name.replace(' ', '_')}.csv",
                    mime="text/csv"
                )
        with col2:
            if st.button("🔄 Get New Recommendations"):
                st.session_state.recommendations = []
                st.session_state.selected_movie = None
                st.rerun()
    else:
        st.error("Sorry, couldn't find recommendations for this movie.")

# Show favorites if requested
if st.session_state.get('show_favorites', False):
    st.markdown("<h2 style='color: #2c3e50; text-align: center;'>⭐ Your Favorite Movies</h2>", unsafe_allow_html=True)
    if st.session_state.favorites:
        for i, fav in enumerate(st.session_state.favorites):
            col1, col2, col3 = st.columns([1, 3, 1])
            with col1:
                render_poster(fav['poster'])
            with col2:
                st.write(f"**{fav['title']}** - ⭐ {fav['vote_average']}/10")
                st.write(f"🎭 {', '.join(fav['genres'][:3]) if fav['genres'] else 'N/A'}")
            with col3:
                if st.button("Remove", key=f"remove_{i}"):
                    st.session_state.favorites.pop(i)
                    st.rerun()
        if st.button("Hide Favorites"):
            st.session_state.show_favorites = False
            st.rerun()
    else:
        st.info("No favorites added yet!")
        if st.button("Hide Favorites"):
            st.session_state.show_favorites = False
            st.rerun()

# Show popular movies when no recommendations
if not st.session_state.recommendations:
    st.markdown("### 🔥 Popular Movies")
    popular_movies = movies.nlargest(10, 'popularity')
    
    cols = st.columns(5)
    for idx, (_, movie) in enumerate(popular_movies.iterrows()):
        with cols[idx % 5]:
            poster = fetch_poster(movie['movie_id'])
            render_poster(poster)
            st.write(f"**{movie['title']}**")
            st.write(f"⭐ {movie['vote_average']}/10")