# Stage 3 — PostgreSQL Data Types

## 1. Purpose

The processed CSV files have no types, only text. PostgreSQL needs a type for every column and rejects any value that does not fit. The pandas types chosen in Stage 2 (document 15) describe data in Python memory, so the database types are a separate decision.

This document records the type, the missing-value rule (`NULL` or `NOT NULL`) and the constraints for all 17 processed tables. It is the input for the ER diagram, the schema file and the load.

## 2. Rules used for every column

1. **Be honest about the data.** A whole number is not stored as a decimal, and a date is not stored as text.
2. **Size for the largest real value.** The largest value in the data decides between `SMALLINT`, `INTEGER` and `BIGINT`.
3. **Missing becomes `NULL`.** A column is `NOT NULL` only when the processed data has no missing values and the column should never have any.
4. **Types must match across a foreign key.** Every id type is chosen once and reused: ids are `INTEGER`, except `credit_id` and the language and country codes, which are `TEXT`.
5. **`TEXT` for text.** `TEXT` and `VARCHAR(n)` perform the same in PostgreSQL, and no column has a real length limit.
6. **`UNIQUE` only where the data really is unique.** Names of people and companies repeat, so they are not unique.
7. **Avoid reserved or confusing column names.** `order` and `timestamp` are renamed (section 5).

## 3. The tables

Tables are listed in load order: tables that are pointed at come before the tables that point at them.

### 3.1 Lookup tables

#### `genres` (20 rows)

| Column | Type | Allow NULL? | Constraint |
|---|---|---|---|
| `genre_id` | `INTEGER` | No | `PRIMARY KEY` |
| `genre_name` | `TEXT` | No | `UNIQUE` |

#### `keywords` (19,956 rows)

| Column | Type | Allow NULL? | Constraint |
|---|---|---|---|
| `keyword_id` | `INTEGER` | No | `PRIMARY KEY` |
| `keyword_name` | `TEXT` | No | `UNIQUE` |

#### `people` (353,343 rows)

| Column | Type | Allow NULL? | Constraint |
|---|---|---|---|
| `person_id` | `INTEGER` | No | `PRIMARY KEY` |
| `name` | `TEXT` | No | None |

#### `production_companies` (23,693 rows)

| Column | Type | Allow NULL? | Constraint |
|---|---|---|---|
| `company_id` | `INTEGER` | No | `PRIMARY KEY` |
| `company_name` | `TEXT` | No | None |

#### `production_countries` (161 rows)

| Column | Type | Allow NULL? | Constraint |
|---|---|---|---|
| `country_code` | `TEXT` | No | `PRIMARY KEY` |
| `country_name` | `TEXT` | No | None |

#### `spoken_languages` (133 rows)

| Column | Type | Allow NULL? | Constraint |
|---|---|---|---|
| `language_code` | `TEXT` | No | `PRIMARY KEY` |
| `language_name` | `TEXT` | Yes | None |

### 3.2 The core table

#### `movies` (45,433 rows)

| Column | Type | Allow NULL? | Constraint |
|---|---|---|---|
| `movie_id` | `INTEGER` | No | `PRIMARY KEY` |
| `imdb_id` | `TEXT` | Yes | `UNIQUE` |
| `title` | `TEXT` | No | None |
| `original_title` | `TEXT` | No | None |
| `original_language` | `TEXT` | Yes | FK → `spoken_languages` |
| `overview` | `TEXT` | Yes | None |
| `tagline` | `TEXT` | Yes | None |
| `status` | `TEXT` | Yes | `CHECK (status IN ('Released', 'Rumored', 'Post Production', 'In Production', 'Planned', 'Canceled'))` |
| `release_date` | `DATE` | Yes | None |
| `runtime` | `SMALLINT` | Yes | `CHECK (runtime > 0)` |
| `budget` | `BIGINT` | Yes | `CHECK (budget > 0)` |
| `revenue` | `BIGINT` | Yes | `CHECK (revenue > 0)` |
| `popularity` | `DOUBLE PRECISION` | No | `CHECK (popularity >= 0)` |
| `vote_average` | `NUMERIC(3,1)` | Yes | `CHECK (vote_average BETWEEN 0 AND 10)` |
| `vote_count` | `INTEGER` | No | `CHECK (vote_count >= 0)` |
| `adult` | `BOOLEAN` | No | None |
| `video` | `BOOLEAN` | No | None |
| `collection_id` | `INTEGER` | Yes | Table-level `CHECK ((collection_id IS NULL) = (collection_name IS NULL))` |
| `collection_name` | `TEXT` | Yes | Covered by the same table-level `CHECK` |
| `budget_review` | `BOOLEAN` | No | None |
| `revenue_review` | `BOOLEAN` | No | None |
| `long_runtime` | `BOOLEAN` | No | None |
| `vote_average_zero_with_votes` | `BOOLEAN` | No | None |

### 3.3 Link tables (many-to-many)

#### `movie_genres` (91,015 rows, one movie-genre pair per row)

| Column | Type | Allow NULL? | Constraint |
|---|---|---|---|
| `movie_id` | `INTEGER` | No | Part of composite primary key, FK → `movies` |
| `genre_id` | `INTEGER` | No | Part of composite primary key, FK → `genres` |

#### `movie_keywords` (156,602 rows)

| Column | Type | Allow NULL? | Constraint |
|---|---|---|---|
| `movie_id` | `INTEGER` | No | Part of composite primary key, FK → `movies` |
| `keyword_id` | `INTEGER` | No | Part of composite primary key, FK → `keywords` |

#### `movie_production_companies` (70,476 rows)

| Column | Type | Allow NULL? | Constraint |
|---|---|---|---|
| `movie_id` | `INTEGER` | No | Part of composite primary key, FK → `movies` |
| `company_id` | `INTEGER` | No | Part of composite primary key, FK → `production_companies` |

#### `movie_production_countries` (49,375 rows)

| Column | Type | Allow NULL? | Constraint |
|---|---|---|---|
| `movie_id` | `INTEGER` | No | Part of composite primary key, FK → `movies` |
| `country_code` | `TEXT` | No | Part of composite primary key, FK → `production_countries` |

#### `movie_spoken_languages` (53,269 rows)

| Column | Type | Allow NULL? | Constraint |
|---|---|---|---|
| `movie_id` | `INTEGER` | No | Part of composite primary key, FK → `movies` |
| `language_code` | `TEXT` | No | Part of composite primary key, FK → `spoken_languages` |

### 3.4 Credit tables

#### `movie_cast` (562,044 rows, one cast credit per row)

| Column | Type | Allow NULL? | Constraint |
|---|---|---|---|
| `credit_id` | `TEXT` | No | `PRIMARY KEY` |
| `movie_id` | `INTEGER` | No | FK → `movies` |
| `person_id` | `INTEGER` | No | FK → `people` |
| `character` | `TEXT` | Yes | None (25,767 missing) |
| `cast_order` (CSV header: `order`) | `SMALLINT` | No | `CHECK (cast_order >= 0)` |
| `gender` | `SMALLINT` | Yes | `CHECK (gender IN (1, 2))` |

#### `movie_crew` (463,836 rows, one crew credit per row)

| Column | Type | Allow NULL? | Constraint |
|---|---|---|---|
| `credit_id` | `TEXT` | No | `PRIMARY KEY` |
| `movie_id` | `INTEGER` | No | FK → `movies` |
| `person_id` | `INTEGER` | No | FK → `people` |
| `department` | `TEXT` | No | None |
| `job` | `TEXT` | No | None |
| `gender` | `SMALLINT` | Yes | `CHECK (gender IN (1, 2))` |

### 3.5 The MovieLens side

#### `movie_links` (45,404 rows, the safe MovieLens-to-TMDB bridge)

| Column | Type | Allow NULL? | Constraint |
|---|---|---|---|
| `movielens_id` | `INTEGER` | No | `PRIMARY KEY` |
| `imdb_id` | `TEXT` | No | `UNIQUE` |
| `movie_id` | `INTEGER` | No | `UNIQUE`, FK → `movies` |
| `imdb_conflict` | `BOOLEAN` | No | None |

#### `movie_links_excluded` (220 rows, mappings that cannot be trusted)

| Column | Type | Allow NULL? | Constraint |
|---|---|---|---|
| `movielens_id` | `INTEGER` | No | `PRIMARY KEY` |
| `imdb_id` | `TEXT` | No | None |
| `movie_id` | `INTEGER` | No | **No foreign key** |
| `shared_tmdb_id` | `BOOLEAN` | No | None |
| `exclusion_reason` | `TEXT` | No | `CHECK (exclusion_reason IN ('shared_tmdb_id', 'tmdb_id_not_in_metadata'))` |

#### `ratings` (26,024,289 rows)

| Column | Type | Allow NULL? | Constraint |
|---|---|---|---|
| `user_id` | `INTEGER` | No | Part of composite primary key |
| `movielens_id` | `INTEGER` | No | Part of composite primary key, **no foreign key** |
| `rating` | `NUMERIC(2,1)` | No | `CHECK (rating BETWEEN 0.5 AND 5.0)` |
| `rated_at` (CSV header: `timestamp`) | `TIMESTAMP` | No | None |

## 4. Design decisions and the reasons

| # | Decision | Reason |
|---|---|---|
| D1 | All ids are `INTEGER`. | The largest id is 1,908,262 (`person_id`), which is over `SMALLINT`'s limit of 32,767 and far below `INTEGER`'s 2.1 billion. One type everywhere avoids mismatches across foreign keys. |
| D2 | Ids are loaded as given, never auto-numbered. | They are TMDB and MovieLens ids, not ours. |
| D3 | `revenue` is `BIGINT`, and so is `budget`. | The largest revenue is 2,787,965,087, which is over the `INTEGER` limit of 2,147,483,647. |
| D4 | `runtime` is `SMALLINT`. | All values are whole numbers from 1 to 1,256. |
| D5 | `vote_average` is `NUMERIC(3,1)`. | Every value has one decimal, and `NUMERIC` stores it exactly. Zeros were turned into missing in Stage 2, so the minimum is 0.5. |
| D6 | `popularity` is `DOUBLE PRECISION`. | It is a computed score with up to 6 decimals, where a tiny rounding error is acceptable. The 4-byte `REAL` would round values such as 547.488298. |
| D7 | `rating` is `NUMERIC(2,1)`. | Only 10 values exist (0.5 to 5.0 in half steps), and `NUMERIC` stores them exactly. `REAL` is a smaller and faster alternative, since half steps are exact in binary. To be compared when query plans are studied in Stage 4. |
| D8 | `rated_at` is `TIMESTAMP`, not `TIMESTAMPTZ`. Values are UTC. | The CSV text has no timezone. With `TIMESTAMPTZ`, PostgreSQL would assume the computer's timezone and shift every rating. |
| D9 | `gender` is `SMALLINT` with `CHECK (gender IN (1, 2))`, nullable. | Only 1 and 2 exist (TMDB: 1 is female, 2 is male). The Stage 2 "not specified" `0` became missing (40% of cast, 59% of crew). |
| D10 | `UNIQUE` only on `genre_name`, `keyword_name`, `imdb_id` (in both `movies` and `movie_links`) and `movie_links.movie_id`. | These are really unique in the data. Not on `people.name`, `company_name` or `country_name` (two countries are named "Congo"). |
| D11 | `UNIQUE` on `movies.imdb_id` allows several missing values. | In PostgreSQL a missing value never equals another missing value. |
| D12 | `UNIQUE` on `movie_links.movie_id`. | The Stage 2 safe bridge promises one MovieLens id per movie. The database now enforces that promise. |
| D13 | No foreign key from `ratings.movielens_id`. | 52,160 ratings (0.20%) have no safe bridge row, and a foreign key would reject them. Join through `movie_links` and report the loss. |
| D14 | No `users` table and no foreign key on `ratings.user_id`. (Departure from the Stage 0 plan.) | MovieLens has no user attributes. A table of ids copied from `ratings` would have nothing to validate against. Revisit if the recommender needs user data. |
| D15 | `movie_links_excluded` has no foreign keys. | A quarantine table. 161 of its 220 rows have a TMDB id that is not in `movies`, so a foreign key would reject the very rows it exists to record. |
| D16 | `movies.original_language` has a foreign key to `spoken_languages`. | All 89 values were checked and all exist there. |
| D17 | `movies.status` is limited by `CHECK`, not by a lookup table. | There are only 6 values, and a separate table would add complexity for no gain. |
| D18 | `collection_id` and `collection_name` stay in `movies`, with a `CHECK` that they are missing together. | 90% are missing. A separate `collections` table is the fully normalized alternative and was rejected in Stage 2 as not worth the extra table. |
| D19 | `department` stays plain `TEXT`. | Only 12 values, and nothing in the analytical questions needs a lookup table. |
| D20 | `order` becomes `cast_order` and `timestamp` becomes `rated_at`. | `ORDER` is a reserved SQL word, and `TIMESTAMP` is a type name. The load reads columns by position, so the CSV headers can stay as they are. |

## 5. Things that can go wrong

- **The country code `NA` (Namibia).** pandas reads the text `NA` as missing by default. In `movie_production_countries.csv`, three rows are `NA`. PostgreSQL's `COPY` loads them correctly as text, but any pandas read of these columns must use `keep_default_na=False`.
- **Whole numbers written as floats.** The CSV writes `budget`, `revenue`, `runtime` and `collection_id` as `4000000.0`, `69.0` and `10.0`. PostgreSQL's `COPY` rejects these in integer columns. **Fix: write these columns as nullable integers (`Int64`) in the Stage 2 load step.** Status: **TODO** (re-run the pipeline, then check that `movies.csv` shows `4000000`).
- **Text encoding.** Some names contain accents and other scripts. The database must be UTF-8. Status: **TODO** (run `SHOW server_encoding;`).
- **Never open the processed CSVs in Excel and save them.** Excel cannot hold the 26 million rows of `ratings.csv`, and it rewrites dates.
- **The `ratings` primary key index is large** (26 million rows). The load order must be planned (Phase D).

## 6. Indexes to plan (Phase B, step 6)

The primary key index of a composite key only helps lookups that start with its first column.

| Table | Extra index to consider | Question it serves |
|---|---|---|
| `movie_genres` | `genre_id` | All movies in a genre |
| `movie_keywords` | `keyword_id` | All movies with a keyword |
| `movie_production_companies` | `company_id` | All movies of a company |
| `movie_production_countries` | `country_code` | All movies from a country |
| `movie_spoken_languages` | `language_code` | All movies in a language |
| `movie_cast`, `movie_crew` | `movie_id`, `person_id` | Credits of a movie, credits of a person |
| `ratings` | `movielens_id` | All ratings of a movie (expensive at 26 million rows, to be weighed deliberately) |

PostgreSQL indexes primary keys and `UNIQUE` columns automatically, but **not** foreign key columns.

## 7. Open items before moving on

- [ ] Fix the `.0` export in Stage 2 and confirm the new `movies.csv`
- [ ] Confirm the database encoding is `UTF8`
- [ ] Confirm the first lines of `ratings.csv` (rating format and ISO timestamps with seconds)
- [ ] Draw the ER diagram (next step)