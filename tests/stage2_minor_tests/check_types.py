import pandas as pd

from config.paths import RAW_DATA_DIR
from config.logging_config import setup_logging
from src.scripts.stage2_modules.stage2_clean_metadata import (
    repair_split_records,
    remove_duplicate_movies,
    fix_data_types,
)

setup_logging()

meta = pd.read_csv(RAW_DATA_DIR / "movies_metadata.csv", low_memory=False)
typed = fix_data_types(remove_duplicate_movies(repair_split_records(meta)))

print("\nRows:", len(typed))
print("\nData types:")
print(typed.dtypes)

print("\nadult:\n", typed["adult"].value_counts())
print("\nvideo:\n", typed["video"].value_counts())
print("\nstatus:\n", typed["status"].value_counts(dropna=False))

print("\nRelease dates from", typed["release_date"].min(), "to", typed["release_date"].max())
print("Missing release dates:", typed["release_date"].isna().sum())
print("Missing runtimes:", typed["runtime"].isna().sum())

# Run from the project root with: python -m tests.check_types