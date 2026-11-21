import logging

from src.scripts.stage2_modules.stage2_clean_metadata import clean_movies_metadata
from src.scripts.stage2_modules.stage2_clean_credits import clean_credits
from src.scripts.stage2_modules.stage2_clean_keywords import clean_keywords
from src.scripts.stage2_modules.stage2_clean_links import clean_links
from src.scripts.stage2_modules.stage2_clean_ratings import clean_ratings
from src.scripts.stage2_modules.stage2_build_tables import (
    build_movies_table,
    build_genre_tables,
    build_company_tables,
    build_country_tables,
    build_language_tables,
    build_keyword_tables,
    build_people_tables,
    build_links_table,
    build_ratings_table,
)
from src.scripts.stage2_modules.stage2_join_tables import (
    build_safe_bridge,
    add_imdb_conflict_flag,
    link_ratings_to_movies,
)

logger = logging.getLogger(__name__)


def build_all_tables(tables):
    """Clean every raw table and build the final tables.

    The raw tables are removed from the dictionary as they are used, to save memory.
    """
    # Metadata: one clean table, then the movies table and four list tables
    clean_meta = clean_movies_metadata(tables.pop("movies_metadata"))
    movies = build_movies_table(clean_meta)
    genres, movie_genres = build_genre_tables(clean_meta)
    companies, movie_companies = build_company_tables(clean_meta)
    countries, movie_countries = build_country_tables(clean_meta)
    languages, movie_languages = build_language_tables(clean_meta)
    del clean_meta

    # Keywords and credits
    keywords, movie_keywords = build_keyword_tables(clean_keywords(tables.pop("keywords")))
    people, movie_cast, movie_crew = build_people_tables(clean_credits(tables.pop("credits")))

    # Bridge: split safe from unsafe rows, then flag IMDb conflicts
    movie_links = build_links_table(clean_links(tables.pop("links")))
    safe_bridge, excluded = build_safe_bridge(movie_links, movies)
    safe_bridge = add_imdb_conflict_flag(safe_bridge, movies)

    # Ratings, and a proof that they can reach movies through the safe bridge
    ratings = build_ratings_table(clean_ratings(tables.pop("ratings")))
    coverage = link_ratings_to_movies(ratings, safe_bridge)

    final_tables = {
        "movies": movies,
        "genres": genres,
        "movie_genres": movie_genres,
        "production_companies": companies,
        "movie_production_companies": movie_companies,
        "production_countries": countries,
        "movie_production_countries": movie_countries,
        "spoken_languages": languages,
        "movie_spoken_languages": movie_languages,
        "keywords": keywords,
        "movie_keywords": movie_keywords,
        "people": people,
        "movie_cast": movie_cast,
        "movie_crew": movie_crew,
        "movie_links": safe_bridge,
        "movie_links_excluded": excluded,
        "ratings": ratings,
    }

    logger.info("build_all_tables: built %s tables.", len(final_tables))
    return final_tables, coverage
