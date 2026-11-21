import logging

import pandas as pd

from src.scripts.stage2_modules.stage2_table_specs import TABLE_SPECS

logger = logging.getLogger(__name__)

RATING_SCALE = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
EXPECTED_COVERAGE = {
    "rating_rows": 26_024_289,
    "rating_rows_reachable": 25_972_129,
    "rating_rows_lost": 52_160,
    "rated_movies": 45_115,
    "rated_movies_reachable": 44_682,
}
EXPECTED_IMDB_CONFLICTS = 65
EXPECTED_EXCLUSIONS = {"tmdb_id_not_in_metadata": 161, "shared_tmdb_id": 59}
MOVIE_MISSING_FROM_CREDITS = 401840    # C13

# (child table, child column, parent table, parent column)
FOREIGN_KEYS = [
    ("movie_genres", "movie_id", "movies", "movie_id"),
    ("movie_genres", "genre_id", "genres", "genre_id"),
    ("movie_production_companies", "movie_id", "movies", "movie_id"),
    ("movie_production_companies", "company_id", "production_companies", "company_id"),
    ("movie_production_countries", "movie_id", "movies", "movie_id"),
    ("movie_production_countries", "country_code", "production_countries", "country_code"),
    ("movie_spoken_languages", "movie_id", "movies", "movie_id"),
    ("movie_spoken_languages", "language_code", "spoken_languages", "language_code"),
    ("movie_keywords", "movie_id", "movies", "movie_id"),
    ("movie_keywords", "keyword_id", "keywords", "keyword_id"),
    ("movie_cast", "movie_id", "movies", "movie_id"),
    ("movie_cast", "person_id", "people", "person_id"),
    ("movie_crew", "movie_id", "movies", "movie_id"),
    ("movie_crew", "person_id", "people", "person_id"),
    ("movie_links", "movie_id", "movies", "movie_id"),
]


class Checker:
    """Collects check results, so every problem is reported at once."""

    def __init__(self):
        self.passed = 0
        self.failures = []

    def expect(self, condition, message):
        if bool(condition):
            self.passed += 1
        else:
            self.failures.append(message)
            logger.error("VALIDATION FAILED: %s", message)


def _ratings_pairs_are_unique(ratings):
    """Proves (user_id, movielens_id) is a key, without hashing 26 million rows."""
    keys = (
        ratings["user_id"].to_numpy(dtype="int64") * 1_000_000
        + ratings["movielens_id"].to_numpy(dtype="int64")
    )
    keys.sort()
    return not bool((keys[1:] == keys[:-1]).any())


def validate_all(tables, coverage):
    check = Checker()

    check.expect(
        set(tables) == set(TABLE_SPECS),
        f"table names differ from the specification: {sorted(set(tables) ^ set(TABLE_SPECS))}",
    )

    # 1. Row counts, missing keys, unique keys
    for name, spec in TABLE_SPECS.items():
        if name not in tables:
            continue
        table = tables[name]
        check.expect(
            len(table) == spec["rows"],
            f"{name}: expected {spec['rows']} rows, found {len(table)}",
        )
        check.expect(
            table[spec["key"]].notna().all().all(),
            f"{name}: missing values in key columns {spec['key']}",
        )
        if name == "ratings":
            check.expect(
                tables["ratings"]["movielens_id"].max() < 1_000_000,
                "ratings: movielens_id too large for the uniqueness check",
            )
            check.expect(_ratings_pairs_are_unique(table), "ratings: repeated (user_id, movielens_id) pairs")
        else:
            check.expect(
                not table.duplicated(subset=spec["key"]).any(),
                f"{name}: key {spec['key']} is not unique",
            )

    # 2. Foreign keys: nothing may point at a row that does not exist
    for child, child_col, parent, parent_col in FOREIGN_KEYS:
        orphans = int((~tables[child][child_col].isin(tables[parent][parent_col])).sum())
        check.expect(orphans == 0, f"{child}.{child_col}: {orphans} values not found in {parent}.{parent_col}")

    # 3. Value checks
    movies = tables["movies"]
    check.expect(movies["vote_average"].dropna().between(0.5, 10).all(), "movies: vote_average outside 0.5 to 10")
    check.expect((movies["runtime"].dropna() > 0).all(), "movies: a runtime is zero or negative")
    check.expect((movies["budget"].dropna() >= 1_000).all(), "movies: a budget placeholder remains")
    check.expect((movies["revenue"].dropna() >= 1_000).all(), "movies: a revenue placeholder remains")
    check.expect(
        movies["release_date"].dropna().between(pd.Timestamp("1874-01-01"), pd.Timestamp("2020-12-31")).all(),
        "movies: release_date outside 1874 to 2020",
    )

    for name in ["movie_cast", "movie_crew"]:
        check.expect(tables[name]["gender"].dropna().isin([1, 2]).all(), f"{name}: unexpected gender value")
    check.expect((tables["movie_cast"]["order"] >= 0).all(), "movie_cast: negative billing order")

    links = tables["movie_links"]
    check.expect(links["imdb_id"].str.fullmatch(r"tt\d{7}").all(), "movie_links: malformed imdb_id")
    check.expect(
        int(links["imdb_conflict"].sum()) == EXPECTED_IMDB_CONFLICTS,
        f"movie_links: expected {EXPECTED_IMDB_CONFLICTS} imdb conflicts",
    )
    check.expect(
        tables["movie_links_excluded"]["exclusion_reason"].value_counts().to_dict() == EXPECTED_EXCLUSIONS,
        "movie_links_excluded: unexpected exclusion reasons",
    )
    check.expect(
        tables["ratings"]["rating"].isin(RATING_SCALE).all(),
        "ratings: a rating is outside the 0.5 to 5.0 scale",
    )

    # 4. C13: movie 401840 must exist, with no cast, crew or keywords
    check.expect((movies["movie_id"] == MOVIE_MISSING_FROM_CREDITS).any(), "C13: movie 401840 is missing from movies")
    for name in ["movie_cast", "movie_crew", "movie_keywords"]:
        check.expect(
            not (tables[name]["movie_id"] == MOVIE_MISSING_FROM_CREDITS).any(),
            f"C13: movie 401840 unexpectedly appears in {name}",
        )

    # 5. Join coverage must match the Stage 1 investigation
    for key, expected in EXPECTED_COVERAGE.items():
        check.expect(coverage[key] == expected, f"coverage: {key} expected {expected}, found {coverage[key]}")

    logger.info("Validation finished: %s checks passed, %s failed.", check.passed, len(check.failures))
    if check.failures:
        raise ValueError("Validation failed:\n" + "\n".join(check.failures))
