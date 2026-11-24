import pandas as pd

from config.paths import RAW_DATA_DIR

raw = pd.read_csv(RAW_DATA_DIR / "keywords.csv")
extra = raw[raw.duplicated(subset="id", keep="first")]

print("Extra copies:", len(extra), "| of which empty:", (extra["keywords"] == "[]").sum())

# Run from the project root with: python -m tests.check_keywords_gap