import streamlit as st
import pandas as pd
import pickle
import requests
from difflib import get_close_matches

st.markdown("""
    <style>
        * {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
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

api_key = st.secrets["TMDB_API_KEY"]

def fetch_poster(movie_id):
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
        response = requests.get(url)
        data = response.json()
        return "https://image.tmdb.org/t/p/w500" + data['poster_path'] if data.get("poster_path") else None
    except:
        return None

def recommend(movie):
    try:
        movie = movie.strip().lower()
        movies['title_clean'] = movies['title'].str.strip().str.lower()
        
        movie_matches = movies[movies['title_clean'] == movie]
        if movie_matches.empty:
            return []

        movie_index = movie_matches.index[0]
        distances = similarity[movie_index]
        movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

        recommended_movies = []
        for i in movies_list:
            movie_data = movies.iloc[i[0]]
            recommended_movies.append({
                'title': movie_data['title'],
                'overview': movie_data['overview'],
                'genres': movie_data['genres'],
                'cast': movie_data['cast'],
                'crew': movie_data['crew'],
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
        st.error(f"Error: {e}")
        return []

try:
    with open("movies_data.pkl", "rb") as f:
        movies = pickle.load(f)
        if not isinstance(movies, pd.DataFrame):
            movies = pd.DataFrame(movies)
    with open("similarity.pkl", "rb") as f:
        similarity = pickle.load(f)
    movies["title_clean"] = movies["title"].str.strip().str.lower()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

st.set_page_config(page_title="🎬 Movie Recommender", layout="wide", page_icon="🎬")
st.markdown("<h1>🎬 Movie Recommendation System</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.2em; color: #ffffff; margin-bottom: 2rem;'>Discover your next favorite movie with AI-powered recommendations</p>", unsafe_allow_html=True)

# Enhanced Search & Filters
st.sidebar.markdown("### 🔍 Movie Search")
search_query = st.sidebar.text_input("Search for a movie:", placeholder="Type movie name...")

# Genre filter
all_genres = set()
for genres_list in movies['genres']:
    if isinstance(genres_list, list):
        all_genres.update(genres_list)
genre_filter = st.sidebar.selectbox("Filter by Genre:", ["All Genres"] + sorted(list(all_genres)))

# Rating filter
min_rating = st.sidebar.slider("Minimum Rating:", 0.0, 10.0, 0.0, 0.1)

# Apply filters
filtered_movies = movies.copy()
if genre_filter != "All Genres":
    filtered_movies = filtered_movies[filtered_movies['genres'].apply(lambda x: genre_filter in x if isinstance(x, list) else False)]
filtered_movies = filtered_movies[filtered_movies['vote_average'] >= min_rating]

# Search logic
selected_movie_name = None
if search_query:
    movie_titles = filtered_movies['title'].tolist()
    matches = get_close_matches(search_query, movie_titles, n=10, cutoff=0.3)
    if matches:
        selected_movie_name = st.sidebar.selectbox("Select from matches:", matches)
    else:
        st.sidebar.error("No movies found matching your search.")
else:
    if not filtered_movies.empty:
        selected_movie_name = st.sidebar.selectbox("Choose a movie:", filtered_movies['title'].values)

# User rating system
if selected_movie_name:
    user_rating = st.sidebar.slider(f"Rate '{selected_movie_name}':", 1, 5, 3)
    if st.sidebar.button("⭐ Save Rating"):
        if 'user_ratings' not in st.session_state:
            st.session_state.user_ratings = {}
        st.session_state.user_ratings[selected_movie_name] = user_rating
        st.sidebar.success(f"Rated {user_rating}/5 stars!")

st.sidebar.markdown("---")
st.sidebar.markdown("💡 **Tip:** Use search or filters to find movies!")

if st.sidebar.button("🎯 Get Recommendations", type="primary") and selected_movie_name:
    recommendations = recommend(selected_movie_name)

    if recommendations:
        selected_movie_data = movies[movies['title'] == selected_movie_name].iloc[0]
        
        st.markdown(f"<div class='movie-card'><h2 style='color: #2c3e50;'>🎬 Selected: {selected_movie_name}</h2></div>", unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 2])
        with col1:
            poster = fetch_poster(selected_movie_data.movie_id)
            if poster:
                st.image(poster, use_container_width=True)

        with col2:
            st.markdown(f"""
                <h3>{selected_movie_data.title}</h3>
                <p class="rating">⭐ {selected_movie_data.vote_average}/10</p>
                <p style="color:gray;">
                    📅 {selected_movie_data.release_date} | 
                    ⏳ {int(selected_movie_data.runtime)} min | 
                    🌍 {selected_movie_data.original_language.upper()}
                </p>
                <p>
                    <b>🎭 Genres:</b> {', '.join(selected_movie_data.genres) if isinstance(selected_movie_data.genres, list) else 'N/A'}<br>
                    <b>🎬 Director:</b> {', '.join(selected_movie_data.crew) if isinstance(selected_movie_data.crew, list) else 'N/A'}<br>
                    <b>👥 Cast:</b> {', '.join(selected_movie_data.cast[:3]) if isinstance(selected_movie_data.cast, list) else 'N/A'}
                </p>
            """, unsafe_allow_html=True)
            
            with st.expander("📖 Overview"):
                overview_text = ' '.join(selected_movie_data.overview) if isinstance(selected_movie_data.overview, list) else selected_movie_data.overview
                st.write(overview_text)

        # Show user ratings
        if 'user_ratings' in st.session_state and st.session_state.user_ratings:
            with st.expander("📊 Your Ratings"):
                for movie, rating in st.session_state.user_ratings.items():
                    st.write(f"⭐ {movie}: {rating}/5")

        st.markdown("### 🎯 Recommended Movies")
        
        for movie in recommendations:
            col1, col2 = st.columns([1, 2])
            with col1:
                if movie['poster']:
                    st.image(movie['poster'], use_container_width=True)
            with col2:
                st.markdown(f"""
                    <h4>{movie['title']}</h4>
                    <p class="rating">⭐ {movie['vote_average']}/10</p>
                    <p style="color:gray;">
                        📅 {movie['release_date']} | 
                        ⏳ {int(movie['runtime']) if movie['runtime'] else 'N/A'} min
                    </p>
                    <p>
                        <b>🎭 Genres:</b> {', '.join(movie['genres']) if isinstance(movie['genres'], list) else 'N/A'}<br>
                        <b>🎬 Director:</b> {', '.join(movie['crew']) if isinstance(movie['crew'], list) else 'N/A'}
                    </p>
                """, unsafe_allow_html=True)
                
                with st.expander("📖 Overview"):
                    overview_text = ' '.join(movie['overview']) if isinstance(movie['overview'], list) else movie['overview']
                    st.write(overview_text if overview_text else "No overview available.")
            
            st.markdown("---")
    else:
        st.error("No recommendations found.")
else:
    # Show popular movies
    st.markdown("### 🔥 Popular Movies")
    popular_movies = movies.nlargest(10, 'popularity')
    
    cols = st.columns(5)
    for idx, (_, movie) in enumerate(popular_movies.iterrows()):
        with cols[idx % 5]:
            poster = fetch_poster(movie['movie_id'])
            if poster:
                st.image(poster, use_container_width=True)
            st.write(f"**{movie['title']}**")
            st.write(f"⭐ {movie['vote_average']}/10")