import pandas as pd

from config.paths import RAW_DATA_DIR
from config.logging_config import setup_logging
from src.scripts.stage2_modules.stage2_clean_credits import clean_credits

setup_logging()

credits = pd.read_csv(RAW_DATA_DIR / "credits.csv")
clean = clean_credits(credits)

print("\nRows before:", len(credits), "| after:", len(clean))
print("Ids unique:", not clean["id"].duplicated().any())

print("\nEmpty cast lists:", clean["cast"].apply(lambda v: v == []).sum())
print("Empty crew lists:", clean["crew"].apply(lambda v: v == []).sum())

toy_story = clean[clean["id"] == 862].iloc[0]
print("\nToy Story, first cast member:", toy_story["cast"][0]["name"])
print("Toy Story cast size:", len(toy_story["cast"]), "| crew size:", len(toy_story["crew"]))

# Run from the project root with: python -m tests.check_credits