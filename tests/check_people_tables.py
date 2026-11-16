import pandas as pd

from config.paths import RAW_DATA_DIR
from config.logging_config import setup_logging
from src.scripts.stage2_modules.stage2_clean_credits import clean_credits
from src.scripts.stage2_modules.stage2_build_tables import build_people_tables

setup_logging()

credits = clean_credits(pd.read_csv(RAW_DATA_DIR / "credits.csv"))
people, movie_cast, movie_crew = build_people_tables(credits)

print("\nPeople:", len(people), "| cast credits:", len(movie_cast), "| crew credits:", len(movie_crew))
print("Movies with cast:", movie_cast["movie_id"].nunique(),
      "| movies with crew:", movie_crew["movie_id"].nunique())

missing_gender = movie_cast["gender"].isna().sum() + movie_crew["gender"].isna().sum()
print("Missing gender (cast + crew):", missing_gender)

print("\nData types:")
print(movie_cast.dtypes)

print("\nToy Story, top 3 cast:")
top_cast = movie_cast[movie_cast["movie_id"] == 862].sort_values("order").head(3)
print(top_cast.merge(people, on="person_id")[["order", "name", "character"]].to_string(index=False))

print("\nToy Story, director:")
directors = movie_crew[(movie_crew["movie_id"] == 862) & (movie_crew["job"] == "Director")]
print(directors.merge(people, on="person_id")[["name", "job"]].to_string(index=False))

conflict_ids = [9779, 23764, 58646, 63574, 67212, 72932, 74947, 78456,
                78809, 87637, 87662, 99692, 111690, 117642, 132233]
print("\nName conflict outcomes:")
print(people[people["person_id"].isin(conflict_ids)].to_string(index=False))

# Run from the project root with: python -m tests.check_people_tables