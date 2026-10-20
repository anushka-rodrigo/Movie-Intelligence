#setup
import pandas as pd
from pathlib import Path

def extract_data():
    DATA = Path("../../data/raw_data")

    credits       = pd.read_csv(DATA / "credits.csv")
    keywords      = pd.read_csv(DATA / "keywords.csv")
    links         = pd.read_csv(DATA / "links.csv")
    links_small   = pd.read_csv(DATA / "links_small.csv")
    meta          = pd.read_csv(DATA / "movies_metadata.csv", low_memory=False)
    ratings_small = pd.read_csv(DATA / "ratings_small.csv")
    ratings       = pd.read_csv(
        DATA / "ratings.csv",
        dtype={"userId": "int32", "movieId": "int32", "rating": "float32", "timestamp": "int32"},
    )  # smaller dtypes keep 26M rows light on memory

    tables = {
        "credits": credits, 
        "keywords": keywords, 
        "links": links,
        "links_small": links_small, 
        "meta": meta,
        "ratings_small": ratings_small, 
        "ratings": ratings,
    }