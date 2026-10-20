#setup
import pandas as pd
from pathlib import Path

def extract_data():
    DATA = Path("../../data/raw_data")

    credits       = pd.read_csv(DATA / "credits.csv")
    keywords      = pd.read_csv(DATA / "keywords.csv")
    links         = pd.read_csv(DATA / "links.csv")
    meta          = pd.read_csv(DATA / "movies_metadata.csv", low_memory=False)
    ratings       = pd.read_csv(
        DATA / "ratings.csv",
        dtype={"userId": "int32", "movieId": "int32", "rating": "float32", "timestamp": "int32"},
    )  # smaller dtypes keep 26M rows light on memory

    tables = {
        "credits": credits, 
        "keywords": keywords, 
        "links": links,
        "meta": meta,
        "ratings": ratings,
    }