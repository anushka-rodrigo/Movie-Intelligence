import pandas as pd

from config.paths import RAW_DATA_DIR
from config.logging_config import setup_logging
from src.scripts.stage2_modules.stage2_clean_metadata import clean_movies_metadata
from src.scripts.stage2_modules.stage2_clean_links import clean_links
from src.scripts.stage2_modules.stage2_clean_ratings import clean_ratings
from src.scripts.stage2_modules.stage2_build_tables import (
    build_movies_table,
    build_links_table,
    build_ratings_table,
)

setup_logging()

meta = pd.read_csv(RAW_DATA_DIR / "movies_metadata.csv", low_memory=False)
links = pd.read_csv(RAW_DATA_DIR / "links.csv")
ratings = pd.read_csv(
    RAW_DATA_DIR / "ratings.csv",
    dtype={"userId": "int32", "movieId": "int32", "rating": "float32", "timestamp": "int32"},
)

movies = build_movies_table(clean_movies_metadata(meta))
movie_links = build_links_table(clean_links(links))
ratings_table = build_ratings_table(clean_ratings(ratings))

print("\n=== movies ===")
print("Rows:", len(movies), "| columns:", movies.shape[1])
print(movies.columns.tolist())
print("Movies in a collection:", movies["collection_id"].notna().sum())
print(movies[movies["movie_id"] == 862][["movie_id", "title", "collection_id", "collection_name"]].to_string(index=False))

print("\n=== movie_links ===")
print("Rows:", len(movie_links))
print(movie_links.columns.tolist())
print(movie_links.head(1).to_string(index=False))

print("\n=== ratings ===")
print("Rows:", len(ratings_table))
print(ratings_table.columns.tolist())

# Run from the project root with: python -m tests.check_core_tables