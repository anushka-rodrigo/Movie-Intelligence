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
    
    print("="*40)
    print(f"Information on {file}:")
    print("="*40)
    print("Row count: ", len(df))
    print("Column count: ", len(df.columns))    
    print()
    
    for column in df.columns:
        print("Column: ", column)
        print("     Data type: ", df[column].dtype)
        print("     Missing values: ", df[column].isna().sum())
        print("     Unique values: ", df[column].nunique())
        print("     Duplicates: ", df[column].duplicated().sum())
        
        if pd.api.types.is_numeric_dtype(df[column]):
            print("     Minimum: ", df[column].min())
            print("     Maximum: ", df[column].max())
            
        print()