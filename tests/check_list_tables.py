import pandas as pd

from config.paths import RAW_DATA_DIR
from config.logging_config import setup_logging
from src.scripts.stage2_modules.stage2_clean_metadata import clean_movies_metadata
from src.scripts.stage2_modules.stage2_build_tables import (
    build_genre_tables,
    build_company_tables,
    build_country_tables,
    build_language_tables,
)

setup_logging()

meta = pd.read_csv(RAW_DATA_DIR / "movies_metadata.csv", low_memory=False)
clean = clean_movies_metadata(meta)

jobs = [
    ("genres", build_genre_tables, "genres"),
    ("production_companies", build_company_tables, "production_companies"),
    ("production_countries", build_country_tables, "production_countries"),
    ("spoken_languages", build_language_tables, "spoken_languages"),
]

for label, builder, column in jobs:
    lookup, link = builder(clean)

    empty = clean[column].apply(lambda v: len(v) == 0).sum()
    expected_movies = len(clean) - empty
    got_movies = link["movie_id"].nunique()

    print(f"\n=== {label} ===")
    print("Lookup rows:", len(lookup), "| Link rows:", len(link))
    print("Movies with at least one entry:", got_movies, "| expected:", expected_movies,
          "| OK" if got_movies == expected_movies else "| MISMATCH")

    key, name = lookup.columns
    top = (
        link.merge(lookup, on=key)
        .groupby(name)
        .size()
        .sort_values(ascending=False)
        .head(3)
    )
    print("Most common:")
    print(top.to_string())

# Run from the project root with: python -m tests.check_list_tables