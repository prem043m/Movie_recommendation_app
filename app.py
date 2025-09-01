import streamlit as st 
import pickle
import pandas as pd

def recommend(movie):
    """Recommend movies based on similarity with error handling."""
    try:
        movie_matches = movies[movies['title'] == movie]
        if movie_matches.empty:
            return []
            
        movie_index = movie_matches.index[0]
        distances = similarity[movie_index]
        movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]
        
        recommended_movies = []
        for i in movies_list:
            movie_data = movies.iloc[i[0]]
            recommended_movies.append({
                'title': movie_data.title,
                'overview': movie_data.overview,
                'genres': movie_data.genres,
                'cast': movie_data.cast,
                'crew': movie_data.crew
            })
        return recommended_movies
    except (IndexError, KeyError):
        return []


# Load data with proper resource management
with open('movies_data.pkl', 'rb') as f:
    movies_data = pickle.load(f)
movies = pd.DataFrame(movies_data)

with open('similarity.pkl', 'rb') as f:
    similarity = pickle.load(f)

st.title("Movie Recommender System")

selected_movie_name = st.selectbox(
    'What brings you here?',
    movies['title'].values
)

if st.button('Recommend'):
    recommendations = recommend(selected_movie_name)
    
    if recommendations:
        st.subheader("Recommended Movies:")
        for i, movie in enumerate(recommendations, 1):
            st.markdown(f"### {i}. {movie['title']}")
            st.write(f"**Genres:** {movie['genres']}")
            st.write(f"**Director:** {movie['crew']}")
            st.write(f"**Cast:** {movie['cast']}")
            st.write(f"**Overview:** {movie['overview']}")
            st.markdown("---")
    else:
        st.error("Sorry, couldn't find recommendations for this movie.")
    