import numpy as np
import pandas as pd
import pytest

from src.scripts.stage2_modules.stage2_helpers import keep_first_copy_per_id, parse_literal_column
from src.scripts.stage2_modules.stage2_clean_metadata import (
    repair_split_records,
    remove_duplicate_movies,
    fix_data_types,
    clean_placeholders,
)
from src.scripts.stage2_modules.stage2_clean_links import clean_links
from src.scripts.stage2_modules.stage2_clean_ratings import clean_ratings
from src.scripts.stage2_modules.stage2_build_tables import build_lookup_and_link, build_people_tables
from src.scripts.stage2_modules.stage2_join_tables import build_safe_bridge, link_ratings_to_movies
from src.scripts.stage2_modules.stage2_load import cast_integer_columns

META_COLUMNS = [
    "adult", "belongs_to_collection", "budget", "genres", "homepage", "id", "imdb_id",
    "original_language", "original_title", "overview", "popularity", "poster_path",
    "production_companies", "production_countries", "release_date", "revenue", "runtime",
    "spoken_languages", "status", "tagline", "title", "video", "vote_average", "vote_count",
]


# ---------- parsing (C26) ----------

def test_parse_literal_column_parses_lists_and_keeps_missing():
    parsed = parse_literal_column(pd.Series(["[{'id': 1, 'name': 'A'}]", "[]", None]), list, "genres")
    assert parsed.iloc[0] == [{"id": 1, "name": "A"}]
    assert parsed.iloc[1] == []
    assert pd.isna(parsed.iloc[2])


def test_parse_literal_column_rejects_the_wrong_type():
    with pytest.raises(ValueError):
        parse_literal_column(pd.Series(["5"]), list, "genres")


# ---------- duplicates (C03 to C07) ----------

def test_keep_first_copy_per_id_keeps_the_first_row():
    table = pd.DataFrame({"id": [1, 1, 2], "value": ["a", "b", "c"]})
    cleaned = keep_first_copy_per_id(table, "id", expected_removed=1, table_name="t")
    assert cleaned["value"].tolist() == ["a", "c"]


def test_keep_first_copy_per_id_stops_on_an_unexpected_count():
    table = pd.DataFrame({"id": [1, 1, 2], "value": ["a", "a", "c"]})
    with pytest.raises(ValueError):
        keep_first_copy_per_id(table, "id", expected_removed=5, table_name="t")


def test_remove_duplicate_movies_keeps_the_higher_vote_count():
    meta = pd.DataFrame({
        "id": ["1", "1", "2"],
        "vote_count": ["10", "12", "5"],
        "popularity": ["9.0", "3.0", "1.0"],     # popularity must never decide
    })
    cleaned = remove_duplicate_movies(meta, expected_removed=1)
    assert cleaned["vote_count"].tolist() == ["12", "5"]


# ---------- split records (C01) ----------

def test_repair_split_records_glues_the_halves_together():
    def row(**values):
        return {column: None for column in META_COLUMNS} | values

    normal = row(id="1", title="Normal", overview="Fine")
    stub = row(id="5", original_title="Midnight", overview="First half")
    tail_values = [
        " second half", "0.5", "/p.jpg", "[]", "[]", "1997-08-20", "0", "104.0",
        "[]", "Released", "a tagline", "Midnight Man", "False", "6.0", "1",
    ]
    tail = dict(zip(META_COLUMNS[:15], tail_values)) | {c: None for c in META_COLUMNS[15:]}

    fixed = repair_split_records(pd.DataFrame([normal, stub, tail]), expected_records=1)

    assert len(fixed) == 2
    assert fixed.loc[1, "title"] == "Midnight Man"
    assert fixed.loc[1, "release_date"] == "1997-08-20"
    assert fixed.loc[1, "overview"] == "First half\n second half"


# ---------- data types (C27) ----------

def _typed_input(**overrides):
    data = {
        "id": ["1", "2"], "vote_count": ["3.0", "0.0"], "popularity": ["1.5", "2.5"],
        "budget": ["100", "0"], "revenue": ["5", "6"], "runtime": ["90.0", "0.0"],
        "vote_average": ["7.5", "0.0"], "adult": ["False", "True"], "video": ["False", "False"],
        "status": ["Released", "Planned"], "original_language": ["en", "fr"],
        "release_date": ["1995-10-30", None],
    }
    data.update(overrides)
    return pd.DataFrame(data)


def test_fix_data_types_converts_every_column():
    typed = fix_data_types(_typed_input())
    assert str(typed["id"].dtype) == "Int64"
    assert typed["adult"].tolist() == [False, True]
    assert typed["release_date"].iloc[0] == pd.Timestamp("1995-10-30")
    assert pd.isna(typed["release_date"].iloc[1])


def test_fix_data_types_stops_on_an_unparseable_value():
    with pytest.raises(ValueError):
        fix_data_types(_typed_input(budget=["abc", "1"]))


# ---------- placeholders and flags (C16, C18 to C22) ----------

def test_clean_placeholders_blanks_zeros_and_flags_borderline_values():
    meta = pd.DataFrame({
        "budget": [0.0, 500.0, 5_000.0, 2_000_000.0],
        "revenue": [0.0, 900.0, 20_000.0, 5_000_000.0],
        "runtime": [0.0, 90.0, 400.0, 100.0],
        "vote_average": [0.0, 0.0, 6.0, 7.0],
        "vote_count": pd.array([0, 10, 5, 5], dtype="Int64"),
        "imdb_id": ["0", "tt0000001", "tt0000002", "tt0000003"],
    })
    clean = clean_placeholders(meta)

    assert clean["budget"].isna().tolist() == [True, True, False, False]
    assert clean["budget_review"].tolist() == [False, False, True, False]
    assert clean["long_runtime"].tolist() == [False, False, True, False]
    assert clean["vote_average_zero_with_votes"].tolist() == [False, True, False, False]
    assert pd.isna(clean["imdb_id"].iloc[0])


# ---------- links (C10, C12, C15) ----------

def test_clean_links_rebuilds_imdb_ids_flags_shared_ids_and_drops_missing_tmdb():
    links = pd.DataFrame({
        "movieId": [1, 2, 3, 4],
        "imdbId": [114709, 113497, 1, 2],
        "tmdbId": [862.0, 8844.0, 8844.0, None],
    })
    clean = clean_links(links, expected_missing_tmdb=1, expected_extra_copies=1)

    assert clean["imdbId"].iloc[0] == "tt0114709"
    assert clean["shared_tmdb_id"].tolist() == [False, True, True]
    assert len(clean) == 3


# ---------- ratings (C27) ----------

def test_clean_ratings_converts_the_timestamp():
    ratings = pd.DataFrame({
        "userId": [1] * 10,
        "movieId": list(range(1, 11)),
        "rating": [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0],
        "timestamp": [1425941529] * 10,
    })
    clean = clean_ratings(ratings)
    assert clean["timestamp"].iloc[0] == pd.Timestamp("2015-03-09 22:52:09")


# ---------- list tables ----------

def test_build_lookup_and_link_splits_lists_into_two_tables():
    meta = pd.DataFrame({
        "id": pd.array([1, 2, 3], dtype="Int64"),
        "genres": [
            [{"id": 10, "name": "Drama"}, {"id": 20, "name": "Comedy"}],
            [{"id": 10, "name": "Drama"}],
            [],
        ],
    })
    lookup, link = build_lookup_and_link(meta, "genres", "id", "genre_id", "genre_name", "genres")

    assert lookup["genre_id"].tolist() == [10, 20]
    assert len(link) == 3
    assert set(link["movie_id"]) == {1, 2}


def test_build_lookup_and_link_stops_when_one_id_has_two_names():
    meta = pd.DataFrame({
        "id": [1, 2],
        "genres": [[{"id": 10, "name": "Drama"}], [{"id": 10, "name": "Dramas"}]],
    })
    with pytest.raises(ValueError):
        build_lookup_and_link(meta, "genres", "id", "genre_id", "genre_name", "genres")


def test_people_prefer_the_latin_spelling_and_gender_zero_becomes_missing():
    credits = pd.DataFrame({
        "id": [1, 2],
        "cast": [
            [{"credit_id": "c1", "id": 9, "name": "Моррис Честнат", "gender": 2,
              "character": "A", "order": 0, "cast_id": 1, "profile_path": None}],
            [],
        ],
        "crew": [
            [],
            [{"credit_id": "c2", "id": 9, "name": "Morris Chestnut", "gender": 0,
              "department": "Directing", "job": "Director", "profile_path": None}],
        ],
    })
    people, movie_cast, movie_crew = build_people_tables(credits)

    assert people["name"].tolist() == ["Morris Chestnut"]
    assert movie_cast["gender"].iloc[0] == 2
    assert pd.isna(movie_crew["gender"].iloc[0])


# ---------- the bridge and the join (C09, C11, C12, C14) ----------

def test_safe_bridge_excludes_unsafe_rows_and_the_join_reports_the_loss():
    movies = pd.DataFrame({"movie_id": pd.array([100, 200], dtype="Int64")})
    movie_links = pd.DataFrame({
        "movielens_id": [1, 2, 3, 4],
        "imdb_id": ["tt0000001", "tt0000002", "tt0000003", "tt0000004"],
        "movie_id": pd.array([100, 200, 200, 999], dtype="Int64"),
        "shared_tmdb_id": [False, True, True, False],
    })
    safe, excluded = build_safe_bridge(movie_links, movies)

    assert safe["movielens_id"].tolist() == [1]
    assert sorted(excluded["exclusion_reason"]) == [
        "shared_tmdb_id", "shared_tmdb_id", "tmdb_id_not_in_metadata",
    ]

    ratings = pd.DataFrame({"user_id": [1, 1, 2, 2], "movielens_id": [1, 2, 3, 1]})
    summary = link_ratings_to_movies(ratings, safe)

    assert summary["rating_rows_reachable"] == 2
    assert summary["rating_rows_lost"] == 2
    assert summary["rated_movies"] == 3
    assert summary["rated_movies_reachable"] == 1


def test_the_join_stops_when_the_bridge_repeats_a_movielens_id():
    bridge = pd.DataFrame({
        "movielens_id": [1, 1],
        "movie_id": pd.array([100, 200], dtype="Int64"),
    })
    with pytest.raises(ValueError):
        link_ratings_to_movies(pd.DataFrame({"movielens_id": [1]}), bridge)

# ---------- writing whole numbers (Stage 3) ----------

def test_cast_integer_columns_writes_whole_numbers_without_decimals():
    table = pd.DataFrame({"movie_id": [1, 2], "budget": [4_000_000.0, np.nan], "popularity": [7.0, 3.5]})
    result = cast_integer_columns(table, ["budget"])
    text = result.to_csv(index=False, lineterminator="\n")
    # budget has no ".0" and the missing value is an empty field; popularity keeps its decimals
    assert text == "movie_id,budget,popularity\n1,4000000,7.0\n2,,3.5\n"
    # the original table is not changed
    assert table["budget"].dtype == "float64"


def test_cast_integer_columns_refuses_a_value_with_decimals():
    table = pd.DataFrame({"runtime": [81.5]})
    with pytest.raises((TypeError, ValueError)):
        cast_integer_columns(table, ["runtime"])