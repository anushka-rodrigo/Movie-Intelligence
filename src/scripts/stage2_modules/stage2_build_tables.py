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


def build_lookup_and_link(meta, list_column, source_key, key_name, name_name, label):
    """Split a column of lists of dictionaries into a lookup table and a movie-link table.

    source_key: the dictionary field that identifies an entry ('id', 'iso_3166_1', ...)
    key_name, name_name: the column names to use in the output tables
    """
    movies = meta.rename(columns={"id": "movie_id"})

    entries = explode_entries(movies, "movie_id", list_column)
    entries = entries.rename(columns={source_key: key_name, "name": name_name})

    # Check 1: nothing lost or invented
    expected_entries = movies[list_column].apply(
        lambda value: len(value) if isinstance(value, list) else 0
    ).sum()
    if len(entries) != expected_entries:
        raise ValueError(f"{label}: expected {expected_entries} entries, got {len(entries)}")

    # Check 2: every key has exactly one name
    names_per_key = entries.groupby(key_name)[name_name].nunique()
    if (names_per_key > 1).any():
        examples = names_per_key[names_per_key > 1].index[:5].tolist()
        raise ValueError(
            f"{label}: some {key_name} values have more than one name, e.g. {examples}"
        )

    # Check 3: no movie lists the same entry twice
    if entries.duplicated(subset=["movie_id", key_name]).any():
        raise ValueError(f"{label}: repeated (movie_id, {key_name}) pairs.")

    lookup = (
        entries[[key_name, name_name]]
        .drop_duplicates()
        .sort_values(key_name)
        .reset_index(drop=True)
    )
    link = entries[["movie_id", key_name]]

    logger.info("%s: %s lookup rows, %s link rows.", label, len(lookup), len(link))
    return lookup, link


def build_genre_tables(meta):
    return build_lookup_and_link(meta, "genres", "id", "genre_id", "genre_name", "genres")


def build_company_tables(meta):
    return build_lookup_and_link(
        meta, "production_companies", "id", "company_id", "company_name", "production_companies"
    )


def build_country_tables(meta):
    return build_lookup_and_link(
        meta, "production_countries", "iso_3166_1", "country_code", "country_name", "production_countries"
    )


def build_language_tables(meta):
    return build_lookup_and_link(
        meta, "spoken_languages", "iso_639_1", "language_code", "language_name", "spoken_languages"
    )
    
def build_keyword_tables(keywords_table):
    return build_lookup_and_link(
        keywords_table, "keywords", "id", "keyword_id", "keyword_name", "keywords"
    )
    
def build_people_tables(credits):
    """Split credits into people, movie_cast and movie_crew."""
    movies = credits.rename(columns={"id": "movie_id"})

    cast = explode_entries(movies, "movie_id", "cast").rename(columns={"id": "person_id"})
    crew = explode_entries(movies, "movie_id", "crew").rename(columns={"id": "person_id"})

    # Check 1: nothing lost or invented
    for label, entries in [("cast", cast), ("crew", crew)]:
        expected = movies[label].apply(
            lambda value: len(value) if isinstance(value, list) else 0
        ).sum()
        if len(entries) != expected:
            raise ValueError(f"{label}: expected {expected} entries, got {len(entries)}")

        # Check 2: credit_id must be a real key
        if entries["credit_id"].duplicated().any():
            raise ValueError(f"{label}: repeated credit_id values.")

        # Gender 0 means 'not specified', so it becomes missing
        entries["gender"] = entries["gender"].mask(entries["gender"] == 0).astype("Int64")

    # One row per person; cast is read before crew, so the first appearance wins
    people_entries = pd.concat(
        [cast[["person_id", "name"]], crew[["person_id", "name"]]], ignore_index=True
    )

    names_per_id = people_entries.groupby("person_id")["name"].nunique()
    conflicting_ids = names_per_id[names_per_id > 1].index
    logger.info(
        "people: %s person ids have more than one name; first appearance wins: %s",
        len(conflicting_ids), sorted(int(i) for i in conflicting_ids),
    )
    
    # Prefer a Latin-alphabet spelling; if several qualify, the first appearance wins
    people_entries["_ascii"] = people_entries["name"].apply(lambda name: name.isascii())

    people = (
        people_entries.sort_values(["person_id", "_ascii"], ascending=[True, False])
        .drop_duplicates(subset="person_id", keep="first")
        .drop(columns="_ascii")
        .reset_index(drop=True)
    )

    # Check 3: one row per person id
    if people["person_id"].duplicated().any():
        raise ValueError("people: repeated person_id values.")

    movie_cast = cast[["credit_id", "movie_id", "person_id", "character", "order", "gender"]]
    movie_crew = crew[["credit_id", "movie_id", "person_id", "department", "job", "gender"]]

    logger.info(
        "build_people_tables: %s people, %s cast credits, %s crew credits.",
        len(people), len(movie_cast), len(movie_crew),
    )
    return people, movie_cast, movie_crew

LIST_COLUMNS_NOW_IN_OWN_TABLES = [
    "genres", "production_companies", "production_countries", "spoken_languages",
]
DROPPED_COLUMNS = ["homepage", "poster_path"]       # C28


def build_movies_table(meta):
    """One row per movie: plain columns only, with the collection split in two."""
    movies = meta.rename(columns={"id": "movie_id"})

    # A movie belongs to at most one collection, so it stays as two plain columns
    collection = movies["belongs_to_collection"]
    movies["collection_id"] = collection.apply(
        lambda value: value["id"] if isinstance(value, dict) else None
    ).astype("Int64")
    movies["collection_name"] = collection.apply(
        lambda value: value["name"] if isinstance(value, dict) else None
    )

    # Each collection id must have exactly one name
    names_per_collection = movies.groupby("collection_id")["collection_name"].nunique()
    if (names_per_collection > 1).any():
        raise ValueError("movies: some collection_id values have more than one name.")

    movies = movies.drop(
        columns=LIST_COLUMNS_NOW_IN_OWN_TABLES + DROPPED_COLUMNS + ["belongs_to_collection"]
    )

    if movies["movie_id"].duplicated().any():
        raise ValueError("movies: movie_id is not unique.")

    logger.info("build_movies_table: %s rows, %s columns.", len(movies), movies.shape[1])
    return movies


def build_links_table(links):
    """One row per MovieLens-to-TMDB mapping."""
    movie_links = links.rename(
        columns={"movieId": "movielens_id", "tmdbId": "movie_id", "imdbId": "imdb_id"}
    )

    if movie_links["movielens_id"].duplicated().any():
        raise ValueError("movie_links: movielens_id is not unique.")

    logger.info("build_links_table: %s rows.", len(movie_links))
    return movie_links


def build_ratings_table(ratings):
    """One row per user's rating of one movie. Renaming only changes labels, not the data."""
    renamed = ratings.rename(columns={"userId": "user_id", "movieId": "movielens_id"})

    if "movie_id" in renamed.columns:
        raise ValueError("ratings: must not contain a TMDB movie_id column.")

    logger.info("build_ratings_table: %s rows.", len(renamed))
    return renamed