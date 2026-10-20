# Data Dictionary

**Project:** Movie Intelligence
**Stage:** 1, Understand the Raw Data
**Dataset:** The Movies Dataset (Kaggle, rounakbanik): https://www.kaggle.com/datasets/rounakbanik/the-movies-dataset
**Last updated:** 2026-10-19
**Companion documents:** `4_metadata_summary.md` (data-quality report with all counts), `5_data_investigation_qa.md` (reasoning), `7_cleaning_decisions.md` (what we do about each problem)

> **About the meanings.** The file-level descriptions follow the dataset's Kaggle description (the Kaggle page itself did not load when this was written, so the file descriptions come from copies of it on other sites). The column-level meanings come from standard TMDB and MovieLens conventions, because the files do not ship with a column guide.

---

## 1. How to read this dictionary

| Term | Meaning |
|---|---|
| **Raw → Target** | The dtype pandas loaded, then the dtype the column should have after cleaning |
| **Missing** | Cells pandas sees as empty (NaN), with the percentage of rows |
| **Hidden missing** | Cells that look filled but carry no information, such as `'[]'`, `0`, or a placeholder value |
| **PK / FK** | Primary key (should identify one row) / foreign key (points to another table's key) |
| **(confirm)** | A meaning taken from TMDB conventions that the data itself cannot confirm |

**Verdicts**

| Verdict | Meaning |
|---|---|
| **Trust** | Use as it is |
| **Transform** | Real information, but it must be converted or repaired first |
| **Investigate** | Usable only with care, or a question is still open |
| **Ignore** | Not useful for this project, so it is left out of the cleaned table |

---

## 2. The files

| File | Rows | Columns | What it holds | Id system |
|---|---:|---:|---|---|
| `movies_metadata.csv` | 45,466 | 24 | The main movie table (TMDB data for the movies in the full MovieLens dataset) | TMDB |
| `credits.csv` | 45,476 | 3 | Cast and crew per movie, as text-encoded lists | TMDB |
| `keywords.csv` | 46,419 | 2 | Plot keywords per movie, as text-encoded lists | TMDB |
| `links.csv` | 45,843 | 3 | Translator between MovieLens ids and the TMDB and IMDb ids | MovieLens plus both |
| `links_small.csv` | 9,125 | 3 | Small version of `links` (about 9,000 movies) | MovieLens plus both |
| `ratings.csv` | 26,024,289 | 4 | User ratings from MovieLens (about 270,000 users) | MovieLens |
| `ratings_small.csv` | 100,004 | 4 | A 100,000-rating sample of `ratings`, with renumbered users | MovieLens |

The Kaggle description says the movie details, credits and keywords come from the TMDB open API, and the ratings come from MovieLens (GroupLens). That is why there are two id systems.

---

## 3. The three id systems

| Id system | Columns | Role in this project |
|---|---|---|
| **TMDB id** | `movies_metadata.id`, `credits.id`, `keywords.id`, `links.tmdbId` | **Backbone key** for everything about a movie |
| **MovieLens id** | `ratings.movieId`, `links.movieId` | Key for ratings only |
| **IMDb id** | `movies_metadata.imdb_id` (text `tt0114709`), `links.imdbId` (number `114709`) | **Cross-check only** |

`links` is the only table that holds both the MovieLens id and the TMDB id side by side, so it is the bridge:

`ratings.movieId` → `links.movieId` → `links.tmdbId` → `movies_metadata.id`

**Worked example:** to `ratings`, Toy Story is `1`. To `movies_metadata`, `credits` and `keywords`, it is `862`. Joining `ratings.movieId` straight to `movies_metadata.id` is wrong.

---

## 4. `movies_metadata.csv`

**Rows:** 45,466 raw. **Key:** `id` (TMDB). **Structure:** one row per movie, plus 30 extra copies of repeated ids and 3 records split across 6 physical rows.

| Column | Meaning | Raw → Target | Missing | Hidden missing and quality notes | Verdict |
|---|---|---|---:|---|---|
| `id` | TMDB movie id. **PK** of the project. | object → Int64 | 0 (0.00%) | 3 values are dates (corrupted rows). 30 extra copies. 45,433 unique numeric ids. | **Transform**, then trust |
| `imdb_id` | IMDb id as text, `tt` plus 7 digits | object → string | 17 (0.04%) | 32 real repeats. At least one value is the placeholder `'0'`. 64 values not found in `links`. | **Transform**, cross-check only |
| `title` | Display title of the movie | object → string | 6 (0.01%) | The 6 missing are exactly the 6 physical rows of the corrupted records. Titles repeat naturally. | **Trust** |
| `original_title` | Title in the original language | object → string | 0 (0.00%) | None known | **Trust** |
| `original_language` | Original language, as a 2-letter ISO 639-1 code | object → category | 11 (0.02%) | 92 distinct values | **Trust** |
| `overview` | Plot summary text | object → string | 954 (2.10%) | 3 overviews are split across two rows (corrupted records) | **Trust** after repair |
| `tagline` | Marketing tagline | object → string | 25,054 (55.10%) | Sparse | **Trust** (sparse) |
| `release_date` | Release date | object → datetime | 87 (0.19%) | In the 3 corrupted rows this column holds a vote count instead | **Transform** |
| `status` | Release status of the movie | object → category | 87 (0.19%) | Released 45,014, Rumored 230, Post Production 98, In Production 20, Planned 15, Canceled 2 | **Transform** |
| `runtime` | Length in minutes | float64 → float | 263 (0.58%) | 1,558 zeros are unknown (1,821 unknown in total, 4.01%). 108 movies exceed 300 minutes and are real miniseries and documentaries. | **Investigate** (zeros are missing; long runtimes are flagged, not errors) |
| `budget` | Production budget, in US dollars **(confirm)** | object → numeric | 0 (0.00%) | 36,573 zeros (80.44%) are unknown. 245 positive values are below 1,000 (placeholders such as 1). 3 non-numeric values (corrupted rows). | **Transform** (zero and tiny values are unknown) |
| `revenue` | Box-office revenue, in US dollars **(confirm)** | float64 → numeric | 6 (0.01%) | 38,052 zeros (83.69%) are unknown. 155 positive values are below 1,000 (placeholders such as 1, 3, 5, 100). | **Transform** (zero and tiny values are unknown) |
| `popularity` | TMDB's popularity score, a number TMDB computes and updates over time | object → float64 | 5 (0.01%) | Non-numeric text from the corrupted rows makes it `object`. It differs between duplicate copies, so it is a snapshot, not a fixed fact. | **Investigate** (use with care) |
| `vote_average` | Average of TMDB user votes, 0 to 10 | float64 → float | 6 (0.01%) | All 2,899 movies with `vote_count` 0 have average 0.0 (a placeholder). 99 more have 0 with votes (81 of them have a single vote). | **Transform** (0 means missing) |
| `vote_count` | Number of TMDB user votes | float64 → Int64 | 6 (0.01%) | 2,899 zeros (6.38%) are real: nobody voted. Differs between 2 duplicate pairs (e.g. 143 vs 144). | **Transform** (zeros are real) |
| `adult` | TMDB adult-content flag | object → bool | 0 (0.00%) | False 45,454, True 9, plus 3 corrupted text values | **Transform** after repair |
| `video` | TMDB flag marking a video-type entry **(confirm exact meaning)** | object → bool | 6 (0.01%) | False 45,367, True 93. It is `object` only because booleans plus NaN. | **Transform** (low value) |
| `genres` | List of the movie's genres | object → list of dicts | 0 (0.00%) | `'[]'` in 2,442 rows (5.37%) | **Transform** (parse) |
| `production_companies` | List of production companies | object → list of dicts | 3 (0.01%) | `'[]'` in 11,875 rows (26.12%) | **Transform** (parse) |
| `production_countries` | List of production countries | object → list of dicts | 3 (0.01%) | `'[]'` in 6,282 rows (13.82%) | **Transform** (parse) |
| `spoken_languages` | List of languages spoken in the film | object → list of dicts | 6 (0.01%) | `'[]'` in 3,829 rows (8.42%). May be genuine (silent films), so never default it to English. | **Transform** (parse) |
| `belongs_to_collection` | The film series the movie belongs to, one dict | object → dict | 40,972 (90.12%) | Missing most likely means "not in a collection" **(confirm)** | **Transform** (parse) |
| `homepage` | Official website link | object → string | 37,684 (82.88%) | Stale: links point to renewed or replaced sites | **Ignore** |
| `poster_path` | Relative path of the poster image on TMDB | object → string | 386 (0.85%) | Only a path, not a usable link. Low analytical value. | **Ignore** |

---

## 5. `credits.csv`

**Rows:** 45,476 raw. **Key:** `id` (TMDB). **Structure:** one row per movie, plus 44 extra copies of repeated ids.

| Column | Meaning | Raw → Target | Missing | Hidden missing and quality notes | Verdict |
|---|---|---|---:|---|---|
| `id` | TMDB movie id. **PK** (has repeats) and **FK** to `movies_metadata.id`. | int64 → int64 | 0 (0.00%) | 45,432 unique. 44 extra copies (36 identical ids, 7 whose `crew` lists hold the same members in a different order). Id 141971 appears three times. | **Trust** after de-duplication |
| `cast` | List of actors and their characters | object → list of dicts | 0 (0.00%) | `'[]'` in 2,418 rows (5.32%), meaning unknown | **Transform** (parse) |
| `crew` | List of crew members and their jobs | object → list of dicts | 0 (0.00%) | `'[]'` in 771 rows (1.70%), meaning unknown | **Transform** (parse) |

---

## 6. `keywords.csv`

**Rows:** 46,419 raw. **Key:** `id` (TMDB). **Structure:** one row per movie, plus 987 extra copies (all identical).

| Column | Meaning | Raw → Target | Missing | Hidden missing and quality notes | Verdict |
|---|---|---|---:|---|---|
| `id` | TMDB movie id. **PK** (has repeats) and **FK** to `movies_metadata.id`. | int64 → int64 | 0 (0.00%) | 45,432 unique. 985 ids repeat, all copies identical. Ids 141971 and 159849 appear three times. | **Trust** after de-duplication |
| `keywords` | List of plot keywords | object → list of dicts | 0 (0.00%) | `'[]'` in 14,795 rows (31.87%): unknown or never tagged | **Transform** (parse) |

---

## 7. `links.csv`

**Rows:** 45,843. **Key:** `movieId` (MovieLens). **Structure:** one row per MovieLens movie. It is the bridge between the two id systems.

| Column | Meaning | Raw → Target | Missing | Hidden missing and quality notes | Verdict |
|---|---|---|---:|---|---|
| `movieId` | MovieLens movie id. **PK**, 45,843 unique. | int64 → int64 | 0 (0.00%) | Range 1 to 176,279 | **Trust** |
| `imdbId` | IMDb id as a plain number (no `tt`, no zero padding) | int64 → string `tt` plus 7 digits | 0 (0.00%) | 45,843 unique. Disagrees with `movies_metadata.imdb_id` for 65 movies (0.14%). | **Transform** |
| `tmdbId` | TMDB id. **FK** to `movies_metadata.id`. | float64 → Int64 | 219 (0.48%) | Float only because of the NaN. 30 repeated values (59 movies share one with another `movieId`). 161 values are not in metadata. | **Transform**, then **Investigate** the shared values |

---

## 8. `links_small.csv`

**Rows:** 9,125. **Key:** `movieId`. **Structure:** small version of `links`. All 9,115 ids shared with `links` agree on both other ids. 10 ids appear only here.

| Column | Meaning | Raw → Target | Missing | Quality notes | Verdict |
|---|---|---|---:|---|---|
| `movieId` | MovieLens movie id | int64 → int64 | 0 (0.00%) | Same id space as `links` | **Trust** |
| `imdbId` | IMDb id as a plain number | int64 → string | 0 (0.00%) | | **Transform** |
| `tmdbId` | TMDB id | float64 → Int64 | 13 (0.14%) | No repeated non-null values | **Transform** |

The small files are not needed for the project (see `7_cleaning_decisions.md`).

---

## 9. `ratings.csv`

**Rows:** 26,024,289. **Key:** (`userId`, `movieId`), with 0 repeats. **Structure:** one row per rating.

| Column | Meaning | Raw → Target | Missing | Quality notes | Verdict |
|---|---|---|---:|---|---|
| `userId` | MovieLens user id | int64 → int32 | 0 (0.00%) | 270,896 unique, range 1 to 270,896 | **Trust** |
| `movieId` | MovieLens movie id (**not** the TMDB id). **FK** to `links.movieId`. | int64 → int32 | 0 (0.00%) | 45,115 unique. All are in `links`. | **Trust** (reach metadata through `links`) |
| `rating` | The user's star rating | float64 → float32 | 0 (0.00%) | 10 distinct values, 0.5 to 5.0 in steps of 0.5 | **Trust** |
| `timestamp` | When the rating was made, as Unix seconds | int64 → datetime | 0 (0.00%) | 1995-01-09 to 2017-08-04 | **Transform** |

**Note:** the Kaggle description says ratings run from 1 to 5, but my data has a minimum of **0.5**, so the description and the data disagree. The data is what we trust.

---

## 10. `ratings_small.csv`

**Rows:** 100,004. **Key:** (`userId`, `movieId`), with 0 repeats. **Structure:** a sample of `ratings`: 99.67% of its distinct (`movieId`, `rating`, `timestamp`) combinations appear in `ratings`, with users renumbered.

| Column | Meaning | Raw → Target | Missing | Quality notes | Verdict |
|---|---|---|---:|---|---|
| `userId` | User id, **numbered separately** from `ratings` | int64 → int32 | 0 (0.00%) | 671 unique, range 1 to 671. Never combine with `ratings.userId`. | **Investigate** (do not mix) |
| `movieId` | MovieLens movie id | int64 → int32 | 0 (0.00%) | 9,066 unique. All are in `links_small`. | **Trust** |
| `rating` | The user's star rating | float64 → float32 | 0 (0.00%) | 0.5 to 5.0 | **Trust** |
| `timestamp` | Unix seconds | int64 → datetime | 0 (0.00%) | Up to October 2016 | **Transform** |

---

## 11. Structure of the text-encoded columns

These columns are stored as text that looks like a Python list or dict. Parse them with **`ast.literal_eval`** (not `json.loads`): the cells use single quotes, and all non-empty cells parsed with 0 failures.

| Column | After parsing | Keys seen in my data |
|---|---|---|
| `genres` | list of dicts | `id`, `name` |
| `production_companies` | list of dicts | `name`, `id` |
| `production_countries` | list of dicts | `iso_3166_1`, `name` |
| `spoken_languages` | list of dicts | `iso_639_1`, `name` |
| `belongs_to_collection` | one dict | typically `id`, `name`, `poster_path`, `backdrop_path` **(confirm)** |
| `keywords` | list of dicts | typically `id`, `name` **(confirm)** |
| `cast` | list of dicts | typically `cast_id`, `character`, `credit_id`, `gender`, `id`, `name`, `order`, `profile_path` **(confirm)** |
| `crew` | list of dicts | `credit_id`, `department`, `gender`, `id`, `job`, `name`, `profile_path` (confirmed) |

**After parsing, check the type too.** A successful parse only proves the syntax is valid. The 3 corrupted rows put plain numbers into `belongs_to_collection` and `production_countries`, and those numbers "parse" even though they are not a dict or a list.

---

## 12. Verdict summary

| Verdict | Columns |
|---|---|
| **Trust** | `title`, `original_title`, `original_language`, `overview` (after repair), `tagline`, `rating`, `userId`, `movieId` (both files), `links.movieId` |
| **Transform** | `movies_metadata.id`, `imdb_id`, `release_date`, `status`, `adult`, `video`, `budget`, `revenue`, `vote_average`, `vote_count`, all list and dict columns, `links.imdbId`, `links.tmdbId`, `timestamp` |
| **Investigate** | `runtime` (flag long runtimes, treat zeros as missing), `popularity` (a snapshot), `ratings_small.userId` (do not mix) |
| **Ignore** | `homepage`, `poster_path` |

---

## 13. Open questions about meaning

These need a source outside the files (the TMDB documentation or a spot check on the site):

1. What exactly does `video` flag? **(confirm)**
2. Are `budget` and `revenue` always in US dollars? **(confirm)**
3. Does a missing `belongs_to_collection` mean "not in a collection"? **(confirm)**
4. What are the exact keys of the `cast`, `keywords` and collection dicts? Check after parsing. (The `crew` keys are confirmed.)