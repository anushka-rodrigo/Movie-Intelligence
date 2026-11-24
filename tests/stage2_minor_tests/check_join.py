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
from src.scripts.stage2_modules.stage2_join_tables import (
    build_safe_bridge,
    add_imdb_conflict_flag,
    link_ratings_to_movies,
)

setup_logging()

meta = pd.read_csv(RAW_DATA_DIR / "movies_metadata.csv", low_memory=False)
links = pd.read_csv(RAW_DATA_DIR / "links.csv")
ratings_raw = pd.read_csv(
    RAW_DATA_DIR / "ratings.csv",
    dtype={"userId": "int32", "movieId": "int32", "rating": "float32", "timestamp": "int32"},
)

movies = build_movies_table(clean_movies_metadata(meta))
movie_links = build_links_table(clean_links(links))
ratings = build_ratings_table(clean_ratings(ratings_raw))

safe_bridge, excluded = build_safe_bridge(movie_links, movies)
safe_bridge = add_imdb_conflict_flag(safe_bridge, movies)

print("\n=== Bridge ===")
print("movie_links:", len(movie_links), "| safe:", len(safe_bridge), "| excluded:", len(excluded))
print(excluded["exclusion_reason"].value_counts().to_string())
print("Safe bridge movie_id unique:", safe_bridge["movie_id"].is_unique)

# Reproduce Stage 1: every row that reaches metadata, shared or not (C12 not yet applied)
stage1_bridge = movie_links[movie_links["movie_id"].isin(movies["movie_id"])]
print("\n=== Joining ratings WITHOUT the C12 exclusion (Stage 1 figure) ===")
print(link_ratings_to_movies(ratings, stage1_bridge))

print("\n=== Joining ratings through the safe bridge ===")
print(link_ratings_to_movies(ratings, safe_bridge))

print("\n=== imdb_conflict ===")
print("Flagged:", safe_bridge["imdb_conflict"].sum())

metadata_imdb = movies.set_index("movie_id")["imdb_id"]
flagged = safe_bridge[safe_bridge["imdb_conflict"]].copy()
flagged["metadata_imdb_id"] = flagged["movie_id"].map(metadata_imdb)
genuine = flagged[flagged["metadata_imdb_id"].isin(movie_links["imdb_id"])]
print("Conflicts where the metadata id belongs to another movie in links:", len(genuine))
print(genuine[["movielens_id", "movie_id", "imdb_id", "metadata_imdb_id"]].to_string(index=False))

# Run from the project root with: python -m tests.check_join