import pandas as pd
from pathlib import Path

DATA_DIR = Path("data/raw_data")

files = [
    "credits.csv",
    "keywords.csv",
    "links_small.csv",
    "links.csv",
    "movies_metadata.csv",
    "ratings_small.csv",
    "ratings.csv",
]

for file in files:
    path = DATA_DIR / file
    df = pd.read_csv(path)
    
    print(f"Information on {file}:")
    print("Row count: ", len(df))
    print("Column count: ", len(df.columns))
    print()