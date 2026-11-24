import pandas as pd

from config.paths import RAW_DATA_DIR
from config.logging_config import setup_logging
from src.scripts.stage2_modules.stage2_clean_metadata import (
    repair_split_records,
    remove_duplicate_movies,
)

setup_logging()

meta = pd.read_csv(RAW_DATA_DIR / "movies_metadata.csv", low_memory=False)
repaired = repair_split_records(meta)
deduped = remove_duplicate_movies(repaired)

print("\nRows after repair:", len(repaired), "| after de-duplication:", len(deduped))
print("Ids unique:", not deduped["id"].duplicated().any())

# The two ids where the copies had different vote_counts
for movie_id in ["10991", "15028"]:
    print(f"\nId {movie_id} before:")
    print(repaired.loc[repaired["id"] == movie_id, ["id", "title", "vote_count", "popularity"]])
    print(f"Id {movie_id} after:")
    print(deduped.loc[deduped["id"] == movie_id, ["id", "title", "vote_count", "popularity"]])

# Run from the project root with: python -m tests.check_duplicates