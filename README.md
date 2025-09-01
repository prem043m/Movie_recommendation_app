
# 🎬 Movie Recommender System (Streamlit App)

A simple **Movie Recommendation System** built with **Streamlit**, **Pandas**, and **Pickle**.  
This app suggests movies similar to a selected movie based on precomputed similarity scores.

---

## 🚀 Features
- Select a movie from a dropdown list
- Get **top 5 recommended movies** based on similarity
- Display:
  - 🎥 Title  
  - 📝 Overview  
  - 🎭 Genres  
  - 👨‍👩‍👧 Cast  
  - 🎬 Crew/Director  

---

## 🛠️ Tech Stack
- [Python](https://www.python.org/)  
- [Streamlit](https://streamlit.io/)  
- [Pandas](https://pandas.pydata.org/)  
- [Pickle](https://docs.python.org/3/library/pickle.html)  

---

## 📂 Project Structure

MoviesRecomendationTactic/
│── movies_data.pkl        # Pickled movie dataset (title, overview, genres, cast, crew)
│── similarity.pkl         # Pickled similarity matrix
│── app.py                 # Main Streamlit app
│── README.md              # Project documentation
