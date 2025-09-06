import streamlit as st
import pickle
import pandas as pd
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# key = os.getenv("TMDB_API_KEY")
key = st.secrets("TMDB_API_KEY")


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
        movie_matches = movies[movies['title'] == movie]
        if movie_matches.empty:
            return []

        movie_index = movie_matches.index[0]
        distances = similarity[movie_index]
        movies_list = sorted(
            list(enumerate(distances)),
            reverse=True,
            key=lambda x: x[1]
        )[1:6]

        recommended_movies = []
        for i in movies_list:
            movie_data = movies.iloc[i[0]]
            recommended_movies.append({
                'title': movie_data.title,
                'overview': movie_data.overview,
                'genres': movie_data.genres,
                'cast': movie_data.cast,
                'crew': movie_data.crew,
                'keywords': movie_data.keywords,
                'poster': fetch_poster(movie_data.movie_id),
            })
        return recommended_movies
    except (IndexError, KeyError):
        return []

try:
    with open('movies_data.pkl', 'rb') as f:
        movies_data = pickle.load(f)
    movies = pd.DataFrame(movies_data)

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
st.markdown("This system analyzes movie genres, cast, crew, keywords, and plot to find similar movies.")

st.sidebar.header("🔍 Find Recommendations")
st.sidebar.markdown("Select a movie to get personalized recommendations based on content similarity.")
selected_movie_name = st.sidebar.selectbox(
    "Choose a movie",
    movies['title'].values
)

# Display selected movie details
if selected_movie_name:
    selected_movie_data = movies[movies['title'] == selected_movie_name].iloc[0]
    
    st.sidebar.markdown("### Selected Movie Details")
    st.sidebar.write(f"**Genres:** {', '.join(selected_movie_data.genres) if isinstance(selected_movie_data.genres, list) else selected_movie_data.genres}")
    st.sidebar.write(f"**Director:** {', '.join(selected_movie_data.crew) if isinstance(selected_movie_data.crew, list) else selected_movie_data.crew}")
    st.sidebar.write(f"**Cast:** {', '.join(selected_movie_data.cast[:3]) if isinstance(selected_movie_data.cast, list) else selected_movie_data.cast}")

if st.sidebar.button("Recommend"):
    recommendations = recommend(selected_movie_name)

    if recommendations:
        # Display selected movie
        selected_movie_data = movies[movies['title'] == selected_movie_name].iloc[0]
        
        st.subheader(f"Selected Movie: **{selected_movie_name}**")
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.image(fetch_poster(selected_movie_data.movie_id), width=200)
        
        with col2:
            st.write(f"**Genres:** {', '.join(selected_movie_data.genres) if isinstance(selected_movie_data.genres, list) else selected_movie_data.genres}")
            st.write(f"**Director:** {', '.join(selected_movie_data.crew) if isinstance(selected_movie_data.crew, list) else selected_movie_data.crew}")
            st.write(f"**Cast:** {', '.join(selected_movie_data.cast) if isinstance(selected_movie_data.cast, list) else selected_movie_data.cast}")
            st.write(f"**Keywords:** {', '.join(selected_movie_data.keywords[:5]) if isinstance(selected_movie_data.keywords, list) else selected_movie_data.keywords}")
            
            with st.expander("Overview"):
                overview_text = ' '.join(selected_movie_data.overview) if isinstance(selected_movie_data.overview, list) else selected_movie_data.overview
                st.write(overview_text)
        
        st.write("---")
        st.subheader(f"Because you watched **{selected_movie_name}**, you might also like:")
        st.write("---")

        for i, movie in enumerate(recommendations, 1):
            col1, col2 = st.columns([1, 3])

            with col1:
                st.image(movie['poster'], width=200)

            with col2:
                st.markdown(f"### {i}. {movie['title']}")
                st.write(f"**Genres:** {', '.join(movie['genres']) if isinstance(movie['genres'], list) else movie['genres']}")
                st.write(f"**Director:** {', '.join(movie['crew']) if isinstance(movie['crew'], list) else movie['crew']}")
                st.write(f"**Cast:** {', '.join(movie['cast']) if isinstance(movie['cast'], list) else movie['cast']}")
                st.write(f"**Keywords:** {', '.join(movie['keywords'][:5]) if isinstance(movie['keywords'], list) else movie['keywords']}")

                with st.expander("Overview"):
                    overview_text = ' '.join(movie['overview']) if isinstance(movie['overview'], list) else movie['overview']
                    st.write(overview_text)

            st.markdown("---")
    else:
        st.error("Sorry, couldn't find recommendations for this movie.")
