import logging

import pandas as pd

logger = logging.getLogger(__name__)

EXPECTED_RATING_VALUES = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
EARLIEST_ALLOWED = pd.Timestamp("1995-01-01")
LATEST_ALLOWED = pd.Timestamp("2017-12-31")


def clean_ratings(ratings):
    """C27: convert the Unix-second timestamp to a real datetime, and check the rest."""
    rows_before = len(ratings)

    # assign() builds a new table that reuses the other columns, so 26M rows are not copied
    ratings = ratings.assign(timestamp=pd.to_datetime(ratings["timestamp"], unit="s"))

    # Checks: Stage 1 said nothing else needs fixing, so prove it
    if len(ratings) != rows_before:
        raise ValueError("ratings: the row count changed.")
    if ratings.isna().any().any():
        raise ValueError("ratings: missing values found.")

    rating_values = sorted(ratings["rating"].unique().tolist())
    if rating_values != EXPECTED_RATING_VALUES:
        raise ValueError(f"ratings: unexpected rating values {rating_values}")

    first, last = ratings["timestamp"].min(), ratings["timestamp"].max()
    if first < EARLIEST_ALLOWED or last > LATEST_ALLOWED:
        raise ValueError(f"ratings: timestamps outside the expected range: {first} to {last}")

    logger.info("clean_ratings: %s rows, timestamps from %s to %s.", len(ratings), first, last)
    return ratings