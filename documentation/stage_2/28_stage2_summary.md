# Stage 2 — Summary: the Reproducible ETL Pipeline

## 1. What was built

One command turns the five raw Kaggle files into 17 clean, validated tables:

```powershell
python -m src.scripts.stage2_pipeline
```

```text
Verify raw fingerprints
        |
     Extract        read the five raw files, check their row counts
        |
      Clean         repair, de-duplicate, fix types, handle placeholders, parse lists
        |
    Transform       split lists into tables, rename ids, build a safe bridge
        |
     Validate       89 automatic checks, nothing is saved if one fails
        |
       Load         write 17 CSV files and a manifest to data/processed
        |
Re-verify raw fingerprints
```

The raw data in `data/raw_data/` is never modified. The processed data in `data/processed/` is always rebuilt from it by the pipeline, never edited by hand.

## 2. Milestone 2 checklist

| Requirement | Evidence |
|---|---|
| ETL scripts work from raw data | The pipeline reads only `data/raw_data/` and completes in 77 to 87 seconds |
| Cleaning is reproducible | Every rule is a function, tested by 16 pytest tests (document 27) |
| Validation checks exist | 89 checks pass, 0 fail (document 25) |
| Raw data remains untouched | Fingerprints are verified at the start and the end of every run (document 11) |
| Running the ETL twice gives consistent results | All 17 output files had identical SHA-256 hashes across two runs: **REPRODUCIBLE** (document 27) |

## 3. From raw to processed

| Raw file | Raw rows | After cleaning |
|---|---:|---|
| `movies_metadata.csv` | 45,466 | 45,433 movies (3 broken records repaired, 30 duplicate copies removed) |
| `credits.csv` | 45,476 | 45,432 (44 duplicates removed) |
| `keywords.csv` | 46,419 | 45,432 (987 duplicates removed) |
| `links.csv` | 45,843 | 45,404 safe + 220 quarantined (219 had no TMDB id and were dropped earlier) |
| `ratings.csv` | 26,024,289 | 26,024,289 (unchanged, timestamp converted) |

## 4. The 17 processed tables

One row represents the thing in the second column. Keys are in the third.

| Table | One row represents | Key | Columns |
|---|---|---|---|
| `movies` | one movie | `movie_id` | `movie_id`, `imdb_id`, `title`, `original_title`, `original_language`, `overview`, `tagline`, `status`, `release_date`, `runtime`, `budget`, `revenue`, `popularity`, `vote_average`, `vote_count`, `adult`, `video`, `collection_id`, `collection_name`, and four flags: `budget_review`, `revenue_review`, `long_runtime`, `vote_average_zero_with_votes` |
| `genres` | one genre | `genre_id` | `genre_id`, `genre_name` |
| `movie_genres` | one movie-genre pair | both ids | `movie_id`, `genre_id` |
| `production_companies` | one company | `company_id` | `company_id`, `company_name` |
| `movie_production_companies` | one movie-company pair | both ids | `movie_id`, `company_id` |
| `production_countries` | one country | `country_code` | `country_code`, `country_name` |
| `movie_production_countries` | one movie-country pair | both ids | `movie_id`, `country_code` |
| `spoken_languages` | one language | `language_code` | `language_code`, `language_name` |
| `movie_spoken_languages` | one movie-language pair | both ids | `movie_id`, `language_code` |
| `keywords` | one keyword | `keyword_id` | `keyword_id`, `keyword_name` |
| `movie_keywords` | one movie-keyword pair | both ids | `movie_id`, `keyword_id` |
| `people` | one person | `person_id` | `person_id`, `name` |
| `movie_cast` | one cast credit | `credit_id` | `credit_id`, `movie_id`, `person_id`, `character`, `order`, `gender` |
| `movie_crew` | one crew credit | `credit_id` | `credit_id`, `movie_id`, `person_id`, `department`, `job`, `gender` |
| `movie_links` | one safe MovieLens-to-TMDB mapping | `movielens_id` | `movielens_id`, `imdb_id`, `movie_id`, `imdb_conflict` |
| `movie_links_excluded` | one mapping that cannot be trusted | `movielens_id` | `movielens_id`, `imdb_id`, `movie_id`, `shared_tmdb_id`, `exclusion_reason` |
| `ratings` | one user's rating of one movie | `user_id`, `movielens_id` | `user_id`, `movielens_id`, `rating`, `timestamp` |

**Naming rule:** `movie_id` always means the TMDB id, and `movielens_id` always means the MovieLens id. The two are different id systems, so ratings must reach `movies` through `movie_links`.

## 5. Where each part is documented

| Topic | Document |
|---|---|
| Extraction, fingerprints, logging and entry point | 10, 11, 12 |
| Repairing the 3 split records | 13 |
| Duplicate movies | 14 |
| Data types | 15 |
| Placeholders and flags | 16 |
| Parsing list columns | 17 |
| Cleaning credits, keywords, links, ratings | 18, 19, 20, 21 |
| Final table design and how the tables were built | 22, 23 |
| Connecting the tables | 24 |
| Validation | 25 |
| Loading | 26 |
| Tests and reproducibility | 27 |

The cleaning decisions (C01 to C30) are in `documentation/stage_1/7_cleaning_decisions.md`.

## 6. Things to remember when using the data

- **52,160 ratings (0.20%) cannot be linked to a movie.** They belong to movies in `movie_links_excluded` or without any bridge row. They are kept in `ratings`, and any analysis that goes through `movies` simply does not see them. 44,682 of the 45,115 rated movies are reachable.
- **Gender is unknown for 48% of credits.** TMDB's gender `0` means "not specified", and it became missing. Any gender analysis has a very large unknown group.
- **Release dates run to 2020.** The dataset was collected around 2017, so later dates are movies marked as planned or rumoured. Filter on `status` for time-based analysis.
- **Empty lists mean unknown, not none.** A movie with no rows in `movie_genres`, `movie_keywords` or the cast table has an unknown value, not a confirmed absence (C24).
- **`budget` and `revenue` are missing for most movies** (36,797 and 38,189 of 45,433). Values below 1,000 were treated as placeholders, and values from 1,000 to 10,000 are flagged for review but kept.
- **65 bridge rows carry `imdb_conflict = True`.** 63 are IMDb ids that `links` has never seen. 2 are a genuine swap between two movies (TMDB 22488 and 20583) that has not been reviewed by hand.
- **15 people had two spellings of their name.** The Latin-alphabet spelling was kept.

## 7. Known limitations

- The expected counts in the validation are fixed numbers. They protect against surprises, but a different version of the dataset would need them updated on purpose.
- The fingerprint script reports with `print` instead of the log, so its output appears in the terminal but not in the log file.
- Reproducibility is proven on one machine. Identical hashes would not necessarily hold under different versions of pandas or Python.
- The swapped IMDb ids (C17) are flagged but unresolved.

## 8. Handoff to Stage 3

Stage 3 loads these CSV files into PostgreSQL.

- Every table has a declared key, and the 15 foreign-key relationships between tables were validated, so they can be enforced in the database.
- **Do not enforce a foreign key from `ratings.movielens_id` to `movie_links`.** 52,160 ratings have no safe bridge row, so it would reject them. Join through the bridge instead, and report the loss.
- CSV files load directly with PostgreSQL's `COPY`. Missing values are empty fields. Dates and timestamps are in ISO format.
- To rebuild everything: `python -m src.scripts.stage2_pipeline` (about 80 seconds, with the raw data in `data/raw_data/`).

## 9. Result

**Stage 2 is complete.** The raw Kaggle files become 17 clean, validated, documented tables with one command. The same command always gives the same files, and the raw data is provably untouched.
