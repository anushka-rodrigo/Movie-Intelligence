import pandas as pd

from config.paths import RAW_DATA_DIR

meta = pd.read_csv(RAW_DATA_DIR / "movies_metadata.csv", low_memory=False)

ids = meta["imdb_id"].dropna().astype(str)
odd = ids[~ids.str.match(r"^tt\d+$")]

print("imdb_id values that are not 'tt' + digits:", len(odd))
print(odd.value_counts().head(10))

# Run from the project root with: python -m tests.check_imdb