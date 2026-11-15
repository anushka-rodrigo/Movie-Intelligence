import pandas as pd

from config.paths import RAW_DATA_DIR
from config.logging_config import setup_logging
from src.scripts.stage2_modules.stage2_clean_keywords import clean_keywords

setup_logging()

keywords = pd.read_csv(RAW_DATA_DIR / "keywords.csv")
clean = clean_keywords(keywords)

print("\nRows before:", len(keywords), "| after:", len(clean))
print("Ids unique:", not clean["id"].duplicated().any())

print("\nEmpty keyword lists:", clean["keywords"].apply(lambda v: v == []).sum())

toy_story = clean[clean["id"] == 862].iloc[0]
print("\nToy Story keywords:", [k["name"] for k in toy_story["keywords"]])

# Run from the project root with: python -m tests.check_keywords