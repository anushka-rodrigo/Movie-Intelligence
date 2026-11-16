import pandas as pd

from config.paths import RAW_DATA_DIR
from config.logging_config import setup_logging
from src.scripts.stage2_modules.stage2_clean_keywords import clean_keywords
from src.scripts.stage2_modules.stage2_build_tables import build_keyword_tables

setup_logging()

keywords = pd.read_csv(RAW_DATA_DIR / "keywords.csv")
clean = clean_keywords(keywords)
lookup, link = build_keyword_tables(clean)

empty = clean["keywords"].apply(lambda v: len(v) == 0).sum()
expected_movies = len(clean) - empty
got_movies = link["movie_id"].nunique()

print("\n=== keywords ===")
print("Lookup rows:", len(lookup), "| Link rows:", len(link))
print(
    "Movies with at least one keyword:", got_movies,
    "| expected:", expected_movies,
    "| OK" if got_movies == expected_movies else "| MISMATCH",
)

print("\nMost common keywords:")
top = (
    link.merge(lookup, on="keyword_id")
    .groupby("keyword_name")
    .size()
    .sort_values(ascending=False)
    .head(5)
)
print(top.to_string())

toy_story = link[link["movie_id"] == 862].merge(lookup, on="keyword_id")
print("\nToy Story keywords:", toy_story["keyword_name"].tolist())

# Run from the project root with: python -m tests.check_keyword_tables