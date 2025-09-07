import streamlit as st
import pandas as pd
import pickle
import requests


st.markdown("""
    <style>
        * {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        h1, h2, h3, h4, h5 {
            font-weight: 600;
        }
        p {
            font-size: 14px;
            line-height: 1.5;
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

st.set_page_config(page_title="🎬 Movie Recommender", layout="wide")
st.title("🎬 Movie Recommendation System")

selected_movie_name = st.sidebar.selectbox(
    "Search a movie:", movies['title'].values
)

if st.sidebar.button("Recommend"):
    recommendations = recommend(selected_movie_name)

    if recommendations:
        # Selected movie
        selected_movie_data = movies[movies['title'] == selected_movie_name].iloc[0]
        
        st.subheader(f"Selected Movie: **{selected_movie_name}**")
        col1, col2 = st.columns([1, 2])

        with col1:
            st.image(fetch_poster(selected_movie_data.movie_id), use_container_width=True)

        with col2:
            st.markdown(f"""
                <h3 style="margin:0;">{selected_movie_data.title}</h3>
                <p style="margin:5px 0; color:#555;">
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
        st.markdown("#### 📖 Overview")
        overview_text = ' '.join(selected_movie_data.overview) if isinstance(selected_movie_data.overview, list) else selected_movie_data.overview
        st.write(overview_text)

        # Homepage
        if pd.notna(selected_movie_data.homepage) and selected_movie_data.homepage != "":
            st.markdown(f"[🔗 Official Website]({selected_movie_data.homepage})", unsafe_allow_html=True)

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
                        <b>🎭 Genres:</b> {', '.join(movie['genres']) if isinstance(movie['genres'], list) and movie['genres'] else 'N/A'}<br>
                        <b>🎬 Director:</b> {', '.join(movie['crew']) if isinstance(movie['crew'], list) and movie['crew'] else 'N/A'}<br>
                        <b>👥 Cast:</b> {', '.join(movie['cast'][:3]) if isinstance(movie['cast'], list) and movie['cast'] else 'N/A'}<br>
                        <b>🔥 Popularity:</b> {round(movie['popularity'], 2) if movie['popularity'] else 'N/A'}<br>
                        <b>💰 Budget:</b> ${movie['budget']:,} <br>
                        <b>📌 Status:</b> {movie['status'] if movie['status'] else 'N/A'}
                    </p>
                """, unsafe_allow_html=True)

            # Overview
            st.markdown("#### 📖 Overview")
            overview_text = ' '.join(movie['overview']) if isinstance(movie['overview'], list) else movie['overview']
            st.write(overview_text if overview_text else "No overview available.")

            # Homepage
            if movie['homepage']:
                st.markdown(f"[🔗 Official Website]({movie['homepage']})", unsafe_allow_html=True)

            st.markdown("---")
    else:
        st.error("Sorry, couldn't find recommendations for this movie.")
