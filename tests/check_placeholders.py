import pandas as pd

from config.paths import RAW_DATA_DIR
from config.logging_config import setup_logging
from src.scripts.stage2_modules.stage2_clean_metadata import clean_movies_metadata

setup_logging()

meta = pd.read_csv(RAW_DATA_DIR / "movies_metadata.csv", low_memory=False)
clean = clean_movies_metadata(meta)

print("\nRows:", len(clean))

print("\nFlag counts:")
for flag in ["budget_review", "revenue_review", "long_runtime", "vote_average_zero_with_votes"]:
    print(f"  {flag}: {clean[flag].sum()}")

print("\nSmallest remaining budget:", clean["budget"].min())
print("Smallest remaining revenue:", clean["revenue"].min())
print("Smallest remaining runtime:", clean["runtime"].min())
print("Smallest remaining vote_average:", clean["vote_average"].min())

usable = clean["budget"].notna() & clean["revenue"].notna()
print("\nMovies with both budget and revenue:", usable.sum())

print("\nvote_count zeros kept:", (clean["vote_count"] == 0).sum())

# Run from the project root with: python -m tests.check_placeholders