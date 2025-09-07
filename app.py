import streamlit as st
import pickle
import pandas as pd
import requests
import os
from dotenv import load_dotenv

st.markdown("""
    <style>
        * {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        h1, h2, h3, h4, h5 {
            font-weight: 600;
        }
        p {
            font-size: 15px;
            line-height: 1.6;
        }
    </style>
""", unsafe_allow_html=True)

load_dotenv()

# key = os.getenv("TMDB_API_KEY")
key = st.secrets["TMDB_API_KEY"]


def fetch_poster(movie_id):
    try:
        api_key = key 
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        poster_path = data.get('poster_path')
        if poster_path:
            return f"https://image.tmdb.org/t/p/w500{poster_path}"
        return "https://via.placeholder.com/500x750?text=No+Image"
    except (requests.RequestException, KeyError, ValueError):
        return "https://via.placeholder.com/500x750?text=No+Image"

def recommend(movie):
    try:
        movie = movie.strip().lower()
        movies['title_clean'] = movies['title'].str.strip().str.lower()
        
        movie_matches = movies[movies['title_clean'] == movie]
        
        if movie_matches.empty:
            return []

        movie_index = movie_matches.index[0]
        
        distances = similarity[movie_index]
        movies_list = sorted(
            list(enumerate(distances)), reverse=True, key=lambda x: x[1]
        )[1:6]  # top 5 movies

        recommendations = []
        for i in movies_list:
            movie_data = movies.iloc[i[0]]
            recommendations.append({
                'title': movie_data['title'],
                'overview': movie_data.get('overview', ''),
                'genres': movie_data.get('genres', []),
                'cast': movie_data.get('cast', []),
                'crew': movie_data.get('crew', []),
                'keywords': movie_data.get('keywords', []),
                'poster': fetch_poster(movie_data.get('movie_id', 0)),
                'popularity': movie_data.get('popularity', 0),
                'budget': movie_data.get('budget', 0),
                'homepage': movie_data.get('homepage', ''),
                'release_date': movie_data.get('release_date', ''),
                'runtime': movie_data.get('runtime', 0),
                'status': movie_data.get('status', ''),
                'original_language': movie_data.get('original_language', ''),
                'vote_average': movie_data.get('vote_average', 0)
            })
        return recommendations
    except Exception as e:
        st.error(f"Error in recommendation: {e}")
        return []

try:
    with open('movies_data.pkl', 'rb') as f:
        movies = pickle.load(f)
    
    with open('similarity.pkl', 'rb') as f:
        similarity = pickle.load(f)
except FileNotFoundError as e:
    st.error(f"Required data files not found: {e}")
    st.stop()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

st.set_page_config(page_title="🎬 Movie Recommender", layout="wide")

st.title("🎬 Movie Recommender System")
st.markdown("### Discover movies similar to your favorite picks!")

st.sidebar.header("🔍 Find Recommendations")
st.sidebar.markdown("Select a movie to get personalized recommendations based on content similarity.")
selected_movie_name = st.sidebar.selectbox(
    "Choose a movie",
    movies['title'].values
)

# Display selected movie details
if st.sidebar.button("Recommend"):
    recommendations = recommend(selected_movie_name)

    if recommendations:
        # Selected movie
        selected_movie_data = movies[movies['title'] == selected_movie_name].iloc[0]
        
        st.subheader(f"Selected Movie: **{selected_movie_name}**")
        col1, col2 = st.columns([1, 2])

        with col1:
            st.image(fetch_poster(selected_movie_data.get('movie_id', 0)), use_container_width=True)

        with col2:
            st.markdown(f"""
                <h3 style="margin:0;">{selected_movie_data['title']}</h3>
                <p style="margin:5px 0; color:#555;">
                    ⭐ {selected_movie_data.get('vote_average', 0)}/10
                </p>
                <p style="margin:0; color:gray;">
                    📅 {selected_movie_data.get('release_date', 'N/A')} &nbsp;&nbsp; | &nbsp;&nbsp; 
                    ⏳ {int(selected_movie_data.get('runtime', 0)) if selected_movie_data.get('runtime') else 'N/A'} min &nbsp;&nbsp; | &nbsp;&nbsp;
                    🌍 {selected_movie_data.get('original_language', 'N/A').upper()}
                </p>
                <hr style="margin:10px 0;">
                <p>
                    <b>🎭 Genres:</b> {', '.join(selected_movie_data.get('genres', []))}<br>
                    <b>🎬 Director:</b> {', '.join(selected_movie_data.get('crew', []))}<br>
                    <b>👥 Cast:</b> {', '.join(selected_movie_data.get('cast', [])[:5])}<br>
                    <b>🔥 Popularity:</b> {round(selected_movie_data.get('popularity', 0), 2)}<br>
                    <b>💰 Budget:</b> ${selected_movie_data.get('budget', 0):,}<br>
                    <b>📌 Status:</b> {selected_movie_data.get('status', 'N/A')}
                </p>
            """, unsafe_allow_html=True)
            # Overview section
            # Expander for overview
            with st.expander("📖 Overview"):
                overview_text = ' '.join(selected_movie_data.get('overview', [])) if isinstance(selected_movie_data.get('overview'), list) else selected_movie_data.get('overview', 'No overview available.')
                st.write(overview_text)
        
            # Homepage link
            homepage = selected_movie_data.get('homepage', '')
            if homepage and homepage != "":
                st.markdown(f"[🔗 Official Website]({homepage})", unsafe_allow_html=True)

        st.markdown("### 🎯 Recommended Movies")
        st.markdown("Here are some movies similar to your selection:")

        # Recommended movies
        for i, movie in enumerate(recommendations, 1):
            col1, col2 = st.columns([1, 2])

            with col1:
                st.image(movie['poster'], use_container_width=True)

            with col2:
                st.markdown(f"""
                    <h3 style="margin:0;">{movie['title']}</h3>
                    <p style="margin:5px 0; color:#555;">
                        ⭐ {movie['vote_average']}/10
                    </p>
                    <p style="margin:0; color:gray;">
                        📅 {movie['release_date']} &nbsp;&nbsp; | &nbsp;&nbsp; 
                        ⏳ {int(movie['runtime']) if movie['runtime'] else 'N/A'} min &nbsp;&nbsp; | &nbsp;&nbsp;
                        🌍 {movie['original_language'].upper() if movie['original_language'] else 'N/A'}
                    </p>
                    <hr style="margin:10px 0;">
                    <p>
                        <b>🎭 Genres:</b> {', '.join(movie['genres']) if movie['genres'] else 'N/A'}<br>
                        <b>🎬 Director:</b> {', '.join(movie['crew']) if movie['crew'] else 'N/A'}<br>
                        <b>👥 Cast:</b> {', '.join(movie['cast'][:5]) if movie['cast'] else 'N/A'}<br>
                        <b>🔥 Popularity:</b> {round(movie['popularity'], 2) if movie['popularity'] else 'N/A'}<br>
                        <b>💰 Budget:</b> ${movie['budget']:,} <br>
                        <b>📌 Status:</b> {movie['status'] if movie['status'] else 'N/A'}
                    </p>
                """, unsafe_allow_html=True)

                # Expander for overview
                with st.expander("📖 Overview"):
                    overview_text = ' '.join(movie['overview']) if isinstance(movie['overview'], list) else movie['overview']
                    st.write(overview_text if overview_text else "No overview available.")
            
                # Homepage
                if movie['homepage']:
                    st.markdown(f"[🔗 Official Website]({movie['homepage']})", unsafe_allow_html=True)

            st.markdown("---")
    else:
        st.error("Sorry, couldn't find recommendations for this movie.")