<<<<<<< HEAD

# Movie Recommendation App

Streamlit app that recommends similar movies using a precomputed similarity matrix.

## Features
- Movie search and filters
- Top recommendations with metadata
- Optional poster fetching from TMDB API
- Works locally and on Streamlit Cloud

## Run Locally
1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a local env file from template:

```bash
copy .env.example .env
```

4. Open `.env` and set your TMDB key:

```env
TMDB_API_KEY=your_tmdb_api_key_here
```

5. Start the app:

```bash
streamlit run app.py
```

## Deploy On Streamlit Cloud
1. Push this repository to GitHub.
2. In Streamlit Cloud, create a new app and select this repo.
3. Set main file path to `app.py`.
4. In App Settings -> Secrets, add:

```toml
TMDB_API_KEY = "your_tmdb_api_key_here"
```

5. Deploy.

## Secret Handling
- Local: app reads `.env` automatically.
- Cloud: app reads Streamlit Secrets (`st.secrets`).
- If no key is configured, the app still runs but poster images are disabled.

## Project Files
- `app.py`: main Streamlit app
- `movies_data.pkl`: processed movie data
- `similarity.pkl`: similarity matrix
- `.env.example`: local environment template
- `.streamlit/secrets.toml.example`: Streamlit secrets template
=======
glow
>>>>>>> fd27852 ( risk managed)
