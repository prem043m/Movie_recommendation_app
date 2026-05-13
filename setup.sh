mkdir -p ~/.streamlit/

echo "\
[server]\n\
port = $PORT\n\
# Enable CORS by default for safer behavior. Set DISABLE_CORS=1 to override.\n\
enableCORS = true\n\
headless = true\n\
\n\
" > ~/.streamlit/config.toml