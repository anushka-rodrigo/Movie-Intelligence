import pandas as pd

from config.paths import PROCESSED_DATA_DIR

movies = pd.read_csv(PROCESSED_DATA_DIR / "movies.csv", dtype=str)

for column in ["budget", "revenue", "runtime"]:
    with_decimal = movies[column].dropna().str.contains(r"\.", regex=True).sum()
    print(column, "values containing a decimal point:", with_decimal)

print(movies[["title", "budget", "revenue", "runtime"]].dropna().head(3))