import pandas as pd

from config.paths import RAW_DATA_DIR
from config.logging_config import setup_logging
from src.scripts.stage2_modules.stage2_clean_metadata import clean_movies_metadata
from src.scripts.stage2_modules.stage2_build_tables import build_genre_tables

setup_logging()

meta = pd.read_csv(RAW_DATA_DIR / "movies_metadata.csv", low_memory=False)
clean = clean_movies_metadata(meta)
genres, movie_genres = build_genre_tables(clean)

print("\nGenres table:", len(genres), "rows")
print(genres.to_string(index=False))

print("\nmovie_genres:", len(movie_genres), "rows")
print("Movies with at least one genre:", movie_genres["movie_id"].nunique())
print("\nData types:")
print(movie_genres.dtypes)

print("\nToy Story:")
print(movie_genres[movie_genres["movie_id"] == 862].merge(genres, on="genre_id"))

print("\nMovies per genre, top 5:")
counts = movie_genres.merge(genres, on="genre_id").groupby("genre_name").size()
print(counts.sort_values(ascending=False).head(5))

# Run from the project root with: python -m tests.check_genres