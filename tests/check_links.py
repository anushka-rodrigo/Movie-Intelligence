import pandas as pd

from config.paths import RAW_DATA_DIR
from config.logging_config import setup_logging
from src.scripts.stage2_modules.stage2_clean_links import clean_links

setup_logging()

links = pd.read_csv(RAW_DATA_DIR / "links.csv")
clean = clean_links(links)

print("\nRows before:", len(links), "| after:", len(clean))
print("\nData types:")
print(clean.dtypes)

print("\nFirst row (Toy Story):")
print(clean.head(1))

print("\nRows flagged shared_tmdb_id:", clean["shared_tmdb_id"].sum())
print(clean[clean["shared_tmdb_id"]].sort_values("tmdbId").head(6))

print("\nmovieId unique:", clean["movieId"].is_unique)

# Run from the project root with: python -m tests.check_links