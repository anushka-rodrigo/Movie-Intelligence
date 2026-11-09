import pandas as pd

from config.paths import RAW_DATA_DIR
from config.logging_config import setup_logging
from src.scripts.stage2_modules.stage2_clean_metadata import repair_split_records

setup_logging()

meta = pd.read_csv(RAW_DATA_DIR / "movies_metadata.csv", low_memory=False)
fixed = repair_split_records(meta)

print("\nRows before:", len(meta), "| after:", len(fixed))

# Midnight Man: your Stage 1 output shows what its values should be
row = fixed[fixed["id"] == "82663"].iloc[0]
print("title:       ", row["title"])
print("release_date:", row["release_date"])
print("runtime:     ", row["runtime"])
print("vote_count:  ", row["vote_count"])
print("overview ends:", repr(row["overview"][-60:]))

print("\nMissing titles left:", fixed["title"].isna().sum())

# Run from the project root with: python -m tests.check_repair