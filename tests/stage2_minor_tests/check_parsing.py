import pandas as pd

from config.paths import RAW_DATA_DIR
from config.logging_config import setup_logging
from src.scripts.stage2_modules.stage2_clean_metadata import clean_movies_metadata

setup_logging()

meta = pd.read_csv(RAW_DATA_DIR / "movies_metadata.csv", low_memory=False)
clean = clean_movies_metadata(meta)

print("\nRows:", len(clean))

print("\nEmpty lists (unknown):")
for column in ["genres", "production_companies", "production_countries", "spoken_languages"]:
    empty = clean[column].apply(lambda value: value == []).sum()
    print(f"  {column}: {empty}")

in_collection = clean["belongs_to_collection"].notna().sum()
print("\nMovies in a collection:", in_collection)

toy_story = clean[clean["id"] == 862].iloc[0]
print("\nToy Story genres:", toy_story["genres"])
print("Toy Story collection:", toy_story["belongs_to_collection"]["name"])

# Run from the project root with: python -m tests.check_parsing