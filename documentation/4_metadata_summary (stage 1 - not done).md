# Movie Dataset: Data Quality Report

**Project:** Movie Intelligence
**Stage:** 1, Understand the Raw Data (investigation done, deliverables in progress)
**Source:** The Movies Dataset (Kaggle, rounakbanik)
**Last updated:** 2026-10-07

> **Where the numbers come from.** Every figure below comes from the pandas investigation notebook (`stage1_data_investigation.ipynb`). Items I have not yet measured are marked **TO VERIFY** and listed in section 10. Nothing marked as a finding is a guess.

---

## 1. How to read this report

| Term | Meaning |
|---|---|
| **Missing (NaN)** | Cells pandas recognises as empty. Counted with `isna()`. |
| **Hidden missing** | Cells that *look* filled but carry no real information, such as `'[]'` (empty list) or `0` in `budget`. Pandas does not count these as missing. |
| **Unique** | Distinct non-missing values (`nunique()`, which ignores NaN). |
| **Key** | The column (or columns) that should identify exactly one row. |
| **Extra copies** | Rows beyond the first for each key (`rows - unique keys`). |
| **Repeated ids** | Number of *distinct* ids that appear more than once. |
| **Copies identical / differ** | Of the repeated ids, how many have every column equal in all copies, versus at least one column different. |

**Why the old "Duplicates" column was removed.** Per-column duplicate counts only say that values repeat, which is normal for columns like `rating`. Worse, `duplicated()` counts missing values as repeats while `nunique()` ignores them, so the two numbers never reconcile. Duplicates are now reported only at **row level** and **key level** (section 4).

---

## 2. Headline findings

1. **There are two different movie-id systems.** TMDB ids (`movies_metadata.id`, `credits.id`, `keywords.id`, `links.tmdbId`) and MovieLens ids (`ratings.movieId`, `links.movieId`). `links` is the only table that holds both, so it is the bridge.
2. **Joining `ratings` directly to `movies_metadata` is wrong.** 37,550 of 45,115 rated movies (83.2%) match nothing, and the 7,565 that do match are coincidences between two unrelated numberings. No error is raised.
3. **`movies_metadata` has 3 corrupted records.** Each is split across two physical rows (6 rows in total), with the second row's values shifted 9 columns to the left. This is why `id`, `adult`, `budget`, and `popularity` have the wrong dtype.
4. **Duplicate ids exist in `credits` (43 ids), `keywords` (985 ids), and `movies_metadata` (29 ids).** Keywords duplicates are all exact copies. Credits has 7 and metadata has 13 ids whose copies **disagree**.
5. **`links` has 30 repeated `tmdbId` values and 219 missing ones.** These can silently merge or multiply rows during a join.
6. **Pandas' missing counts understate the real gaps.** `budget` is unknown for 80.44% of movies and `revenue` for 83.69%. 31.87% of keyword rows are empty lists.
7. **`imdb_id` has a different format in each table** (`tt0114709` vs `114709`). A join on the raw columns matches nothing.
8. **The `_small` files are not subsets of the full files** (none of the 100,004 `ratings_small` rows appear in `ratings`).
9. **`homepage` is stale** and not trustworthy. The dataset is about 9 years old.
10. **Excel row counts were unreliable.** Excel's 1,048,576 for `ratings` is its row limit. The real count is 26,024,289.

---

## 3. Dataset overview

| File | Rows | Columns | Key | Id system | Role |
|---|---:|---:|---|---|---|
| `movies_metadata.csv` | 45,466 | 24 | `id` | TMDB | Main movie table |
| `credits.csv` | 45,476 | 3 | `id` | TMDB | Cast and crew per movie |
| `keywords.csv` | 46,419 | 2 | `id` | TMDB | Keywords per movie |
| `links.csv` | 45,843 | 3 | `movieId` | Both (bridge) | Translates MovieLens id to TMDB and IMDb ids |
| `links_small.csv` | 9,125 | 3 | `movieId` | Both (bridge) | Small version of `links` |
| `ratings.csv` | 26,024,289 | 4 | (`userId`, `movieId`) | MovieLens | User ratings |
| `ratings_small.csv` | 100,004 | 4 | (`userId`, `movieId`) | MovieLens | Small version of `ratings` |

**Row counts versus Excel:** four of the five Excel counts were exactly 1 higher than pandas because Excel counts the header row. Two are unresolved (see section 10): `credits` (Excel 45,505 vs pandas 45,476) and `ratings` (Excel hit its limit).

---

## 4. Duplicates and keys

### 4.1 Fully duplicated rows

| Table | Rows | Fully duplicated rows |
|---|---:|---:|
| credits | 45,476 | 37 |
| keywords | 46,419 | 987 |
| movies_metadata | 45,466 | 17 |
| links | 45,843 | 0 |
| links_small | 9,125 | 0 |
| ratings | 26,024,289 | 0 |
| ratings_small | 100,004 | 0 |

### 4.2 Key tests

| Table | Key tested | Null keys | Rows sharing a key | Extra copies | Repeated ids | Copies identical | Copies differ |
|---|---|---:|---:|---:|---:|---:|---:|
| credits | `id` | 0 | 87 | 44 | 43 | 36 | **7** |
| keywords | `id` | 0 | 1,972 | 987 | 985 | 985 | 0 |
| movies_metadata | `id` | 0 | 59 | 30 | 29 | 16 | **13** |
| links | `movieId` | 0 | 0 | 0 | 0 | n/a | n/a |
| links | `tmdbId` | 219 | 278 | 248 | see 4.3 | n/a | n/a |
| ratings | (`userId`, `movieId`) | 0 | 0 | 0 | 0 | n/a | n/a |
| ratings_small | (`userId`, `movieId`) | 0 | 0 | 0 | 0 | n/a | n/a |

**Identity that explains the gap:** `extra copies - fully duplicated rows = copies differ`.
Credits: 44 − 37 = 7. Metadata: 30 − 17 = 13. Keywords: 987 − 987 = 0.

**What to do:**
- *Identical copies* (credits 36, keywords 985, metadata 16): harmless. Keep one, drop the rest.
- *Conflicting copies* (credits 7, metadata 13): need a decision about which copy wins. Not yet inspected, see section 10.
- Some ids appear three times: 1 in credits (44 extra copies across 43 ids) and 2 in keywords (987 across 985).

### 4.3 The missing-value puzzle (why "Duplicates" never matched)

| Column | Rows | NaN | `nunique()` | `duplicated()` | `duplicated()` ignoring NaN |
|---|---:|---:|---:|---:|---:|
| `movies_metadata.imdb_id` | 45,466 | 17 | 45,417 | 48 | **32** |
| `links.tmdbId` | 45,843 | 219 | 45,594 | 248 | **30** |

`duplicated()` treats the NaNs as repeats of each other (17 NaN gives 16, and 219 NaN gives 218). `nunique()` ignores them. The real repeats are 32 and 30.

---

## 5. Table profiles

Column notation: **Dtype (raw)** is what pandas loaded. **Target** is what it should become. **Verdict** is a proposal (Trust, Transform, Investigate, Ignore) to confirm in the data dictionary.

### 5.1 `credits.csv`: 45,476 rows, 3 columns

| Column | Dtype (raw) | Target | Missing | Missing % | Unique | Hidden missing | Verdict |
|---|---|---|---:|---:|---:|---|---|
| `id` | int64 | int64 | 0 | 0.00 | 45,432 | none | Trust (key, but has repeats) |
| `cast` | object | list[dict] | 0 | 0.00 | 43,019 | `'[]'`: 2,418 (5.32%) | Transform (parse) |
| `crew` | object | list[dict] | 0 | 0.00 | 44,669 | `'[]'`: 771 (1.70%) | Transform (parse) |

`id` range: 2 to 469,172. Empty lists mean *unknown*, because every real film has people who made it.

### 5.2 `keywords.csv`: 46,419 rows, 2 columns

| Column | Dtype (raw) | Target | Missing | Missing % | Unique | Hidden missing | Verdict |
|---|---|---|---:|---:|---:|---|---|
| `id` | int64 | int64 | 0 | 0.00 | 45,432 | none | Trust (key, but has repeats) |
| `keywords` | object | list[dict] | 0 | 0.00 | 25,989 | `'[]'`: 14,795 (31.87%) | Transform (parse) |

`id` range: 2 to 469,172. Same 45,432 unique ids as `credits`. An empty list may mean "never tagged", which is not necessarily "unknown".

### 5.3 `links.csv`: 45,843 rows, 3 columns

| Column | Dtype (raw) | Target | Missing | Missing % | Unique | Range | Verdict |
|---|---|---|---:|---:|---:|---|---|
| `movieId` | int64 | int64 | 0 | 0.00 | 45,843 | 1 to 176,279 | Trust (MovieLens id, unique) |
| `imdbId` | int64 | string `tt0000000` | 0 | 0.00 | 45,843 | 1 to 7,158,814 | Transform (needs `tt` plus 7-digit padding) |
| `tmdbId` | float64 | Int64 | 219 | 0.48 | 45,594 | 2 to 469,172 | Transform and investigate (30 repeats) |

`tmdbId` is float only because it contains NaN.

### 5.4 `links_small.csv`: 9,125 rows, 3 columns

| Column | Dtype (raw) | Target | Missing | Missing % | Unique | Range | Verdict |
|---|---|---|---:|---:|---:|---|---|
| `movieId` | int64 | int64 | 0 | 0.00 | 9,125 | 1 to 164,979 | Investigate (not a subset of `links`) |
| `imdbId` | int64 | string `tt0000000` | 0 | 0.00 | 9,125 | 417 to 5,794,766 | Transform |
| `tmdbId` | float64 | Int64 | 13 | 0.14 | 9,112 | 2 to 416,437 | Transform |

No repeated non-null `tmdbId` (the old "12 duplicates" were the 13 NaNs).

### 5.5 `movies_metadata.csv`: 45,466 rows, 24 columns

| Column | Dtype (raw) | Target | Missing | Missing % | Unique | Notes | Verdict |
|---|---|---|---:|---:|---:|---|---|
| `id` | object | Int64 | 0 | 0.00 | 45,436 | TMDB id. 3 corrupted values are dates. 30 extra copies. 45,433 unique numeric ids. | Transform, then trust |
| `imdb_id` | object | string `tt0000000` | 17 | 0.04 | 45,417 | 32 real repeats. 64 not found in `links`. | Transform, cross-check only |
| `title` | object | string | 6 | 0.01 | 42,277 | Titles repeat naturally (remakes), not a key | Trust |
| `original_title` | object | string | 0 | 0.00 | 43,373 | | Trust |
| `original_language` | object | category | 11 | 0.02 | 92 | | Trust |
| `overview` | object | string | 954 | 2.10 | 44,307 | | Trust |
| `tagline` | object | string | 25,054 | 55.10 | 20,283 | | Trust (sparse) |
| `release_date` | object | datetime | 87 | 0.19 | 17,336 | | Transform |
| `status` | object | category | 87 | 0.19 | 6 | Released 45,014, Rumored 230, Post Production 98, In Production 20, Planned 15, Canceled 2 | Transform |
| `runtime` | float64 | float or Int64 | 263 | 0.58 | 353 | 1,558 zeros. Unknown total: 1,821 (4.01%). Range 0 to 1,256, mean 94.1. | Investigate |
| `budget` | object | numeric | 0 | 0.00 | 1,226 | 36,573 zeros (80.44%) = unknown. 3 non-numeric values (corrupted rows). | Transform and treat 0 as unknown |
| `revenue` | float64 | numeric | 6 | 0.01 | 6,863 | 38,052 zeros (83.69%) = unknown. Range 0 to 2,787,965,087. | Transform and treat 0 as unknown |
| `vote_average` | float64 | float | 6 | 0.01 | 92 | Range 0 to 10. Zeros may be a placeholder for "no votes" (TO VERIFY). | Investigate |
| `vote_count` | float64 | Int64 | 6 | 0.01 | 1,820 | Range 0 to 14,075. 2,899 zeros (6.38%) are real "no votes". | Transform, zeros are real |
| `popularity` | object | float64 | 5 | 0.01 | 43,758 | Non-numeric text from corrupted rows forces `object`. | Transform |
| `adult` | object | bool | 0 | 0.00 | 5 | False 45,454, True 9, 3 corrupted text values | Transform |
| `video` | object | bool | 6 | 0.01 | 2 | False 45,367, True 93. `object` only because bools plus NaN, not corruption. | Transform |
| `genres` | object | list[dict] | 0 | 0.00 | 4,069 | `'[]'`: 2,442 (5.37%) | Transform (parse) |
| `production_companies` | object | list[dict] | 3 | 0.01 | 22,708 | `'[]'`: 11,875 (26.12%) | Transform (parse) |
| `production_countries` | object | list[dict] | 3 | 0.01 | 2,393 | `'[]'`: 6,282 (13.82%) | Transform (parse) |
| `spoken_languages` | object | list[dict] | 6 | 0.01 | 1,931 | `'[]'`: 3,829 (8.42%). Can be genuine (silent films). Do not default to English. | Transform (parse) |
| `belongs_to_collection` | object | dict | 40,972 | 90.12 | 1,698 | NaN most likely means "not in a collection" (TO VERIFY) | Transform (parse) |
| `homepage` | object | string | 37,684 | 82.88 | 7,673 | Stale links, e.g. an old film redirecting to a newer sequel | **Ignore** |
| `poster_path` | object | string | 386 | 0.85 | 45,024 | Relative path only, not a usable image link on its own | Ignore (low value) |

**A note on `popularity`.** The earlier report showed 44,176 unique values. The correct figure is **43,758**. The old script read the file in chunks (`low_memory=True`), so the same number could be seen as both text and float and be counted twice. `low_memory=False` reads the column consistently.

### 5.6 `ratings.csv`: 26,024,289 rows, 4 columns

| Column | Dtype (raw) | Target | Missing | Unique | Range | Verdict |
|---|---|---|---:|---:|---|---|
| `userId` | int64 | int32 | 0 | 270,896 | 1 to 270,896 | Trust |
| `movieId` | int64 | int32 | 0 | 45,115 | 1 to 176,275 | Trust, **MovieLens id** |
| `rating` | float64 | float32 | 0 | 10 | 0.5 to 5.0 (steps of 0.5) | Trust |
| `timestamp` | int64 | datetime (seconds) | 0 | 20,549,435 | 1995-01-09 to 2017-08-04 | Transform |

Key (`userId`, `movieId`): 0 repeats.

### 5.7 `ratings_small.csv`: 100,004 rows, 4 columns

| Column | Dtype (raw) | Target | Missing | Unique | Range | Verdict |
|---|---|---|---:|---:|---|---|
| `userId` | int64 | int32 | 0 | 671 | 1 to 671 | Investigate (separate user numbering) |
| `movieId` | int64 | int32 | 0 | 9,066 | 1 to 163,949 | Investigate |
| `rating` | float64 | float32 | 0 | 10 | 0.5 to 5.0 | Trust |
| `timestamp` | int64 | datetime (seconds) | 0 | 78,141 | 789,652,009 to 1,476,640,644 | Transform |

---

## 6. Hidden missing values

| Field | Hidden value | Count | % of rows | Interpretation |
|---|---|---:|---:|---|
| `credits.cast` | `'[]'` | 2,418 | 5.32 | Unknown (every film has a cast) |
| `credits.crew` | `'[]'` | 771 | 1.70 | Unknown |
| `keywords.keywords` | `'[]'` | 14,795 | 31.87 | Unknown or never tagged |
| `meta.genres` | `'[]'` | 2,442 | 5.37 | Unknown |
| `meta.production_companies` | `'[]'` | 11,875 | 26.12 | Unknown |
| `meta.production_countries` | `'[]'` | 6,282 | 13.82 | Unknown |
| `meta.spoken_languages` | `'[]'` | 3,829 | 8.42 | Unknown **or genuinely none** (silent films) |
| `meta.budget` | `0` | 36,573 | 80.44 | Unknown (a film cannot cost 0) |
| `meta.revenue` | `0` | 38,052 | 83.69 | Unknown |
| `meta.runtime` | `0` | 1,558 | 3.43 | Unknown (4.01% with the 263 NaN) |
| `meta.vote_count` | `0` | 2,899 | 6.38 | **Real observation** (no one voted) |

**Consequence:** averages of `budget` or `revenue`, and ROI (`revenue / budget`), are meaningless until zeros are treated as unknown. Dividing by a zero budget produces infinity. The usable sample for financial analysis is the set of movies with **both** budget and revenue greater than 0 (count **TO VERIFY**).

---

## 7. Malformed records in `movies_metadata`

**Finding:** 3 logical records are split across 6 physical rows. A stub row holds the first columns of the record and is followed by a row containing the **tail** of the same record, shifted **9 columns to the left**.

| Stub row index | Stub id | Corrupted row index | Value sitting in `id` column |
|---:|---:|---:|---|
| 19,729 | 82663 | 19,730 | `1997-08-20` |
| 29,502 | 122662 | 29,503 | `2012-09-29` |
| 35,586 | 249260 | 35,587 | `2014-01-01` |

**Evidence:**
- All 3 rows with a non-numeric `id` are exactly the 3 rows with an invalid `adult` value.
- In the corrupted row, consecutive original columns appear in order, shifted left: overview text, then popularity, poster path, production companies, production countries, release date.
- The corrupted row's `release_date` column holds a small number (`1`, `12`), which matches the last original column, `vote_count` (9 + 14 = 23).
- `title` is missing for all 6 physical rows, matching the "6 missing" seen in many columns.

**What this explains:** `id` is text, `adult` has 5 values instead of 2, `budget` has 3 non-numeric values, and `popularity` is `object`.

**Decision pending:** repair (reassemble each record) or drop. Either way the **stub and its tail must be treated as one unit**. Dropping only the three bad-id rows would leave three ghost movies behind.

**Missingness pattern:** `release_date` and `status` are each missing 87 times, but only 4 rows are missing both (83 only date, 83 only status), so they are not the same rows. Most rows have 2 to 3 missing fields. Rows with 10 or more missing fields (5 of them) are the corrupted ones.

---

## 8. Relationships and joins

### 8.1 Id systems

```
TMDB ids                                         MovieLens ids
movies_metadata.id  --  credits.id               ratings.movieId
                    --  keywords.id                    |
links.tmdbId  <----------- links ------------>  links.movieId
                              |
                          links.imdbId  (IMDb ids, a third system)
```

Correct join chain: `ratings.movieId` → `links.movieId` → `links.tmdbId` → `movies_metadata.id`

### 8.2 Join tests (id overlap)

| Left | Right | In both | Only left | Only right |
|---|---|---:|---:|---:|
| meta.id | credits.id | 45,432 | 1 | 0 |
| meta.id | keywords.id | 45,432 | 1 | 0 |
| credits.id | keywords.id | 45,432 | 0 | 0 |
| meta.id | links.tmdbId | 45,433 | 0 | 161 |
| ratings.movieId | links.movieId | 45,115 | 0 | 728 |
| ratings.movieId | meta.id (**wrong join**) | 7,565 | 37,550 | 37,868 |

**Reading the table:**
- `credits` and `keywords` contain exactly the same ids and cover every metadata movie except 1 (which one: TO VERIFY).
- 161 `links.tmdbId` values point at movies that do not exist in metadata.
- 728 movies in `links` have never been rated.
- The last row is the proof that the two id systems differ. Only 16.8% of rated movies match by coincidence of numbers.

**Three problems inside `links`:**

| Problem | Count | Effect on a join | Visible? |
|---|---:|---|---|
| Missing `tmdbId` | 219 | Rows drop out | Yes, countable |
| `tmdbId` not in metadata | 161 | Rows drop out | Yes, countable |
| Repeated `tmdbId` | 30 | Rows **multiply or merge** | **No, silent** |

### 8.3 IMDb id format

| Table | Column | Example | Type |
|---|---|---|---|
| movies_metadata | `imdb_id` | `tt0114709` | string |
| links | `imdbId` | `114709` | int |

After rebuilding the `tt` plus 7-digit form: 45,353 match, 64 only in metadata, 490 only in links.

**Which key to use between metadata and links:**

| Key | Metadata side | Links side | Metadata movies with no match |
|---|---|---|---:|
| TMDB (`id` vs `tmdbId`) | 0 missing, 30 extra copies | 219 missing, 30 repeats | 0 |
| IMDb (`imdb_id` vs `imdbId`) | 17 missing, 32 repeats | 0 missing, 0 repeats | 64 |

TMDB is the backbone key because `credits` and `keywords` only carry it. IMDb is a cross-check. Whether the two paths agree on the same movie is **TO VERIFY**.

### 8.4 The `_small` files

| Check | Result |
|---|---|
| `links_small.movieId` ⊆ `links.movieId` | **False** |
| `ratings_small.movieId` ⊆ `links_small.movieId` | True |
| `ratings_small` rows found in `ratings` | **0 of 100,004** |

The small files are **not samples** of the full files. Untested: whether the same `movieId` points to different movies in the two files.

---

## 9. Plausibility checks

| Check | Result | Verdict |
|---|---|---|
| Rating timestamps | 1995-01-09 to 2017-08-04 | Plausible. Convert from Unix seconds. |
| Runtime | Mean 94.1, median 95, max 1,256, 1,558 zeros | Zeros = unknown. High values need inspection. **Do not cap.** Flag or exclude instead. |

---

## 10. Open items

| # | Item | Needed for |
|---:|---|---|
| 1 | Reachable rated movies through the bridge (count and % lost) | Section 8 |
| 2 | Which `meta` id is missing from `credits` and `keywords` | Section 8.2 |
| 3 | Do the TMDB path and IMDb path agree on the same movie in `links`? | Section 8.3 |
| 4 | Do shared `movieId` values in `links` and `links_small` point to the same `tmdbId`? | Section 8.4 |
| 5 | Movies with `runtime` over 300: do the titles look plausible? | Section 9 |
| 6 | Inspect the 7 (credits) and 13 (metadata) conflicting duplicate ids | Section 4.2 |
| 7 | Count of movies with both budget and revenue above 0 | Section 6 |
| 8 | What `vote_average` holds when `vote_count` is 0 | Section 5.5 |
| 9 | Why Excel showed 45,505 rows for `credits` (the file has 45,477 physical lines, so line breaks do not explain it) | Section 3 |
| 10 | Does `belongs_to_collection` NaN mean "not in a collection"? | Section 5.5 |