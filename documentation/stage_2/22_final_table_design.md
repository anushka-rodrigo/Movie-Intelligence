# Stage 2 — Final Table Design (Step 14)

## 1. Purpose

After cleaning, each table is correct but still has lists inside cells (`genres`, `cast`, `keywords` and so on). Lists cannot be saved properly to CSV, cannot be grouped in SQL, and cannot be linked to other tables.

This document records how the cleaned data is reshaped before it is saved, so that the processed datasets are ready for the database in Stage 3 and the SQL work in Stage 4.

## 2. The idea: many-to-many and grain

A movie has many genres, and a genre has many movies. This is a **many-to-many** relationship. The standard solution is a **link table** with one row per pair:

```text
movie_genres:  movie 862 -> Animation
               movie 862 -> Comedy
               movie 862 -> Family
```

Every table must have a **grain**: it must be possible to finish the sentence "one row represents ___". A table that cannot be described that way is mixing two things.

## 3. The final tables

| Table | One row represents | Key |
|---|---|---|
| `movies` | one movie | `movie_id` |
| `genres` | one genre | `genre_id` |
| `movie_genres` | one movie-genre pair | (`movie_id`, `genre_id`) |
| `production_companies` | one company | `company_id` |
| `movie_production_companies` | one movie-company pair | (`movie_id`, `company_id`) |
| `production_countries` | one country | country code |
| `movie_production_countries` | one movie-country pair | (`movie_id`, country code) |
| `spoken_languages` | one language | language code |
| `movie_spoken_languages` | one movie-language pair | (`movie_id`, language code) |
| `keywords` | one keyword | `keyword_id` |
| `movie_keywords` | one movie-keyword pair | (`movie_id`, `keyword_id`) |
| `people` | one person | `person_id` |
| `movie_cast` | one cast credit | `credit_id` |
| `movie_crew` | one crew credit | `credit_id` |
| `movie_links` | one MovieLens-to-TMDB mapping | `movielens_id` |
| `ratings` | one user's rating of one movie | (`user_id`, `movielens_id`) |

`belongs_to_collection` is not many-to-many, because a movie is in at most one collection. It stays in `movies` as two plain columns, `collection_id` and `collection_name`.

The company, country, language, keyword, cast and crew tables are included because the analytical questions need them (E4 and I3 companies, E6 countries, E7 languages, R1 keywords, cast and crew, I2 directors).

## 4. Decisions

1. **All seven list columns become tables.** The analytical questions use all of them.
2. **Cast and crew keep every credit**, including the billing `order`, so that later analysis decides who counts (for example directors for question I2).
3. **Naming convention.** `movie_id` always means the TMDB id, and the MovieLens id is always called `movielens_id`. Because the two ids have different names, the mistake that Stage 1 warned about (C09, joining ratings straight to metadata) cannot be typed by accident.
4. **Columns dropped (C28):** `homepage` and `poster_path` from `movies`, and `profile_path` from the people records. They are image and web links with no analytical use.

## 5. Checks required when the tables are built

The lookup tables are built by collecting the dictionaries from every movie, so each entry appears many times. Building them must prove:

- **Each id maps to exactly one name.** If genre id 35 were ever "Comedy" in one place and something else in another, the lookup would be ambiguous.
- **Each person id maps to one name**, for cast and crew.
- **Nothing is lost or invented.** The number of link-table rows must equal the total number of list entries before splitting.
- **No repeated pairs.** A movie cannot appear twice for the same genre, company, country, language or keyword.

## 6. Result

**The shape of the processed data is decided.** Next, each table pattern is built and verified one at a time, starting with genres. The other list columns follow the same recipe.
