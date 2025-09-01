import streamlit as st 
import pickle
import pandas as pd
import requests


def Fetch_poster(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=6f252fb3bf3a0133ad6cc719b630a8f8&language=en-US"
    response = requests.get(url)
    data = response.json()
    print(data)
    return "https://image.tmdb.org/t/p/w500" + data['poster_path']


def recommend(movie):
    movie_index = movies[movies['title']== movie].index[0]
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]
    
    recommended_movies = []
    recommended_movies_poster = []
    for i in movies_list:
        movies_id = movies.iloc[i[0]].movie_id
        recommended_movies.append(movies.iloc[i[0]].title)
        # fetch poster from API : 6f252fb3bf3a0133ad6cc719b630a8f8
        recommended_movies_poster.append(Fetch_poster(movies_id))
    return recommended_movies,recommended_movies_poster

movies_dict = pickle.load(open('movies_dict.pkl','rb'))
movies = pd.DataFrame(movies_dict)

similarity = pickle.load(open('similarity.pkl','rb'))

st.title("Movie Recommender System")

selected_movie_name = st.selectbox(
'What brings you here ?',
movies['title'].values
)

if st.button('recommend'):
    names,posters = recommend(selected_movie_name)
    
    cols = st.columns(5)
    for i, col in enumerate(cols):
        with col:
            st.text(names[i])
            st.image(posters[i])
    
