import logging

import pandas as pd

logger = logging.getLogger(__name__)


def build_safe_bridge(movie_links, movies):
    """C11, C12: split the bridge into rows that are safe to join and rows that are not."""
    rows_before = len(movie_links)

    in_metadata = movie_links["movie_id"].isin(movies["movie_id"])

    # One reason per excluded row; C11 takes priority if both apply
    reason = pd.Series(None, index=movie_links.index, dtype="object")
    reason[~in_metadata] = "tmdb_id_not_in_metadata"                            # C11
    reason[movie_links["shared_tmdb_id"] & reason.isna()] = "shared_tmdb_id"    # C12

    safe = (
        movie_links[reason.isna()]
        .drop(columns="shared_tmdb_id")       # always False in the safe rows
        .reset_index(drop=True)
    )
    excluded = movie_links[reason.notna()].copy()
    excluded["exclusion_reason"] = reason[reason.notna()]
    excluded = excluded.reset_index(drop=True)

    # Checks (C14)
    if len(safe) + len(excluded) != rows_before:
        raise ValueError("bridge: rows were lost or created while splitting.")
    if safe["movie_id"].duplicated().any():
        raise ValueError("bridge: a movie_id is still reachable through two rows.")
    if safe["movielens_id"].duplicated().any():
        raise ValueError("bridge: movielens_id is not unique.")
    if not safe["movie_id"].isin(movies["movie_id"]).all():
        raise ValueError("bridge: a safe row points at a movie that does not exist.")

    logger.info(
        "build_safe_bridge: %s rows -> %s safe + %s excluded (%s)",
        rows_before, len(safe), len(excluded),
        excluded["exclusion_reason"].value_counts().to_dict(),
    )
    return safe, excluded


def add_imdb_conflict_flag(safe_bridge, movies):
    """C17: flag bridge rows whose IMDb id disagrees with the one in metadata."""
    merged = safe_bridge.merge(
        movies[["movie_id", "imdb_id"]].rename(columns={"imdb_id": "metadata_imdb_id"}),
        on="movie_id",
        how="left",
        validate="one_to_one",
    )
    if len(merged) != len(safe_bridge):
        raise ValueError("imdb_conflict: the join changed the number of rows.")

    comparable = merged["metadata_imdb_id"].notna()
    different = (merged["imdb_id"] != merged["metadata_imdb_id"]).fillna(False).astype(bool)
    merged["imdb_conflict"] = comparable & different

    logger.info(
        "add_imdb_conflict_flag: %s comparable movies, %s conflicts.",
        comparable.sum(), merged["imdb_conflict"].sum(),
    )
    return merged.drop(columns="metadata_imdb_id")


def link_ratings_to_movies(ratings, bridge):
    """C09, C14: attach a TMDB movie_id to each rating through the bridge, and report the loss."""
    rows_before = len(ratings)

    linked = ratings[["movielens_id"]].merge(
        bridge[["movielens_id", "movie_id"]],
        on="movielens_id",
        how="left",
        validate="many_to_one",     # stops if the bridge has a repeated movielens_id
    )
    if len(linked) != rows_before:
        raise ValueError("ratings join: the number of ratings changed.")

    reachable = linked["movie_id"].notna()

    summary = {
        "rating_rows": rows_before,
        "rating_rows_reachable": int(reachable.sum()),
        "rating_rows_lost": int((~reachable).sum()),
        "rated_movies": int(linked["movielens_id"].nunique()),
        "rated_movies_reachable": int(linked.loc[reachable, "movielens_id"].nunique()),
    }
    logger.info("link_ratings_to_movies: %s", summary)
    return summary