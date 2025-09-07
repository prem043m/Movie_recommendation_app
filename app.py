import streamlit as st
import pandas as pd
import pickle
import requests


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
            color: #2c3e50;
            text-align: center;
            font-size: 3rem;
            margin-bottom: 2rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
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

api_key = st.secrets["TMDB_API_KEY"]

def fetch_poster(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
    response = requests.get(url)
    data = response.json()
    return "https://image.tmdb.org/t/p/w500" + data['poster_path'] if data.get("poster_path") else None

def recommend(movie):
    try:
        # Normalize the input (ignore case and spaces)
        movie = movie.strip().lower()

        # Make a clean version of titles
        movies['title_clean'] = movies['title'].str.strip().str.lower()

        # Find the movie
        movie_matches = movies[movies['title_clean'] == movie]
        if movie_matches.empty:
            return []  # No match found

        movie_index = movie_matches.index[0]

        # Get similarity scores
        distances = similarity[movie_index]

        # Sort movies by similarity
        movies_list = sorted(
            list(enumerate(distances)),
            reverse=True,
            key=lambda x: x[1]
        )[1:6]  # Top 5 recommendations

        # Build recommendations
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


try:
    with open("movies_data.pkl", "rb") as f:
        movies = pickle.load(f)
        if not isinstance(movies, pd.DataFrame):
            movies = pd.DataFrame(movies)

    with open("similarity.pkl", "rb") as f:
        similarity = pickle.load(f)

    # Pre-clean title column for matching
    movies["title_clean"] = movies["title"].str.strip().str.lower()

except FileNotFoundError as e:
    st.error(f"Required file missing: {e}")
    st.stop()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

st.set_page_config(page_title="🎬 Movie Recommender", layout="wide", page_icon="🎬")
st.markdown("<h1>🎬 Movie Recommendation System</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.2em; color: #7f8c8d; margin-bottom: 2rem;'>Discover your next favorite movie with AI-powered recommendations</p>", unsafe_allow_html=True)

st.sidebar.markdown("### 🔍 Movie Search")
selected_movie_name = st.sidebar.selectbox(
    "Choose a movie to get recommendations:", movies['title'].values
)
st.sidebar.markdown("---")
st.sidebar.markdown("💡 **Tip:** Select any movie and click 'Get Recommendations' to discover similar films!")

if st.sidebar.button("🎯 Get Recommendations", type="primary"):
    recommendations = recommend(selected_movie_name)

    if recommendations:
        # Selected movie
        selected_movie_data = movies[movies['title'] == selected_movie_name].iloc[0]
        
        st.markdown(f"<div class='movie-card'><h2 style='color: #2c3e50; margin-bottom: 1rem;'>🎬 Selected Movie: {selected_movie_name}</h2></div>", unsafe_allow_html=True)
        col1, col2 = st.columns([1, 2])

        with col1:
            st.image(fetch_poster(selected_movie_data.movie_id), use_container_width=True)

        with col2:
            st.markdown(f"""
                <h3 style="margin:0;">{selected_movie_data.title}</h3>
                <p style="margin:5px 0;" class="rating">
                    ⭐ {selected_movie_data.vote_average}/10
                </p>
                <p style="margin:0; color:gray;">
                    📅 {selected_movie_data.release_date} &nbsp;&nbsp; | &nbsp;&nbsp; 
                    ⏳ {int(selected_movie_data.runtime)} min &nbsp;&nbsp; | &nbsp;&nbsp;
                    🌍 {selected_movie_data.original_language.upper()}
                </p>
                <hr style="margin:10px 0;">
                <p>
                    <b>🎭 Genres:</b> {', '.join(selected_movie_data.genres) if isinstance(selected_movie_data.genres, list) else 'N/A'}<br>
                    <b>🎬 Director:</b> {', '.join(selected_movie_data.crew) if isinstance(selected_movie_data.crew, list) else 'N/A'}<br>
                    <b>👥 Cast:</b> {', '.join(selected_movie_data.cast[:3]) if isinstance(selected_movie_data.cast, list) else 'N/A'}<br>
                    <b>🔥 Popularity:</b> {round(selected_movie_data.popularity, 2)}<br>
                    <b>💰 Budget:</b> ${selected_movie_data.budget:,}<br>
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

        st.markdown("<div style='margin: 3rem 0 2rem 0;'><h2 style='color: #2c3e50; text-align: center;'>🎯 Movies You Might Love</h2><p style='text-align: center; color: #7f8c8d;'>Based on your selection, here are our top recommendations:</p></div>", unsafe_allow_html=True)

        # Recommended movies
        for i, movie in enumerate(recommendations, 1):
            col1, col2 = st.columns([1, 2])

            with col1:
                st.image(movie['poster'], use_container_width=True)

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

            st.markdown("<div style='margin: 2rem 0; border-bottom: 2px solid #ecf0f1;'></div>", unsafe_allow_html=True)
    else:
        st.error("Sorry, couldn't find recommendations for this movie.")
