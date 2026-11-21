"""Every final table: its key, its expected row count, and whether it is sorted before saving."""

TABLE_SPECS = {
    "movies": {"key": ["movie_id"], "rows": 45_433, "sort": True},
    "genres": {"key": ["genre_id"], "rows": 20, "sort": True},
    "movie_genres": {"key": ["movie_id", "genre_id"], "rows": 91_015, "sort": True},
    "production_companies": {"key": ["company_id"], "rows": 23_693, "sort": True},
    "movie_production_companies": {"key": ["movie_id", "company_id"], "rows": 70_476, "sort": True},
    "production_countries": {"key": ["country_code"], "rows": 161, "sort": True},
    "movie_production_countries": {"key": ["movie_id", "country_code"], "rows": 49_375, "sort": True},
    "spoken_languages": {"key": ["language_code"], "rows": 133, "sort": True},
    "movie_spoken_languages": {"key": ["movie_id", "language_code"], "rows": 53_269, "sort": True},
    "keywords": {"key": ["keyword_id"], "rows": 19_956, "sort": True},
    "movie_keywords": {"key": ["movie_id", "keyword_id"], "rows": 156_602, "sort": True},
    "people": {"key": ["person_id"], "rows": 353_343, "sort": True},
    "movie_cast": {"key": ["credit_id"], "rows": 562_044, "sort": True},
    "movie_crew": {"key": ["credit_id"], "rows": 463_836, "sort": True},
    "movie_links": {"key": ["movielens_id"], "rows": 45_404, "sort": True},
    "movie_links_excluded": {"key": ["movielens_id"], "rows": 220, "sort": True},
    # Ratings keep their file order: sorting 26 million rows is slow, and the order is already fixed
    "ratings": {"key": ["user_id", "movielens_id"], "rows": 26_024_289, "sort": False},
}
