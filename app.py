import streamlit as st
import pickle
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

key = st.secrets["tmdb_api_key"]

def fetch_poster(movie_id):
    api_key = key 
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
    response = requests.get(url)
    data = response.json()
    poster_path = data.get('poster_path')
    if poster_path:
        return f"https://image.tmdb.org/t/p/w500{poster_path}"
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
                'poster': fetch_poster(movie_data.movie_id),
            })
        return recommended_movies
    except (IndexError, KeyError):
        return []

with open('movies_data.pkl', 'rb') as f:
    movies_data = pickle.load(f)
movies = pd.DataFrame(movies_data)

with open('similarity.pkl', 'rb') as f:
    similarity = pickle.load(f)

st.set_page_config(page_title=" Movie Recommender ", layout="wide")

st.title("Movie Recommender System")
st.markdown("Discover movies similar to your favorite picks!")

st.sidebar.header(" Find Recommendations")
selected_movie_name = st.sidebar.selectbox(
    "Choose a movie",
    movies['title'].values
)

if st.sidebar.button("Recommend"):
    recommendations = recommend(selected_movie_name)

    if recommendations:
        st.subheader(f"Because you watched **{selected_movie_name}**...")
        st.write("---")

        for i, movie in enumerate(recommendations, 1):
            col1, col2 = st.columns([1, 3])

            with col1:
                st.image(movie['poster'], width=200)

            with col2:
                st.markdown(f"### {i}. {movie['title']}")
                st.write(f"**Genres:** {movie['genres']}")
                st.write(f"**Director:** {movie['crew']}")
                st.write(f"**Cast:** {movie['cast']}")

                with st.expander("Overview"):
                    st.write(movie['overview'])


            st.markdown("---")
    else:
        st.error("Sorry, couldn't find recommendations for this movie.")
