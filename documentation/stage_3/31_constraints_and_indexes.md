# Stage 3: Schema, Delete Rules and Indexes

**Project:** Movie Intelligence
**Stage:** 3, Design the PostgreSQL Database (step: design decisions)
**Builds on:** `29_data_types.md` (columns, keys, constraints) and `30_er_diagram.md` (relationships)

## 1. Purpose

Documents 29 and 30 decided what each table contains and how the tables connect. This document decides three further things before any SQL is written:

1. What the database does when a row that other rows depend on is **deleted**.
2. **Where** the tables live inside the database.
3. Which **indexes** exist, and why each one is there.

## 2. Decisions

| # | Decision | Reason |
|---|---|---|
| D21 | Foreign keys that point **at `movies`** use `ON DELETE CASCADE`. | A link or credit row only has meaning because of the movie it describes. Deleting the movie deletes only the rows with that `movie_id`. The parent rows (genres, people and so on) stay, because other movies still use them. |
| D22 | Foreign keys that point **at a lookup table** use `ON DELETE RESTRICT`, written explicitly. | A genre, person, company, country or language *defines* the movies attached to it. Deleting one while it is in use would silently remove credits or labels. A lookup row can still be **renamed** (`UPDATE`) at any time, and a row nobody uses can still be deleted. |
| D23 | `movies.original_language` uses `ON DELETE RESTRICT`, not `SET NULL`. | Language defines the movie, so it must not become "unknown" silently. |
| D24 | No `ON UPDATE` rule is set. | The ids never change, so the default is enough. |
| D25 | All 17 tables live in one dedicated schema called `movie_intelligence`, not in `public`. | The whole database can be dropped and rebuilt in one step, new PostgreSQL versions restrict who can create tables in `public`, and the later API can be given access to this schema only. A search path is set once so queries do not need the schema prefix. |
| D26 | Extra indexes are built only where a foreign key column would otherwise have none, on tables large enough to matter (section 4). Analytical indexes (such as `release_date`) wait until a slow query proves they are needed. | Every index costs disk space and slows the load. PostgreSQL indexes primary keys and `UNIQUE` columns automatically, but **not** foreign key columns. |
| D27 | The index on `ratings.movielens_id` is built **after** the data is loaded. | Building an index once on finished data is much faster than updating it 26 million times during the load. The same principle applies to the primary key and foreign keys of the large tables (to be finalized in Phase D). |

## 3. Delete rule of every foreign key

### 3.1 Pointing at `movies`: `CASCADE` (8 foreign keys)

| Child table | Column |
|---|---|
| `movie_genres` | `movie_id` |
| `movie_keywords` | `movie_id` |
| `movie_production_companies` | `movie_id` |
| `movie_production_countries` | `movie_id` |
| `movie_spoken_languages` | `movie_id` |
| `movie_cast` | `movie_id` |
| `movie_crew` | `movie_id` |
| `movie_links` | `movie_id` |

Side effect of `movie_links`: deleting a movie also deletes its bridge row, so that movie's ratings join to nothing and count as unlinked. That is acceptable, because `ratings` has no foreign key by design.

### 3.2 Pointing at a lookup table: `RESTRICT` (8 foreign keys)

| Child table | Column | Parent table |
|---|---|---|
| `movie_genres` | `genre_id` | `genres` |
| `movie_keywords` | `keyword_id` | `keywords` |
| `movie_production_companies` | `company_id` | `production_companies` |
| `movie_production_countries` | `country_code` | `production_countries` |
| `movie_spoken_languages` | `language_code` | `spoken_languages` |
| `movie_cast` | `person_id` | `people` |
| `movie_crew` | `person_id` | `people` |
| `movies` | `original_language` | `spoken_languages` |

### 3.3 The rule in one line

> **Deleting the thing a row *describes* (a movie) cascades. Deleting a thing a row merely *refers to* (a genre, a person) is refused.**

Removing one person's credit from one movie means deleting a row in `movie_cast` or `movie_crew` (the child), which is always allowed. `RESTRICT` blocks deleting the person row itself (the parent).

## 4. Index plan

### 4.1 Indexes PostgreSQL creates automatically

| Source | Tables |
|---|---|
| Primary keys | all 17 tables |
| `UNIQUE` constraints | `genres.genre_name`, `keywords.keyword_name`, `movies.imdb_id`, `movie_links.imdb_id`, `movie_links.movie_id` |

The composite primary key of a link table is sorted by its first column. `(movie_id, genre_id)` serves lookups that start with `movie_id`, and the `UNIQUE` index on `movie_links.movie_id` serves the cascade from `movies`.

### 4.2 Extra indexes to build (10)

| Table | Index on | Why it is needed |
|---|---|---|
| `movie_genres` | `genre_id` | "All movies in a genre", and the `RESTRICT` check when a genre is deleted. |
| `movie_keywords` | `keyword_id` | Same, for keywords. |
| `movie_production_companies` | `company_id` | Same, for companies. |
| `movie_production_countries` | `country_code` | Same, for countries. |
| `movie_spoken_languages` | `language_code` | Same, for languages. |
| `movie_cast` | `movie_id` | "Cast of a movie", and the cascade when a movie is deleted. Its primary key `credit_id` is unrelated to movies or people. |
| `movie_cast` | `person_id` | "Movies of a person", and the `RESTRICT` check when a person is deleted. |
| `movie_crew` | `movie_id` | Same as cast. |
| `movie_crew` | `person_id` | Same as cast. |
| `ratings` | `movielens_id` | "All ratings of a movie". The primary key `(user_id, movielens_id)` is sorted by user first and cannot answer this. Built after the load (D27). Roughly half a gigabyte. |

### 4.3 Deliberately not indexed

| Column | Reason |
|---|---|
| `credit_id` in `movie_cast` and `movie_crew` | Already indexed as the primary key, and nobody searches by it. |
| `movies.original_language` | `movies` has only 45,433 rows, so a full scan is cheap. |
| Analytical columns (`release_date`, `budget`, `revenue`, `vote_average`) | Wait for evidence. In Stage 4, `EXPLAIN` shows whether a query is slow, and an index is added if it helps. |

## 5. Open items before building the schema

- [ ] Confirm the database encoding is `UTF8` (`SHOW server_encoding;`)
- [ ] Fix the `.0` export in Stage 2 and confirm the new `movies.csv`
- [ ] Confirm the first lines of `ratings.csv` (rating format, ISO timestamps with seconds)
- [ ] Write the schema as a SQL file in the repository (Phase C)
