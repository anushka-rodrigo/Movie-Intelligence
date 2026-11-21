import logging

logger = logging.getLogger(__name__)

EXPECTED_ROWS_WITHOUT_TMDB_ID = 219    # C10
EXPECTED_EXTRA_TMDB_COPIES = 30        # C12 (the first copy is not counted)


def clean_links(links, expected_missing_tmdb=EXPECTED_ROWS_WITHOUT_TMDB_ID, expected_extra_copies=EXPECTED_EXTRA_TMDB_COPIES,):
    """C10, C12, C15, C27: fix types, rebuild imdbId, flag shared tmdbId, drop rows with no tmdbId."""
    rows_before = len(links)
    links = links.copy()

    # Keys must be unique before we touch anything
    if links["movieId"].duplicated().any():
        raise ValueError("links: movieId is not unique.")

    # C27: tmdbId is a decimal only because it contains missing values
    links["tmdbId"] = links["tmdbId"].astype("Int64")

    # C15: 114709 -> tt0114709
    links["imdbId"] = "tt" + links["imdbId"].astype(str).str.zfill(7)
    if not links["imdbId"].str.fullmatch(r"tt\d{7}").all():
        raise ValueError("links: some imdbId values are not 'tt' plus 7 digits.")
    if links["imdbId"].duplicated().any():
        raise ValueError("links: imdbId is not unique.")

    # C12: flag every row whose tmdbId is shared with another row (ignore missing values)
    extra_copies = links["tmdbId"].dropna().duplicated().sum()
    if extra_copies != expected_extra_copies:
        raise ValueError(
            f"links: expected {expected_extra_copies} extra tmdbId copies, found {extra_copies}"
        )
    links["shared_tmdb_id"] = links["tmdbId"].notna() & links["tmdbId"].duplicated(keep=False)
    logger.info(
        "links: %s rows share a tmdbId (%s distinct tmdbId values).",
        links["shared_tmdb_id"].sum(),
        links.loc[links["shared_tmdb_id"], "tmdbId"].nunique(),
    )

    # C10: drop the rows that have no tmdbId (they stay in the raw file)
    missing_tmdb = links["tmdbId"].isna()
    if missing_tmdb.sum() != expected_missing_tmdb:
        raise ValueError(
            f"links: expected {expected_missing_tmdb} rows without tmdbId, "
            f"found {missing_tmdb.sum()}"
        )
    links = links[~missing_tmdb].reset_index(drop=True)

    if links["tmdbId"].isna().any():
        raise ValueError("links: missing tmdbId values remain.")

    logger.info("clean_links: %s rows -> %s rows.", rows_before, len(links))
    return links