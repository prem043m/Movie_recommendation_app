# 🎬 Movie Recommender System

An intelligent movie recommendation system built with Streamlit that suggests movies based on content similarity.

## Features

- **Smart Recommendations**: Content-based filtering using movie features
- **Interactive UI**: Clean, modern interface with emojis and intuitive design
- **Customizable**: Adjust number of recommendations (3-10)
- **Movie Details**: Get additional information about recommended movies
- **Error Handling**: Robust error handling for API calls and missing data
- **Performance**: Cached data loading for faster response times

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Generate similarity matrix (if not already present):
```bash
python generate_similarity.py
```

3. Run the app:
```bash
streamlit run app.py
```

## Files

- `app.py` - Main Streamlit application
- `generate_similarity.py` - Script to create similarity matrix
- `movies_dict.pkl` - Processed movie data
- `similarity.pkl` - Cosine similarity matrix
- `requirements.txt` - Python dependencies

## Usage

1. Select a movie you like from the dropdown
2. Adjust the number of recommendations in the sidebar
3. Click "Get Recommendations" to see similar movies
4. Click "Details" on any recommendation to learn more

## API

Uses The Movie Database (TMDb) API for movie posters and additional details.