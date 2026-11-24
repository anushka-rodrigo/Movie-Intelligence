import pandas as pd

from config.paths import RAW_DATA_DIR
from config.logging_config import setup_logging
from src.scripts.stage2_modules.stage2_clean_ratings import clean_ratings

setup_logging()

ratings = pd.read_csv(
    RAW_DATA_DIR / "ratings.csv",
    dtype={
        "userId": "int32",
        "movieId": "int32",
        "rating": "float32",
        "timestamp": "int32",
    },
)
memory_before = ratings.memory_usage(deep=True).sum() / 1e6

clean = clean_ratings(ratings)
memory_after = clean.memory_usage(deep=True).sum() / 1e6

print("\nRows before:", len(ratings), "| after:", len(clean))
print("\nData types:")
print(clean.dtypes)

print("\nFirst 3 rows:")
print(clean.head(3))

print("\nRating distribution:")
print(clean["rating"].value_counts().sort_index())

print(f"\nMemory: {memory_before:.0f} MB -> {memory_after:.0f} MB")

# Run from the project root with: python -m tests.check_ratings