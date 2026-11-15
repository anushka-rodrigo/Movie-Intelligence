import logging

import pandas as pd

logger = logging.getLogger(__name__)


def explode_entries(table, id_column, list_column):
    """One row per list entry: the movie id, plus the fields of each dictionary."""
    exploded = table[[id_column, list_column]].explode(list_column)

    # A movie with an empty or missing list becomes one empty row: remove it
    exploded = exploded.dropna(subset=[list_column]).reset_index(drop=True)

    entries = pd.DataFrame(exploded[list_column].tolist())
    entries.insert(0, id_column, exploded[id_column])
    return entries


def build_genre_tables(meta):
    """Split the genres lists into a lookup table (genres) and a link table (movie_genres)."""
    movies = meta.rename(columns={"id": "movie_id"})

    entries = explode_entries(movies, "movie_id", "genres")
    entries = entries.rename(columns={"id": "genre_id", "name": "genre_name"})

    # Check 1: nothing lost or invented
    expected_entries = movies["genres"].apply(
        lambda value: len(value) if isinstance(value, list) else 0
    ).sum()
    if len(entries) != expected_entries:
        raise ValueError(
            f"genres: expected {expected_entries} entries, got {len(entries)}"
        )

    # Check 2: every genre_id has exactly one name
    names_per_id = entries.groupby("genre_id")["genre_name"].nunique()
    if (names_per_id > 1).any():
        raise ValueError("genres: some genre_id values have more than one name.")

    # Check 3: no movie lists the same genre twice
    if entries.duplicated(subset=["movie_id", "genre_id"]).any():
        raise ValueError("movie_genres: repeated (movie_id, genre_id) pairs.")

    genres = (
        entries[["genre_id", "genre_name"]]
        .drop_duplicates()
        .sort_values("genre_id")
        .reset_index(drop=True)
    )
    movie_genres = entries[["movie_id", "genre_id"]]

    logger.info(
        "build_genre_tables: %s genres, %s movie-genre rows.", len(genres), len(movie_genres)
    )
    return genres, movie_genres