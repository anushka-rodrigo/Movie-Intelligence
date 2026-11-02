# Stage 2: ETL Pipeline - Extraction
import pandas as pd
from config.paths import RAW_DATA_DIR


# Expected row counts from the Stage 1 investigation
EXPECTED_ROW_COUNTS = {
    "credits": 45_476,
    "keywords": 46_419,
    "links": 45_843,
    "movies_metadata": 45_466,
    "ratings": 26_024_289,
}


def extract_data():
    # Load raw datasets
    credits = pd.read_csv(
        RAW_DATA_DIR / "credits.csv"
    )
    keywords = pd.read_csv(
        RAW_DATA_DIR / "keywords.csv"
    )
    links = pd.read_csv(
        RAW_DATA_DIR / "links.csv"
    )
    movies_metadata = pd.read_csv(
        RAW_DATA_DIR / "movies_metadata.csv",
        low_memory=False
    )
    ratings = pd.read_csv(
        RAW_DATA_DIR / "ratings.csv",
        dtype={
            "userId": "int32",
            "movieId": "int32",
            "rating": "float32",
            "timestamp": "int32"
        }
    )

    # Store datasets in a dictionary
    tables = {
        "credits": credits,
        "keywords": keywords,
        "links": links,
        "movies_metadata": movies_metadata,
        "ratings": ratings,
    }

    # Validate extracted row counts
    for table_name, dataframe in tables.items():

        actual_rows = len(dataframe)
        expected_rows = EXPECTED_ROW_COUNTS[table_name]

        if actual_rows != expected_rows:
            raise ValueError(
                f"Row count mismatch in {table_name}: "
                f"expected {expected_rows:,}, "
                f"got {actual_rows:,}"
            )

        print(
            f"{table_name}: {actual_rows:,} rows - PASS"
        )

    # Return all extracted datasets
    return tables
