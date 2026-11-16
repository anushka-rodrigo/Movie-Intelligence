import pandas as pd

from config.paths import RAW_DATA_DIR
from config.logging_config import setup_logging
from src.scripts.stage2_modules.stage2_clean_credits import clean_credits
from src.scripts.stage2_modules.stage2_build_tables import explode_entries

setup_logging()

credits = clean_credits(pd.read_csv(RAW_DATA_DIR / "credits.csv"))
movies = credits.rename(columns={"id": "movie_id"})

cast = explode_entries(movies, "movie_id", "cast")
crew = explode_entries(movies, "movie_id", "crew")

for label, entries in [("CAST", cast), ("CREW", crew)]:
    print(f"\n=== {label} ===")
    print("Rows:", len(entries), "| movies covered:", entries["movie_id"].nunique())
    print("Columns:", entries.columns.tolist())
    print("\nMissing values per column:")
    print(entries.isna().sum().to_string())
    print("\ncredit_id repeated:", entries["credit_id"].duplicated().sum())

# The same person can appear in both cast and crew, so look at them together
people = pd.concat(
    [cast[["id", "name", "gender"]], crew[["id", "name", "gender"]]],
    ignore_index=True,
)
print("\n=== PEOPLE (cast and crew together) ===")
print("Entries:", len(people), "| distinct person ids:", people["id"].nunique())

names_per_id = people.groupby("id")["name"].nunique()
print("\nPerson ids with more than one name:", (names_per_id > 1).sum())
conflicts = names_per_id[names_per_id > 1].index[:5]
print(people[people["id"].isin(conflicts)].drop_duplicates().sort_values("id").to_string())

genders_per_id = people.groupby("id")["gender"].nunique()
print("\nPerson ids with more than one gender value:", (genders_per_id > 1).sum())

print("\nGender values:")
print(people["gender"].value_counts(dropna=False).to_string())

# Run from the project root with: python -m tests.explore_people